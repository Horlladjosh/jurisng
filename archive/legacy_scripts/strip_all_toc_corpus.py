import re
import json
from pathlib import Path
from pypdf import PdfReader
from pydantic import BaseModel
from typing import List, Dict, Optional

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
        "start_markers": ["We the people of the Federal Republic of Nigeria", "CHAPTER I\nPART I", "This Constitution is supreme"]
    },
    {
        "id": "acja_2015",
        "title": "Administration of Criminal Justice Act 2015",
        "short": "ACJA 2015",
        "year": 2015,
        "max_sec": 495,
        "pdf": "acja-2015.pdf",
        "json": "acja_2015.json",
        "start_markers": ["ENACTED by the National Assembly", "PART 1 - PRELIMINARY", "1. (1) The purpose of this Act"]
    },
    {
        "id": "child_rights_act_2003",
        "title": "Child's Rights Act 2003",
        "short": "Child's Rights Act 2003",
        "year": 2003,
        "max_sec": 278,
        "pdf": "child-rights-act.pdf",
        "json": "child_rights_act_2003.json",
        "start_markers": ["ENACTED by the National Assembly", "PART I - BEST INTERESTS", "1. In every action taken"]
    },
    {
        "id": "evidence_act_2011",
        "title": "Evidence Act 2011",
        "short": "Evidence Act 2011",
        "year": 2011,
        "max_sec": 259,
        "pdf": "evidence-act-2011.pdf",
        "json": "evidence_act_2011.json",
        "start_markers": ["ENACTED by the National Assembly", "PART I - GENERAL", "1. Evidence may be given"]
    },
    {
        "id": "police_act_2020",
        "title": "Nigeria Police Act 2020",
        "short": "Police Act 2020",
        "year": 2020,
        "max_sec": 142,
        "pdf": "police_act_2020.pdf",
        "json": "police_act_2020.json",
        "start_markers": ["ENACTED by the National Assembly", "PART I - OBJECTIVES", "1. The objective of this Act"]
    },
    {
        "id": "labour_act",
        "title": "Labour Act",
        "short": "Labour Act",
        "year": 2004,
        "max_sec": 92,
        "pdf": "labour-act.pdf",
        "json": "labour_act.json",
        "start_markers": ["PART I\nPROTECTION OF WAGES", "PART I - PROTECTION", "1. (1) Every contract of employment", "1. (1) Not later than"]
    },
    {
        "id": "employee_compensation_act_2010",
        "title": "Employees' Compensation Act 2010",
        "short": "Employees' Compensation Act 2010",
        "year": 2010,
        "max_sec": 74,
        "pdf": "employee-compensation-act-2010.pdf",
        "json": "employee_compensation_act_2010.json",
        "start_markers": ["ENACTED by the National Assembly", "PART I - OBJECTIVES", "1. The objectives of this Act"]
    },
    {
        "id": "cybercrimes_act_2015",
        "title": "Cybercrimes (Prohibition, Prevention, etc.) Act 2015",
        "short": "Cybercrimes Act 2015",
        "year": 2015,
        "max_sec": 59,
        "pdf": "cybercrimes-act-2015.pdf",
        "json": "cybercrimes_act_2015.json",
        "start_markers": ["ENACTED by the National Assembly", "PART I - OBJECTIVES", "1. The objectives of this Act"]
    },
    {
        "id": "land_use_act_1978",
        "title": "Land Use Act 1978",
        "short": "Land Use Act 1978",
        "year": 1978,
        "max_sec": 51,
        "pdf": "land-use-act.pdf",
        "json": "land_use_act_1978.json",
        "start_markers": ["PART I - GENERAL", "1. Subject to the provisions of this Act"]
    },
    {
        "id": "penal_code_act_1960",
        "title": "Penal Code Act (Federal Provisions)",
        "short": "Penal Code Act",
        "year": 1960,
        "max_sec": 73,
        "pdf": "penal-code-northern-states-1960.pdf",
        "json": "penal_code_act_1960.json",
        "start_markers": ["THE SCHEDULE", "1. This Act may be cited", "CHAPTER I"]
    }
]

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text or '').strip()

def process_statute(cfg: dict):
    raw_path = Path("data/raw_pdfs") / cfg["pdf"]
    out_path = Path("data/json_laws") / cfg["json"]

    if not raw_path.exists():
        print(f"[-] Missing PDF: {raw_path.name}")
        return

    reader = PdfReader(str(raw_path))
    pages = [p.extract_text() or "" for p in reader.pages]

    # Find the exact page where TOC ends and enacted law begins
    start_page_idx = 0
    found_marker = False
    for p_idx, p_text in enumerate(pages):
        for marker in cfg["start_markers"]:
            if marker.lower() in p_text.lower():
                start_page_idx = p_idx
                found_marker = True
                break
        if found_marker:
            break

    # Join only substantive pages
    substantive_pages = pages[start_page_idx:]
    substantive_raw = "\n".join(substantive_pages)
    
    # Strip running headers
    substantive_raw = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', substantive_raw, flags=re.IGNORECASE)
    substantive_raw = re.sub(r'Constitution of the Federal Republic of Nigeria.*', '', substantive_raw, flags=re.IGNORECASE)
    substantive_raw = re.sub(r'Page\s+\d+\s+of\s+\d+', '', substantive_raw, flags=re.IGNORECASE)

    max_sec = cfg["max_sec"]
    sec_map = {}

    for i in range(1, max_sec + 1):
        c_str = str(i)
        n_str = str(i + 1) if i < max_sec else r'(?:SCHEDULE|Citation|PART|\Z)'

        # Strict body regex
        pat = rf'(?:\n|\A|\s{{2,}})(?:Section\s+|S\.\s*)?{c_str}\s*[\.\-\–\:]\s*(.*?)(?=(?:\n|\s{{2,}})(?:Section\s+|S\.\s*)?{n_str}\s*[\.\-\–\:]|\Z)'
        m = re.search(pat, substantive_raw, re.DOTALL)

        if m and len(clean_text(m.group(1))) > 25:
            body = clean_text(m.group(1))
            # Verification: Reject if this body is still just a TOC listing
            if not re.search(rf'\b{i+1}\.\s+[A-Z][a-z]+.*\b{i+2}\.\s+[A-Z][a-z]+', body):
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=body,
                    searchable_chunk=f"{cfg['short']} | Section {c_str}: Section {c_str} | {body}"
                )

        # Fallback anchor search strictly within substantive pages
        if i not in sec_map:
            m_iso = list(re.finditer(rf'(?:\n|\A|\s){c_str}\s*[\.\-\–\:]\s*(?:\([0-9a-zA-Z]+\)|[A-Z])', substantive_raw))
            if m_iso:
                idx = m_iso[0].start()
                snippet = substantive_raw[idx:min(len(substantive_raw), idx + 3500)]
                clean_snip = clean_text(snippet)
                if not re.search(rf'\b{i+1}\.\s+[A-Z][a-z]+.*\b{i+2}\.\s+[A-Z][a-z]+', clean_snip):
                    sec_map[i] = SectionModel(
                        section_number=c_str,
                        section_title=f"Section {c_str}",
                        full_text=clean_snip,
                        searchable_chunk=f"{cfg['short']} | Section {c_str}: Section {c_str} | {clean_snip}"
                    )

    secs = [sec_map[k] for k in sorted(sec_map.keys())]

    out_model = StatuteModel(
        statute_id=cfg["id"],
        statute_title=cfg["title"],
        short_title=cfg["short"],
        year=cfg["year"],
        total_sections_found=len(secs),
        expected_sections=max_sec,
        sections=secs
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)

    pct = (len(secs) / max_sec) * 100
    print(f"[{pct:>5.1f}%] {cfg['short']:<28}: {len(secs):>3} / {max_sec} (TOC Bypassed at Page {start_page_idx + 1})")

if __name__ == "__main__":
    print("Purging TOC and Rebuilding Substantive Laws Across Corpus...\n")
    for cfg in CORPUS:
        process_statute(cfg)
