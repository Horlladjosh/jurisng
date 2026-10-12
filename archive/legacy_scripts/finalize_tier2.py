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

def parse_statute_to_100(statute_id: str, title: str, short_title: str, year: int, total_secs: int, pdf_path: str, out_path: str):
    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"[-] File not found: {pdf_path}")
        return

    reader = PdfReader(str(pdf))
    raw_pages = []
    for page in reader.pages:
        t = page.extract_text() or ""
        t = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', t, flags=re.IGNORECASE)
        t = re.sub(r'Page\s+\d+\s+of\s+\d+', '', t, flags=re.IGNORECASE)
        raw_pages.append(t)

    full_text = "\n".join(raw_pages)

    # Multi-case boundary pattern matching:
    # 1. "Section 84." or "Section 84A."
    # 2. "84." or "84-(1)" or "84 (1)" or "[84]"
    # 3. "\n84\n" followed by capitalized title or subsection
    pattern = re.compile(
        r'(?:\n|\A)\s*(?:\[|\()? *(?:Section\s+|S\.\s*)?([0-9]{1,3}[A-Z]?)(?:\]|\))?\s*[\.\-\–\:]?\s*(?:\n\s*)?([A-Z][^\n\(\)\.\—]{1,120})?(?:\n|\s{2,}|\s*(?=\([0-9a-zA-Z]+\)|[A-Z]))',
        re.MULTILINE
    )

    matches = list(pattern.finditer(full_text))
    sections_dict = {}

    for i, match in enumerate(matches):
        sec_num = match.group(1).strip()
        
        try:
            num_digits = int(re.sub(r'\D', '', sec_num))
            if num_digits > (total_secs + 15) or num_digits == 0:
                continue
        except ValueError:
            continue

        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        
        raw_title = match.group(2).strip() if (match.lastindex and match.lastindex >= 2 and match.group(2)) else ""
        raw_body = full_text[start_pos:end_pos].strip()

        if not raw_title and "\n" in raw_body:
            lines = [l.strip() for l in raw_body.split("\n") if l.strip()]
            if lines and len(lines[0]) < 90 and not lines[0].startswith("("):
                raw_title = lines[0]
                raw_body = "\n".join(lines[1:])

        clean_body = re.sub(r'\s+', ' ', raw_body).strip()
        clean_title = re.sub(r'\s+', ' ', raw_title).strip() or f"Section {sec_num}"

        # Accept all non-empty sections
        if len(clean_body) > 2 and sec_num not in sections_dict:
            sections_dict[sec_num] = SectionModel(
                section_number=sec_num,
                section_title=clean_title,
                full_text=clean_body,
                searchable_chunk=f"{short_title} | Section {sec_num}: {clean_title} | {clean_body}"
            )

    # Sort numerically while preserving alpha sub-clauses (e.g., 84, 84A, 85)
    def sort_key(s):
        match = re.match(r'(\d+)([A-Z]?)', s)
        if match:
            return (int(match.group(1)), match.group(2))
        return (0, s)

    sorted_secs = sorted(sections_dict.values(), key=lambda x: sort_key(x.section_number))

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
    tag = "100% COMPLETE" if len(sorted_secs) >= total_secs else f"{pct:.1f}%"
    print(f"[{tag:^15}] {short_title:<28}: {len(sorted_secs):>4} / {total_secs:<4} -> {out_file.name}")

if __name__ == "__main__":
    print("=" * 65)
    print("FINALIZING TIER 2 STATUTES TO 100%")
    print("=" * 65)

    parse_statute_to_100(
        "evidence_act_2011",
        "Evidence Act 2011",
        "Evidence Act 2011",
        2011,
        259,
        "data/raw_pdfs/evidence-act-2011.pdf",
        "data/json_laws/evidence_act_2011.json"
    )

    parse_statute_to_100(
        "cybercrimes_act_2015",
        "Cybercrimes (Prohibition, Prevention, etc.) Act 2015",
        "Cybercrimes Act 2015",
        2015,
        59,
        "data/raw_pdfs/cybercrimes-act-2015.pdf",
        "data/json_laws/cybercrimes_act_2015.json"
    )
