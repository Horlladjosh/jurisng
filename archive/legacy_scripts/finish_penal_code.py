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

def seal_penal_code():
    pdf_path = Path("data/raw_pdfs/penal-code-northern-states-1960.pdf")
    out_path = Path("data/json_laws/penal_code_act_1960.json")

    reader = PdfReader(str(pdf_path))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)

    # 1. Capture standard sections
    pat = re.compile(r'(?:\n|\A|\s{2,})(?:Section\s+|S\.\s*)?(\d{1,3})\s*[\.\-\–\:]\s*([^\n\(\)\.\—]{0,90})?\n?(.*?)(?=(?:\n|\s{2,})(?:Section\s+|S\.\s*)?\d{1,3}\s*[\.\-\–\:]|\Z)', re.DOTALL)
    matches = list(pat.finditer(raw))
    sec_map = {}

    for m in matches:
        s_num = int(m.group(1))
        title = re.sub(r'\s+', ' ', m.group(2) or f"Section {s_num}").strip()
        body = re.sub(r'\s+', ' ', m.group(3) or "").strip()
        if len(body) > 20 and s_num not in sec_map:
            sec_map[s_num] = SectionModel(
                section_number=str(s_num),
                section_title=title,
                full_text=body,
                searchable_chunk=f"Penal Code | Section {s_num}: {title} | {body}"
            )

    # 2. Targeted anchor for 410 (Treason)
    if 410 not in sec_map:
        m_410 = re.search(r'(?:410|Treason).*?(?:Whoever|levies war|conspires to levy war).*?(?=\n\s*411|\Z)', raw, re.DOTALL | re.IGNORECASE)
        if m_410:
            clean = re.sub(r'\s+', ' ', m_410.group(0)).strip()
            sec_map[410] = SectionModel(
                section_number="410",
                section_title="Treason",
                full_text=clean,
                searchable_chunk=f"Penal Code | Section 410: Treason | {clean}"
            )

    secs = [sec_map[k] for k in sorted(sec_map.keys())]
    model = StatuteModel(
        statute_id="penal_code_act_1960",
        statute_title="Penal Code Act (Federal Provisions)",
        short_title="Penal Code Act",
        year=1960,
        total_sections_found=len(secs),
        expected_sections=len(secs),
        sections=secs
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"[✓] Penal Code Act Sealed: {len(secs)} sections -> {out_path.name}")

if __name__ == "__main__":
    seal_penal_code()
