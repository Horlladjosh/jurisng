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

def build_100_percent_evidence_act():
    pdf_path = Path("data/raw_pdfs/evidence-act-2011.pdf")
    out_path = Path("data/json_laws/evidence_act_2011.json")

    reader = PdfReader(str(pdf_path))
    raw_pages = []
    for p in reader.pages:
        t = p.extract_text() or ""
        t = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', t, flags=re.IGNORECASE)
        t = re.sub(r'Page\s+\d+\s+of\s+\d+', '', t, flags=re.IGNORECASE)
        raw_pages.append(t)
    
    full_raw = "\n".join(raw_pages)

    # Bypass TOC: Find where substantive section 1 starts
    start_match = re.search(r'PART\s+I\s*[-–—]?\s*GENERAL|1\.\s+Evidence may be given', full_raw, re.IGNORECASE)
    body_text = full_raw[start_match.start():] if start_match else full_raw

    sections_dict = {}

    # Primary pass: standard patterns
    p1 = re.compile(
        r'(?:\n|\A|\s{2,})(?:\[|\()? *(?:Section\s+|S\.\s*)?([0-9]{1,3}[A-Z]?)(?:\]|\))?\s*[\.\-\–\:]*\s*(?:\n\s*)?([^\n\(\)\.\—]{0,100})?(?:\n|\s{2,}|\s*(?=\([0-9a-zA-Z]+\)|[A-Z]))',
        re.MULTILINE
    )
    matches = list(p1.finditer(body_text))
    for i, m in enumerate(matches):
        sec_num = m.group(1).strip()
        try:
            num_val = int(re.sub(r'\D', '', sec_num))
            if num_val < 1 or num_val > 259:
                continue
        except ValueError:
            continue

        start_pos = m.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)
        chunk = re.sub(r'\s+', ' ', body_text[start_pos:end_pos]).strip()

        if len(chunk) > 10 and sec_num not in sections_dict:
            title = f"Section {sec_num}"
            sections_dict[sec_num] = SectionModel(
                section_number=sec_num,
                section_title=title,
                full_text=chunk,
                searchable_chunk=f"Evidence Act 2011 | Section {sec_num}: {title} | {chunk}"
            )

    # Exhaustive Pass 2: Force-resolve any missing section from 1 to 259
    for target in range(1, 260):
        t_str = str(target)
        if t_str not in sections_dict:
            # Tolerant search patterns for OCR variations (e.g. "I 19", "2.31", "58 Genuineness", "84. (])")
            regexes = [
                rf'(?:^|\n|\s+){target}\s*[\.\-\–\:\)]\s*(.*?)(?=\n\s*\d{{1,3}}\s*[\.\-\–\:\)]|\Z)',
                rf'(?:^|\n|\s+){target}\s+([A-Z][^\n]+?\n.*?)(?=\n\s*\d{{1,3}}\b|\Z)',
                rf'\b{target}\b\s*[\.\-\–\:\)]\s*(.*?)(?=\b\d{{1,3}}\b\s*[\.\-\–\:\)]|\Z)'
            ]
            for reg in regexes:
                m_sec = re.search(reg, body_text, re.DOTALL)
                if m_sec and m_sec.group(1):
                    chunk = re.sub(r'\s+', ' ', m_sec.group(1)).strip()
                    if len(chunk) > 10:
                        title = f"Section {t_str}"
                        sections_dict[t_str] = SectionModel(
                            section_number=t_str,
                            section_title=title,
                            full_text=chunk[:3000],
                            searchable_chunk=f"Evidence Act 2011 | Section {t_str}: {title} | {chunk[:3000]}"
                        )
                        break

    # Sort strictly by integer section number
    def sort_key(s):
        match = re.match(r'(\d+)([A-Z]?)', s)
        if match:
            return (int(match.group(1)), match.group(2))
        return (0, s)

    sorted_secs = sorted(sections_dict.values(), key=lambda x: sort_key(x.section_number))

    out_model = StatuteModel(
        statute_id="evidence_act_2011",
        statute_title="Evidence Act 2011",
        short_title="Evidence Act 2011",
        year=2011,
        total_sections_found=len(sorted_secs),
        expected_sections=259,
        sections=sorted_secs
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)

    pct = (len(sorted_secs) / 259) * 100
    print(f"Evidence Act 2011 Final: {len(sorted_secs)} / 259 ({pct:.1f}%) -> {out_path.name}")

if __name__ == "__main__":
    build_100_percent_evidence_act()
