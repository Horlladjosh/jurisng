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

RAW = Path("data/raw_pdfs")
OUT = Path("data/json_laws")

def clean_txt(t):
    return re.sub(r'\s+', ' ', t or '').strip()

# 1. EVIDENCE ACT 2011 (Exact 259 Substantive Slices)
def fix_evidence_act():
    reader = PdfReader(str(RAW / "evidence-act-2011.pdf"))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)
    raw = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'Page\s+\d+\s+of\s+\d+', '', raw, flags=re.IGNORECASE)
    
    start_m = re.search(r'PART\s+I\s*[-–—]?\s*GENERAL|1\.\s+Evidence may be given', raw, re.IGNORECASE)
    body = raw[start_m.start():] if start_m else raw

    sec_map = {}
    for i in range(1, 260):
        c_str = str(i)
        n_str = str(i + 1) if i < 259 else r'(?:SCHEDULE|\Z)'
        pat = rf'(?:^|\n|\s{{2,}}){c_str}\s*[\.\-\–\:]\s*(.*?)(?=(?:\n|\s{{2,}}){n_str}\s*[\.\-\–\:]|\Z)'
        m = re.search(pat, body, re.DOTALL)
        if m and len(clean_txt(m.group(1))) > 15:
            txt = clean_txt(m.group(1))
            sec_map[i] = SectionModel(
                section_number=c_str,
                section_title=f"Section {c_str}",
                full_text=txt,
                searchable_chunk=f"Evidence Act 2011 | Section {c_str} | {txt}"
            )
        else:
            # Anchor search
            m_iso = list(re.finditer(rf'(?:^|\n|\s){c_str}\b\s*[\.\-\–\:]?', body))
            if m_iso:
                s_idx = m_iso[0].end()
                txt = clean_txt(body[s_idx:min(len(body), s_idx + 2500)])
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=txt,
                    searchable_chunk=f"Evidence Act 2011 | Section {c_str} | {txt}"
                )

    secs = [sec_map[k] for k in sorted(sec_map.keys())]
    model = StatuteModel(
        statute_id="evidence_act_2011",
        statute_title="Evidence Act 2011",
        short_title="Evidence Act 2011",
        year=2011,
        total_sections_found=len(secs),
        expected_sections=259,
        sections=secs
    )
    with open(OUT / "evidence_act_2011.json", "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"[✓] Evidence Act 2011: {len(secs)} / 259")

# 2. POLICE ACT 2020 (Clean 1 to 142)
def fix_police_act():
    reader = PdfReader(str(RAW / "police_act_2020.pdf"))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)
    raw = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', raw, flags=re.IGNORECASE)
    
    start_m = re.search(r'ENACTED\s+by\s+the\s+National\s+Assembly|1\.\s+The objective of this Act', raw)
    body = raw[start_m.start():] if start_m else raw

    sec_map = {}
    for i in range(1, 143):
        c_str = str(i)
        n_str = str(i + 1) if i < 142 else r'(?:SCHEDULE|\Z)'
        pat = rf'(?:^|\n|\s{{2,}}){c_str}\s*[\.\-\–\:]\s*(.*?)(?=(?:\n|\s{{2,}}){n_str}\s*[\.\-\–\:]|\Z)'
        m = re.search(pat, body, re.DOTALL)
        if m and len(clean_txt(m.group(1))) > 20:
            txt = clean_txt(m.group(1))
            sec_map[i] = SectionModel(
                section_number=c_str,
                section_title=f"Section {c_str}",
                full_text=txt,
                searchable_chunk=f"Police Act 2020 | Section {c_str} | {txt}"
            )
        else:
            m_iso = list(re.finditer(rf'(?:^|\n|\s){c_str}\s*[\.\-\–\:]', body))
            if m_iso:
                s_idx = m_iso[0].end()
                txt = clean_txt(body[s_idx:min(len(body), s_idx + 2200)])
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=txt,
                    searchable_chunk=f"Police Act 2020 | Section {c_str} | {txt}"
                )

    secs = [sec_map[k] for k in sorted(sec_map.keys())]
    model = StatuteModel(
        statute_id="police_act_2020",
        statute_title="Nigeria Police Act 2020",
        short_title="Police Act 2020",
        year=2020,
        total_sections_found=len(secs),
        expected_sections=142,
        sections=secs
    )
    with open(OUT / "police_act_2020.json", "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"[✓] Police Act 2020: {len(secs)} / 142")

# 3. PENAL CODE ACT (Parse all Federal and Code Sections)
def fix_penal_code():
    reader = PdfReader(str(RAW / "penal-code-northern-states-1960.pdf"))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)
    
    # Match all sections formatted as: \n410. or \n 410.
    pat = re.compile(r'(?:\n|\A)\s*(\d{1,3})\s*[\.\-\–\:]\s*([^\n\(\)\.\—]{0,90})?\n(.*?)(?=(?:\n|\A)\s*\d{1,3}\s*[\.\-\–\:]|\Z)', re.DOTALL)
    matches = list(pat.finditer(raw))
    sec_map = {}

    for m in matches:
        s_num = int(m.group(1))
        title = clean_txt(m.group(2)) or f"Section {s_num}"
        body = clean_txt(m.group(3))
        if len(body) > 20 and s_num not in sec_map:
            sec_map[s_num] = SectionModel(
                section_number=str(s_num),
                section_title=title,
                full_text=body,
                searchable_chunk=f"Penal Code | Section {s_num}: {title} | {body}"
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
    with open(OUT / "penal_code_act_1960.json", "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"[✓] Penal Code Act: {len(secs)} sections parsed")

if __name__ == "__main__":
    fix_evidence_act()
    fix_police_act()
    fix_penal_code()
