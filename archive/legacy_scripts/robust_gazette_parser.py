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

def parse_with_state_machine(statute_id: str, title: str, short_title: str, year: int, total_secs: int, pdf_path: str, output_path: str):
    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"[-] Missing file: {pdf_path}")
        return

    reader = PdfReader(str(pdf))
    raw_pages = []
    for page in reader.pages:
        t = page.extract_text() or ""
        # Clean running headers
        t = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', t, flags=re.IGNORECASE)
        t = re.sub(r'Page\s+\d+\s+of\s+\d+', '', t, flags=re.IGNORECASE)
        raw_pages.append(t)

    full_text = "\n".join(raw_pages)

    # Locate section markers sequentially: accepts "1.", "1.-", "1 ", "Section 1", "[1]"
    # Captures positions of every candidate number up to total_secs + 5
    marker_pattern = re.compile(
        r'(?:^|\n|\s{2,})(?:Section\s+)?(\d{1,3})\s*[\.\-\–\:]?\s*(?:\((?:1|[a-zA-Z])\)|[A-Z])',
        re.MULTILINE
    )

    candidates = list(marker_pattern.finditer(full_text))
    
    sections_dict = {}
    last_found_num = 0

    for i, match in enumerate(candidates):
        num_str = match.group(1)
        try:
            num = int(num_str)
        except ValueError:
            continue

        if num < 1 or num > total_secs:
            continue

        # Lookahead boundary: either next candidate or end of file
        start_idx = match.start()
        end_idx = candidates[i + 1].start() if i + 1 < len(candidates) else len(full_text)
        
        chunk = full_text[start_idx:end_idx].strip()
        
        # Clean section title from the first line
        lines = [l.strip() for l in chunk.split("\n") if l.strip()]
        sec_title = f"Section {num}"
        if lines:
            header_candidate = re.sub(r'^(?:Section\s+)?\d+\s*[\.\-\–\:]?\s*', '', lines[0]).strip()
            if len(header_candidate) > 2 and not header_candidate.startswith("("):
                sec_title = header_candidate[:100]

        clean_body = re.sub(r'\s+', ' ', chunk).strip()

        if len(clean_body) > 20 and str(num) not in sections_dict:
            sections_dict[str(num)] = SectionModel(
                section_number=str(num),
                section_title=sec_title,
                full_text=clean_body,
                searchable_chunk=f"{short_title} | Section {num}: {sec_title} | {clean_body}"
            )

    sorted_secs = sorted(sections_dict.values(), key=lambda x: int(x.section_number))
    
    out_model = StatuteModel(
        statute_id=statute_id,
        statute_title=title,
        short_title=short_title,
        year=year,
        total_sections_found=len(sorted_secs),
        expected_sections=total_secs,
        sections=sorted_secs
    )

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)

    pct = (len(sorted_secs) / total_secs) * 100
    print(f"[{'COMPLETE' if pct >= 90 else 'PARTIAL'}] {short_title:<28}: {len(sorted_secs):>3} / {total_secs:<3} ({pct:5.1f}%) -> {out_file.name}")

if __name__ == "__main__":
    print("=" * 65)
    print("RUNNING STATE-MACHINE PARSER ON TARGETED STATUTES")
    print("=" * 65)
    
    parse_with_state_machine(
        "national_health_act_2014",
        "National Health Act 2014",
        "National Health Act 2014",
        2014,
        65,
        "data/raw_pdfs/national-health-act-2014.pdf",
        "data/json_laws/national_health_act_2014.json"
    )

    parse_with_state_machine(
        "fccpa_2018",
        "Federal Competition and Consumer Protection Act 2018",
        "FCCPA 2018",
        2018,
        168,
        "data/raw_pdfs/fccpa-2018.pdf",
        "data/json_laws/fccpa_2018.json"
    )

    parse_with_state_machine(
        "cybercrimes_act_2015",
        "Cybercrimes (Prohibition, Prevention, etc.) Act 2015",
        "Cybercrimes Act 2015",
        2015,
        59,
        "data/raw_pdfs/cybercrimes-act-2015.pdf",
        "data/json_laws/cybercrimes_act_2015.json"
    )
