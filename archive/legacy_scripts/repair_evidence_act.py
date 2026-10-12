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

def parse_evidence_act_sliced():
    pdf_path = Path("data/raw_pdfs/evidence-act-2011.pdf")
    out_path = Path("data/json_laws/evidence_act_2011.json")

    reader = PdfReader(str(pdf_path))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)

    # 1. Bypass Table of Contents (TOC usually ends where Part I / Section 1 starts in earnest)
    # Locate the second occurrence of "1." or where substantive text begins
    start_body_match = re.search(r'PART\s+I\s*[-–—]?\s*GENERAL|1\.\s+Evidence may be given|1\.\s+[A-Z]', raw, re.IGNORECASE)
    body_text = raw[start_body_match.start():] if start_body_match else raw

    # 2. Find every section start: \n followed by number and dot/dash/bracket (e.g. "\n19.", "\n84.", "\n84A.")
    pattern = re.compile(r'(?:\n\s*|\A\s*)([0-9]{1,3}[A-Z]?)\s*[\.\-\–]\s*', re.MULTILINE)
    matches = list(pattern.finditer(body_text))

    sections_dict = {}

    for i, match in enumerate(matches):
        sec_num = match.group(1).strip()
        try:
            num_val = int(re.sub(r'\D', '', sec_num))
            if num_val < 1 or num_val > 259:
                continue
        except ValueError:
            continue

        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)

        raw_chunk = body_text[start_pos:end_pos].strip()
        clean_body = re.sub(r'\s+', ' ', raw_chunk).strip()

        # Clean section title if present on first line, else standard label
        clean_title = f"Section {sec_num}"

        if len(clean_body) > 10 and sec_num not in sections_dict:
            sections_dict[sec_num] = SectionModel(
                section_number=sec_num,
                section_title=clean_title,
                full_text=clean_body,
                searchable_chunk=f"Evidence Act 2011 | Section {sec_num}: {clean_title} | {clean_body}"
            )

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
    print(f"Evidence Act 2011 Yield: {len(sorted_secs)} / 259 ({pct:.1f}%) -> {out_path.name}")

if __name__ == "__main__":
    parse_evidence_act_sliced()
