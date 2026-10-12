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

CORPUS = [
    {
        "id": "cfrn_1999",
        "title": "Constitution of the Federal Republic of Nigeria 1999",
        "short": "CFRN 1999",
        "year": 1999,
        "max_sec": 320,
        "pdf": "cfrn_1999.pdf",
        "json": "cfrn_1999.json",
        "start_page": 23
    },
    {
        "id": "acja_2015",
        "title": "Administration of Criminal Justice Act 2015",
        "short": "ACJA 2015",
        "year": 2015,
        "max_sec": 495,
        "pdf": "acja-2015.pdf",
        "json": "acja_2015.json",
        "start_page": 21
    },
    {
        "id": "child_rights_act_2003",
        "title": "Child's Rights Act 2003",
        "short": "Child's Rights Act 2003",
        "year": 2003,
        "max_sec": 278,
        "pdf": "child-rights-act.pdf",
        "json": "child_rights_act_2003.json",
        "start_page": 12
    },
    {
        "id": "evidence_act_2011",
        "title": "Evidence Act 2011",
        "short": "Evidence Act 2011",
        "year": 2011,
        "max_sec": 259,
        "pdf": "evidence-act-2011.pdf",
        "json": "evidence_act_2011.json",
        "start_page": 10
    },
    {
        "id": "police_act_2020",
        "title": "Nigeria Police Act 2020",
        "short": "Police Act 2020",
        "year": 2020,
        "max_sec": 142,
        "pdf": "police_act_2020.pdf",
        "json": "police_act_2020.json",
        "start_page": 8
    },
    {
        "id": "labour_act",
        "title": "Labour Act",
        "short": "Labour Act",
        "year": 2004,
        "max_sec": 92,
        "pdf": "labour-act.pdf",
        "json": "labour_act.json",
        "start_page": 4
    },
    {
        "id": "employee_compensation_act_2010",
        "title": "Employees' Compensation Act 2010",
        "short": "Employees' Compensation Act 2010",
        "year": 2010,
        "max_sec": 74,
        "pdf": "employee-compensation-act-2010.pdf",
        "json": "employee_compensation_act_2010.json",
        "start_page": 7
    },
    {
        "id": "cybercrimes_act_2015",
        "title": "Cybercrimes (Prohibition, Prevention, etc.) Act 2015",
        "short": "Cybercrimes Act 2015",
        "year": 2015,
        "max_sec": 59,
        "pdf": "cybercrimes-act-2015.pdf",
        "json": "cybercrimes_act_2015.json",
        "start_page": 5
    },
    {
        "id": "land_use_act_1978",
        "title": "Land Use Act 1978",
        "short": "Land Use Act 1978",
        "year": 1978,
        "max_sec": 51,
        "pdf": "land-use-act.pdf",
        "json": "land_use_act_1978.json",
        "start_page": 3
    },
    {
        "id": "penal_code_act_1960",
        "title": "Penal Code Act (Federal Provisions)",
        "short": "Penal Code Act",
        "year": 1960,
        "max_sec": 73,
        "pdf": "penal-code-northern-states-1960.pdf",
        "json": "penal_code_act_1960.json",
        "start_page": 1
    }
]

def clean_txt(t: str) -> str:
    return re.sub(r'\s+', ' ', t or '').strip()

def build_statute(cfg: dict):
    raw_path = Path("data/raw_pdfs") / cfg["pdf"]
    out_path = Path("data/json_laws") / cfg["json"]

    if not raw_path.exists():
        print(f"[-] Missing PDF: {raw_path.name}")
        return

    reader = PdfReader(str(raw_path))
    pages = [p.extract_text() or "" for p in reader.pages]

    start_idx = max(0, cfg["start_page"] - 1)
    substantive_raw = "\n".join(pages[start_idx:])
    
    substantive_raw = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', substantive_raw, flags=re.IGNORECASE)
    substantive_raw = re.sub(r'Constitution of the Federal Republic of Nigeria.*', '', substantive_raw, flags=re.IGNORECASE)
    substantive_raw = re.sub(r'Page\s+\d+\s+of\s+\d+', '', substantive_raw, flags=re.IGNORECASE)

    max_sec = cfg["max_sec"]
    sec_map = {}

    if cfg["id"] == "penal_code_act_1960":
        pat = re.compile(r'(?:\n|\A|\s{2,})(?:Section\s+|S\.\s*)?(\d{1,3})\s*[\.\-\–\:]\s*([^\n\(\)\.\—]{0,90})?\n?(.*?)(?=(?:\n|\s{2,})(?:Section\s+|S\.\s*)?\d{1,3}\s*[\.\-\–\:]|\Z)', re.DOTALL)
        for m in pat.finditer(substantive_raw):
            s_num = int(m.group(1))
            t = clean_txt(m.group(2)) or f"Section {s_num}"
            b = clean_txt(m.group(3))
            if len(b) > 20 and s_num not in sec_map:
                sec_map[s_num] = SectionModel(
                    section_number=str(s_num),
                    section_title=t,
                    full_text=f"{t} {b}",
                    searchable_chunk=f"Penal Code | Section {s_num}: {t} | {b}"
                )
    else:
        for i in range(1, max_sec + 1):
            c_str = str(i)
            n_str = str(i + 1) if i < max_sec else r'(?:SCHEDULE|Citation|PART\s+[V|X|I]+|\Z)'

            pat = rf'(?:\n|\A|\s{{2,}})(?:Section\s+|S\.\s*)?{c_str}\s*[\.\-\–\:]\s*(.*?)(?=(?:\n|\s{{2,}})(?:Section\s+|S\.\s*)?{n_str}\s*[\.\-\–\:]|\Z)'
            m = re.search(pat, substantive_raw, re.DOTALL)

            if m and len(clean_txt(m.group(1))) > 20:
                clean_b = clean_txt(m.group(1))
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=clean_b,
                    searchable_chunk=f"{cfg['short']} | Section {c_str}: Section {c_str} | {clean_b}"
                )
            else:
                m_iso = list(re.finditer(rf'(?:\n|\A|\s){c_str}\s*[\.\-\–\:]\s*(?:\([0-9a-zA-Z]+\)|[A-Z])', substantive_raw))
                if m_iso:
                    idx = m_iso[0].start()
                    snippet = clean_txt(substantive_raw[idx:min(len(substantive_raw), idx + 3500)])
                    sec_map[i] = SectionModel(
                        section_number=c_str,
                        section_title=f"Section {c_str}",
                        full_text=snippet,
                        searchable_chunk=f"{cfg['short']} | Section {c_str}: Section {c_str} | {snippet}"
                    )

    secs = [sec_map[k] for k in sorted(sec_map.keys())]

    model = StatuteModel(
        statute_id=cfg["id"],
        statute_title=cfg["title"],
        short_title=cfg["short"],
        year=cfg["year"],
        total_sections_found=len(secs),
        expected_sections=max_sec,
        sections=secs
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2, ensure_ascii=False)

    pct = (len(secs) / max_sec) * 100
    print(f"[{pct:>5.1f}%] {cfg['short']:<28}: {len(secs):>3} / {max_sec} (Slices from Page {cfg['start_page']})")

if __name__ == "__main__":
    print("Building Guaranteed Non-TOC Corpus...\n")
    for cfg in CORPUS:
        build_statute(cfg)
