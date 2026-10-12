import re
import json
from pathlib import Path
from pypdf import PdfReader
from pydantic import BaseModel
from typing import List

class SectionModel(BaseModel):
    section_number: str
    section_title: str
    full_text: str
    searchable_chunk: str

class StatuteModel(BaseModel):
    statute_id: str
    statute_title: str
    short_title: str
    year: int
    total_sections_found: int
    expected_sections: int
    sections: List[SectionModel]

def patch_statute(statute_id: str, title: str, short_title: str, year: int, total_secs: int, pdf_path: str, out_path: str):
    pdf = Path(pdf_path)
    if not pdf.exists():
        return

    reader = PdfReader(str(pdf))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)
    
    # Matches standard numbers, bracketed numbers [84], or "Section 12."
    pattern = re.compile(
        r'(?:\n|\A)\s*(?:\[|\()? *(?:Section\s+)?([0-9]{1,3}[A-Z]?)(?:\]|\))?\s*[\.\-\–\:]?\s*([^\n\(\)\.\—]{2,120})?(?:\n|\s{2,}|\s*(?=\([0-9a-zA-Z]+\)|[A-Z]))',
        re.MULTILINE
    )

    matches = list(pattern.finditer(raw))
    sections_dict = {}

    for i, match in enumerate(matches):
        sec_num = match.group(1).strip()
        try:
            num_val = int(re.sub(r'\D', '', sec_num))
            if num_val > (total_secs + 10) or num_val == 0:
                continue
        except ValueError:
            continue

        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        
        raw_title = match.group(2).strip() if (match.lastindex and match.lastindex >= 2 and match.group(2)) else ""
        raw_body = raw[start_pos:end_pos].strip()

        clean_body = re.sub(r'\s+', ' ', raw_body).strip()
        clean_title = re.sub(r'\s+', ' ', raw_title).strip() or f"Section {sec_num}"

        if len(clean_body) > 5 and sec_num not in sections_dict:
            sections_dict[sec_num] = SectionModel(
                section_number=sec_num,
                section_title=clean_title,
                full_text=clean_body,
                searchable_chunk=f"{short_title} | Section {sec_num}: {clean_title} | {clean_body}"
            )

    def sec_key(s_num):
        nums = re.findall(r'\d+', s_num)
        return int(nums[0]) if nums else 0

    sorted_secs = sorted(sections_dict.values(), key=lambda x: sec_key(x.section_number))
    
    out_model = StatuteModel(
        statute_id=statute_id,
        statute_title=title,
        short_title=short_title,
        year=year,
        total_sections_found=len(sorted_secs),
        expected_sections=total_secs,
        sections=sorted_secs
    )

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)

    pct = (len(sorted_secs) / total_secs) * 100
    print(f"[✓] {short_title:<28}: {len(sorted_secs):>4} / {total_secs:<4} ({pct:5.1f}%) -> {out_file.name}")

if __name__ == "__main__":
    patch_statute("evidence_act_2011", "Evidence Act 2011", "Evidence Act 2011", 2011, 259, "data/raw_pdfs/evidence-act-2011.pdf", "data/json_laws/evidence_act_2011.json")
    patch_statute("cybercrimes_act_2015", "Cybercrimes (Prohibition, Prevention, etc.) Act 2015", "Cybercrimes Act 2015", 2015, 59, "data/raw_pdfs/cybercrimes-act-2015.pdf", "data/json_laws/cybercrimes_act_2015.json")
    patch_statute("acja_2015", "Administration of Criminal Justice Act 2015", "ACJA 2015", 2015, 495, "data/raw_pdfs/acja-2015.pdf", "data/json_laws/acja_2015.json")
