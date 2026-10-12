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

# 1. EVIDENCE ACT 2011 (Exact 259 Sections)
def extract_evidence():
    reader = PdfReader(str(RAW / "evidence-act-2011.pdf"))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages[9:]) # Page 10+
    raw = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', raw, flags=re.IGNORECASE)
    
    sec_map = {}
    for i in range(1, 260):
        c_str = str(i)
        n_str = str(i + 1) if i < 259 else r'(?:SCHEDULE|\Z)'
        
        # Matches: "84. (1)", "84.—(1)", "84.-(1)", "84 - ", "84 (1)"
        pat = rf'(?:\n|\A|\s{{2,}}){c_str}\s*[\.\-\–\—\:]?\s*(\([0-9a-zA-Z]+\)|[A-Z\(\(])(.*?)(?=(?:\n|\s{{2,}}){n_str}\s*[\.\-\–\—\:]?\s*[\(A-Z]|\Z)'
        m = re.search(pat, raw, re.DOTALL)
        if m:
            body = clean_txt(f"{m.group(1)} {m.group(2)}")
            if len(body) > 15:
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=body,
                    searchable_chunk=f"Evidence Act 2011 | Section {c_str} | {body}"
                )
        if i not in sec_map:
            # Tolerant single anchor
            m_iso = list(re.finditer(rf'(?:\n|\A|\s){c_str}\s*[\.\-\–\—\:]?\s*(?:\([0-9a-zA-Z]+\)|[A-Z])', raw))
            if m_iso:
                s_idx = m_iso[0].start()
                body = clean_txt(raw[s_idx:min(len(raw), s_idx + 3500)])
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=body,
                    searchable_chunk=f"Evidence Act 2011 | Section {c_str} | {body}"
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
    print(f"[✓] Evidence Act 2011: {len(secs)} / 259 ({(len(secs)/259)*100:.1f}%)")

# 2. POLICE ACT 2020 (Exact 142 Sections)
def extract_police():
    reader = PdfReader(str(RAW / "police_act_2020.pdf"))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages[7:]) # Page 8+
    
    sec_map = {}
    for i in range(1, 143):
        c_str = str(i)
        n_str = str(i + 1) if i < 142 else r'(?:SCHEDULE|\Z)'
        
        pat = rf'(?:\n|\A|\s{{2,}}){c_str}\s*[\.\-\–\—\:]?\s*(\([0-9a-zA-Z]+\)|[A-Z\(\(])(.*?)(?=(?:\n|\s{{2,}}){n_str}\s*[\.\-\–\—\:]?\s*[\(A-Z]|\Z)'
        m = re.search(pat, raw, re.DOTALL)
        if m:
            body = clean_txt(f"{m.group(1)} {m.group(2)}")
            if len(body) > 15:
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=body,
                    searchable_chunk=f"Police Act 2020 | Section {c_str} | {body}"
                )
        if i not in sec_map:
            m_iso = list(re.finditer(rf'(?:\n|\A|\s){c_str}\s*[\.\-\–\—\:]?\s*(?:\([0-9a-zA-Z]+\)|[A-Z])', raw))
            if m_iso:
                s_idx = m_iso[0].start()
                body = clean_txt(raw[s_idx:min(len(raw), s_idx + 3200)])
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=body,
                    searchable_chunk=f"Police Act 2020 | Section {c_str} | {body}"
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
    print(f"[✓] Police Act 2020: {len(secs)} / 142 ({(len(secs)/142)*100:.1f}%)")

# 3. LABOUR ACT (Exact 92 Sections)
def extract_labour():
    reader = PdfReader(str(RAW / "labour-act.pdf"))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages[3:]) # Page 4+
    
    sec_map = {}
    for i in range(1, 93):
        c_str = str(i)
        n_str = str(i + 1) if i < 92 else r'(?:SCHEDULE|\Z)'
        
        pat = rf'(?:\n|\A|\s{{2,}}){c_str}\s*[\.\-\–\—\:]?\s*(\([0-9a-zA-Z]+\)|[A-Z\(\(])(.*?)(?=(?:\n|\s{{2,}}){n_str}\s*[\.\-\–\—\:]?\s*[\(A-Z]|\Z)'
        m = re.search(pat, raw, re.DOTALL)
        if m:
            body = clean_txt(f"{m.group(1)} {m.group(2)}")
            if len(body) > 15:
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=body,
                    searchable_chunk=f"Labour Act | Section {c_str} | {body}"
                )
        if i not in sec_map:
            m_iso = list(re.finditer(rf'(?:\n|\A|\s){c_str}\s*[\.\-\–\—\:]?\s*(?:\([0-9a-zA-Z]+\)|[A-Z])', raw))
            if m_iso:
                s_idx = m_iso[0].end()
                body = clean_txt(raw[s_idx:min(len(raw), s_idx + 3200)])
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=body,
                    searchable_chunk=f"Labour Act | Section {c_str} | {body}"
                )

    secs = [sec_map[k] for k in sorted(sec_map.keys())]
    model = StatuteModel(
        statute_id="labour_act",
        statute_title="Labour Act",
        short_title="Labour Act",
        year=2004,
        total_sections_found=len(secs),
        expected_sections=92,
        sections=secs
    )
    with open(OUT / "labour_act.json", "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"[✓] Labour Act: {len(secs)} / 92 ({(len(secs)/92)*100:.1f}%)")

if __name__ == "__main__":
    extract_evidence()
    extract_police()
    extract_labour()
