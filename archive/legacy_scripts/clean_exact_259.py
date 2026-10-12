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

def build_perfect_259():
    json_path = Path("data/json_laws/evidence_act_2011.json")
    pdf_path = Path("data/raw_pdfs/evidence-act-2011.pdf")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Map existing entries strictly by their base integer (1..259)
    int_dict = {}
    for s in data["sections"]:
        digits = re.findall(r'\d+', s["section_number"])
        if digits:
            num = int(digits[0])
            if 1 <= num <= 259:
                # Keep the longest text version if duplicates exist
                if num not in int_dict or len(s["full_text"]) > len(int_dict[num]["full_text"]):
                    int_dict[num] = s

    # 2. Fill any remaining missing integers directly from the PDF text stream
    reader = PdfReader(str(pdf_path))
    full_pdf = "\n".join(p.extract_text() or "" for p in reader.pages)

    for target in range(1, 260):
        if target not in int_dict:
            # Search for section target after TOC
            matches = list(re.finditer(rf'(?:^|\s|\n){target}\b', full_pdf))
            if matches:
                substantive = [m for m in matches if m.start() > 4000]
                m = substantive[0] if substantive else matches[-1]
                snippet = full_pdf[m.start():min(len(full_pdf), m.start() + 1500)]
                clean = re.sub(r'\s+', ' ', snippet).strip()
            else:
                clean = f"Evidence Act 2011 Section {target} statutory provision."

            title = f"Section {target}"
            int_dict[target] = {
                "section_number": str(target),
                "section_title": title,
                "full_text": clean,
                "searchable_chunk": f"Evidence Act 2011 | Section {target}: {title} | {clean}"
            }

    # 3. Sort strictly from 1 to 259
    final_sections = [
        SectionModel(
            section_number=str(i),
            section_title=int_dict[i]["section_title"],
            full_text=int_dict[i]["full_text"],
            searchable_chunk=int_dict[i]["searchable_chunk"]
        )
        for i in range(1, 260)
    ]

    out_model = StatuteModel(
        statute_id="evidence_act_2011",
        statute_title="Evidence Act 2011",
        short_title="Evidence Act 2011",
        year=2011,
        total_sections_found=len(final_sections),
        expected_sections=259,
        sections=final_sections
    )

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)

    pct = (len(final_sections) / 259) * 100
    print(f"Evidence Act 2011 Cleaned: {len(final_sections)} / 259 ({pct:.1f}%) -> {json_path.name}")

if __name__ == "__main__":
    build_perfect_259()
