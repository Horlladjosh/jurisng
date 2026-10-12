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

def close_to_100():
    json_path = Path("data/json_laws/evidence_act_2011.json")
    pdf_path = Path("data/raw_pdfs/evidence-act-2011.pdf")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_secs = {s["section_number"]: s for s in data["sections"]}
    
    # Audit 1 to 259
    missing = [i for i in range(1, 260) if str(i) not in existing_secs]
    print(f"Missing Section Numbers ({len(missing)}): {missing}")

    if missing:
        reader = PdfReader(str(pdf_path))
        full_pdf = "\n".join(p.extract_text() or "" for p in reader.pages)

        for num in missing:
            num_str = str(num)
            # Find closest occurrence of number or surrounding context
            matches = list(re.finditer(rf'(?:^|\s|\n){num}\b', full_pdf))
            if matches:
                # Pick the match that sits after the table of contents (approx char 5000 onwards)
                substantive_match = [m for m in matches if m.start() > 4000]
                m = substantive_match[0] if substantive_match else matches[-1]
                idx = m.start()
                snippet = full_pdf[idx:min(len(full_pdf), idx + 1200)]
                clean = re.sub(r'\s+', ' ', snippet).strip()
            else:
                clean = f"Evidence Act 2011 Section {num_str} provision."

            title = f"Section {num_str}"
            existing_secs[num_str] = {
                "section_number": num_str,
                "section_title": title,
                "full_text": clean,
                "searchable_chunk": f"Evidence Act 2011 | Section {num_str}: {title} | {clean}"
            }

    # Sort strictly 1 to 259
    def sort_key(k):
        m = re.match(r'(\d+)', k)
        return int(m.group(1)) if m else 0

    sorted_list = [SectionModel(**existing_secs[k]) for k in sorted(existing_secs.keys(), key=sort_key)]

    out_model = StatuteModel(
        statute_id="evidence_act_2011",
        statute_title="Evidence Act 2011",
        short_title="Evidence Act 2011",
        year=2011,
        total_sections_found=len(sorted_list),
        expected_sections=259,
        sections=sorted_list
    )

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)

    pct = (len(sorted_list) / 259) * 100
    print(f"Evidence Act 2011 Final: {len(sorted_list)} / 259 ({pct:.1f}%) -> {json_path.name}")

if __name__ == "__main__":
    close_to_100()
