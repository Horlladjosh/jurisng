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

def parse_full_body_cybercrimes():
    pdf_path = Path("data/raw_pdfs/cybercrimes-act-2015.pdf")
    out_path = Path("data/json_laws/cybercrimes_act_2015.json")

    reader = PdfReader(str(pdf_path))
    raw_pages = []
    for p in reader.pages:
        t = p.extract_text() or ""
        t = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', t, flags=re.IGNORECASE)
        t = re.sub(r'Page\s+\d+\s+of\s+\d+', '', t, flags=re.IGNORECASE)
        raw_pages.append(t)

    full_raw = "\n".join(raw_pages)

    # 1. Locate the true start of substantive enacted text
    # In Nigerian legislation, substantive law starts at "ENACTED" or after the main title recurrence
    enacted_match = re.search(r'ENACTED\s+by\s+the\s+National\s+Assembly|ENACTED\s+BY\s+THE\s+NATIONAL\s+ASSEMBLY', full_raw)
    if enacted_match:
        substantive_text = full_raw[enacted_match.start():]
    else:
        # Fallback: Find the 2nd occurrence of "PART I" or "1. The objectives"
        parts = [m.start() for m in re.finditer(r'PART\s+I\b', full_raw, re.IGNORECASE)]
        substantive_text = full_raw[parts[1]:] if len(parts) > 1 else full_raw

    # 2. Extract sections from 1 to 59 in substantive text
    sections_dict = {}

    for i in range(1, 60):
        curr_num = str(i)
        next_num = str(i + 1) if i < 59 else r'(?:SCHEDULE|Citation|\Z)'

        # Matches: "1. (1)", "1.-(1)", "1. The", "Section 1.", etc.
        pattern = rf'(?:^|\n|\s{{2,}})(?:Section\s+)?{curr_num}\s*[\.\-\–\:]\s*(.*?)(?=(?:\n|\s{{2,}})(?:Section\s+)?{next_num}\s*[\.\-\–\:]|\Z)'
        match = re.search(pattern, substantive_text, re.DOTALL)

        if match:
            raw_body = match.group(1).strip()
            clean_body = re.sub(r'\s+', ' ', raw_body).strip()
            
            # Extract title if on first line or formulate clean title
            lines = [l.strip() for l in raw_body.split('\n') if l.strip()]
            title = lines[0] if lines and len(lines[0]) < 80 and not lines[0].startswith('(') else f"Section {curr_num}"
            title = re.sub(r'\s+', ' ', title).strip()

            sections_dict[i] = SectionModel(
                section_number=curr_num,
                section_title=title,
                full_text=clean_body,
                searchable_chunk=f"Cybercrimes Act 2015 | Section {curr_num}: {title} | {clean_body}"
            )
        else:
            # Tolerant search without trailing dot
            pattern_loose = rf'(?:^|\n|\s{{2,}}){curr_num}\s+([A-Z\(\(].*?)(?=(?:\n|\s{{2,}}){next_num}\s+[\(A-Z]|\Z)'
            match_loose = re.search(pattern_loose, substantive_text, re.DOTALL)
            if match_loose:
                raw_body = match_loose.group(1).strip()
                clean_body = re.sub(r'\s+', ' ', raw_body).strip()
                title = f"Section {curr_num}"
                sections_dict[i] = SectionModel(
                    section_number=curr_num,
                    section_title=title,
                    full_text=clean_body,
                    searchable_chunk=f"Cybercrimes Act 2015 | Section {curr_num}: {title} | {clean_body}"
                )

    sorted_secs = [sections_dict[k] for k in sorted(sections_dict.keys())]

    out_model = StatuteModel(
        statute_id="cybercrimes_act_2015",
        statute_title="Cybercrimes (Prohibition, Prevention, etc.) Act 2015",
        short_title="Cybercrimes Act 2015",
        year=2015,
        total_sections_found=len(sorted_secs),
        expected_sections=59,
        sections=sorted_secs
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)

    pct = (len(sorted_secs) / 59) * 100
    print(f"Cybercrimes Act 2015 Body Extracted: {len(sorted_secs)} / 59 ({pct:.1f}%) -> {out_path.name}")

if __name__ == "__main__":
    parse_full_body_cybercrimes()
