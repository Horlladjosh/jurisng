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

CORPUS_RULES = [
    {
        "id": "cfrn_1999",
        "title": "Constitution of the Federal Republic of Nigeria 1999",
        "short": "CFRN 1999",
        "year": 1999,
        "max_sec": 320,
        "pdf": "cfrn_1999.pdf",
        "json": "cfrn_1999.json",
        "body_start": r'PART\s+I\s*[-–—]?\s*FEDERAL\s+REPUBLIC\s+OF\s+NIGERIA|1\.\s*\(1\)\s*This\s+Constitution\s+is\s+supreme'
    },
    {
        "id": "child_rights_act_2003",
        "title": "Child's Rights Act 2003",
        "short": "Child's Rights Act 2003",
        "year": 2003,
        "max_sec": 278,
        "pdf": "child-rights-act.pdf",
        "json": "child_rights_act_2003.json",
        "body_start": r'ENACTED\s+by\s+the\s+National\s+Assembly|PART\s+I\s*[-–—]?\s*BEST\s+INTERESTS|1\.\s*In every action taken'
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
        "pdf": "police_act_2020.pdf",
        "json": "police_act_2020.json",
        "body_start": r'ENACTED\s+by\s+the\s+National\s+Assembly|PART\s+I\s*[-–—]?\s*OBJECTIVES|1\.\s+The objective of this Act'
    },
    {
        "id": "land_use_act_1978",
        "title": "Land Use Act 1978",
        "short": "Land Use Act 1978",
        "year": 1978,
        "max_sec": 51,
        "pdf": "land-use-act.pdf",
        "json": "land_use_act_1978.json",
        "body_start": r'PART\s+I\s*[-–—]?\s*GENERAL|1\.\s+Subject to the provisions of this Act'
    },
    {
        "id": "penal_code_act_1960",
        "title": "Penal Code Act (Federal Provisions)",
        "short": "Penal Code Act",
        "year": 1960,
        "max_sec": 73,
        "pdf": "penal-code-northern-states-1960.pdf",
        "json": "penal_code_act_1960.json",
        "body_start": r'THE\s+SCHEDULE|1\.\s+This Act may be cited|PART\s+I'
    }
]

def build_corpus():
    raw_dir = Path("data/raw_pdfs")
    out_dir = Path("data/json_laws")

    print("Building Clean Substantive Laws (Bypassing TOC & Indexing Full Body)...\n")

    for cfg in CORPUS_RULES:
        pdf_path = raw_dir / cfg["pdf"]
        out_path = out_dir / cfg["json"]

        if not pdf_path.exists():
            print(f"[-] Missing: {pdf_path.name}")
            continue

        reader = PdfReader(str(pdf_path))
        raw_pages = []
        for p in reader.pages:
            t = p.extract_text() or ""
            t = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', t, flags=re.IGNORECASE)
            t = re.sub(r'Page\s+\d+\s+of\s+\d+', '', t, flags=re.IGNORECASE)
            raw_pages.append(t)

        full_raw = "\n".join(raw_pages)
        start_match = re.search(cfg["body_start"], full_raw, re.IGNORECASE)
        body = full_raw[start_match.start():] if start_match else full_raw

        sections_dict = {}
        max_sec = cfg["max_sec"]

        # Pass 1: Strict sequential regex
        for i in range(1, max_sec + 1):
            curr_num = str(i)
            next_num = str(i + 1) if i < max_sec else r'(?:SCHEDULE|Citation|PART|\Z)'

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

        # Pass 2: Fallback anchor for any missed sections
        for i in range(1, max_sec + 1):
            if i not in sections_dict:
                curr_num = str(i)
                m_iso = list(re.finditer(rf'(?:^|\n|\s){curr_num}\s*[\.\-\–\:]\s*', body))
                if m_iso:
                    start_idx = m_iso[0].end()
                    snippet = body[start_idx:min(len(body), start_idx + 2200)]
                    clean = re.sub(r'\s+', ' ', snippet).strip()
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
        print(f"[{pct:>5.1f}%] {cfg['short']:<28}: {len(sorted_secs):>3} / {max_sec} -> {out_path.name}")

if __name__ == "__main__":
    build_corpus()
