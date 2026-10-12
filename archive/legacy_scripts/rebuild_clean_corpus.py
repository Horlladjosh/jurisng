import re
import json
from pathlib import Path
from pypdf import PdfReader
from pydantic import BaseModel
from typing import List, Dict

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

CORPUS_CONFIG = [
    {
        "id": "cfrn_1999",
        "title": "Constitution of the Federal Republic of Nigeria 1999",
        "short": "CFRN 1999",
        "year": 1999,
        "max_sec": 320,
        "pdf": "cfrn-1999.pdf",
        "json": "cfrn_1999.json",
        "body_start": r'PART\s+I\s*[-–—]?\s*FEDERAL\s+REPUBLIC|1\.\s*\(1\)\s*This Constitution is supreme'
    },
    {
        "id": "acja_2015",
        "title": "Administration of Criminal Justice Act 2015",
        "short": "ACJA 2015",
        "year": 2015,
        "max_sec": 495,
        "pdf": "acja-2015.pdf",
        "json": "acja_2015.json",
        "body_start": r'ENACTED\s+by\s+the\s+National\s+Assembly|PART\s+1\s*[-–—]?\s*PRELIMINARY|1\.\s*\(1\)\s*The purpose of this Act'
    },
    {
        "id": "evidence_act_2011",
        "title": "Evidence Act 2011",
        "short": "Evidence Act 2011",
        "year": 2011,
        "max_sec": 259,
        "pdf": "evidence-act-2011.pdf",
        "json": "evidence_act_2011.json",
        "body_start": r'ENACTED\s+by\s+the\s+National\s+Assembly|PART\s+I\s*[-–—]?\s*GENERAL|1\.\s+Evidence may be given'
    },
    {
        "id": "police_act_2020",
        "title": "Nigeria Police Act 2020",
        "short": "Police Act 2020",
        "year": 2020,
        "max_sec": 142,
        "pdf": "police-act-2020.pdf",
        "json": "police_act_2020.json",
        "body_start": r'ENACTED\s+by\s+the\s+National\s+Assembly|PART\s+I\s*[-–—]?\s*OBJECTIVES|1\.\s+The objective of this Act'
    },
    {
        "id": "labour_act",
        "title": "Labour Act",
        "short": "Labour Act",
        "year": 2004,
        "max_sec": 92,
        "pdf": "labour-act.pdf",
        "json": "labour_act.json",
        "body_start": r'PART\s+I\s*[-–—]?\s*PUBLIC\s+EMPLOYMENT|PART\s+I\s*[-–—]?\s*WAGES|1\.\s*\(1\)\s*Every contract of employment|1\.\s*\(1\)\s*Not later than'
    },
    {
        "id": "land_use_act_1978",
        "title": "Land Use Act 1978",
        "short": "Land Use Act 1978",
        "year": 1978,
        "max_sec": 51,
        "pdf": "land-use-act-1978.pdf",
        "json": "land_use_act_1978.json",
        "body_start": r'PART\s+I\s*[-–—]?\s*GENERAL|1\.\s+Subject to the provisions of this Act'
    }
]

def clean_statute(cfg: dict):
    pdf_path = Path("data/raw_pdfs") / cfg["pdf"]
    out_path = Path("data/json_laws") / cfg["json"]
    
    if not pdf_path.exists():
        print(f"[-] PDF not found: {pdf_path}")
        return

    reader = PdfReader(str(pdf_path))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)
    raw = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'Page\s+\d+\s+of\s+\d+', '', raw, flags=re.IGNORECASE)

    # Bypass TOC completely
    start_match = re.search(cfg["body_start"], raw, re.IGNORECASE)
    body = raw[start_match.start():] if start_match else raw

    sections_dict = {}
    max_sec = cfg["max_sec"]

    for i in range(1, max_sec + 1):
        curr_num = str(i)
        next_num = str(i + 1) if i < max_sec else r'(?:SCHEDULE|Citation|\Z)'
        
        # Capture from "i." to "(i+1)."
        pat = rf'(?:^|\n|\s{{2,}})(?:Section\s+|S\.\s*)?{curr_num}\s*[\.\-\–\:]\s*(.*?)(?=(?:\n|\s{{2,}})(?:Section\s+|S\.\s*)?{next_num}\s*[\.\-\–\:]|\Z)'
        m = re.search(pat, body, re.DOTALL)
        
        if m and len(m.group(1).strip()) > 30:
            clean = re.sub(r'\s+', ' ', m.group(1)).strip()
            title = f"Section {curr_num}"
            sections_dict[i] = SectionModel(
                section_number=curr_num,
                section_title=title,
                full_text=clean,
                searchable_chunk=f"{cfg['short']} | Section {curr_num}: {title} | {clean}"
            )
        else:
            # Fallback for margin format
            pat_fallback = rf'(?:^|\n|\s{{2,}}){curr_num}\s+([A-Z\(\(].*?)(?=(?:\n|\s{{2,}}){next_num}\s+[\(A-Z]|\Z)'
            mf = re.search(pat_fallback, body, re.DOTALL)
            if mf and len(mf.group(1).strip()) > 30:
                clean = re.sub(r'\s+', ' ', mf.group(1)).strip()
                title = f"Section {curr_num}"
                sections_dict[i] = SectionModel(
                    section_number=curr_num,
                    section_title=title,
                    full_text=clean,
                    searchable_chunk=f"{cfg['short']} | Section {curr_num}: {title} | {clean}"
                )

    sorted_secs = [sections_dict[k] for k in sorted(sections_dict.keys())]

    out_model = StatuteModel(
        statute_id=cfg["id"],
        statute_title=cfg["title"],
        short_title=cfg["short"],
        year=cfg["year"],
        total_sections_found=len(sorted_secs),
        expected_sections=max_sec,
        sections=sorted_secs
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)

    pct = (len(sorted_secs) / max_sec) * 100
    print(f"[{pct:>5.1f}%] {cfg['short']:<25}: {len(sorted_secs):>3} / {max_sec} -> {out_path.name}")

if __name__ == "__main__":
    print("Rebuilding substantive bodies (bypassing TOC)...")
    for cfg in CORPUS_CONFIG:
        clean_statute(cfg)
