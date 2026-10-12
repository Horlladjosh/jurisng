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

def clean_txt(t: str) -> str:
    return re.sub(r'\s+', ' ', t or '').strip()

def extract_statute(statute_id: str, title: str, short: str, year: int, max_sec: int, pdf_name: str, start_page: int, out_name: str):
    reader = PdfReader(str(RAW / pdf_name))
    raw_pages = [p.extract_text() or "" for p in reader.pages[start_page - 1:]]
    raw = "\n".join(raw_pages)
    raw = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', raw, flags=re.IGNORECASE)

    sec_map = {}
    
    # Token-based sequential locator
    # Finds any occurrence of the number as a discrete section header
    for i in range(1, max_sec + 1):
        c_str = str(i)
        
        # Look for section header patterns: "84.", "84-", "84 —", "84 (1)", "\n84\n"
        patterns = [
            rf'(?:\n|\A|\s{{2,}})(?:Section\s+|S\.\s*)?{c_str}\s*[\.\-\–\—\:]\s*(?:[A-Z\(\(])',
            rf'(?:\n|\A|\s{{2,}}){c_str}\s*\n\s*[A-Z]',
            rf'(?:\n|\A|\s{{2,}}){c_str}\s*[\.\-\–\—\:]\s*\([0-9a-zA-Z]+\)',
            rf'(?:\n|\A|\s{{2,}}){c_str}\s*[\.\-\–\—\:]'
        ]
        
        match_idx = None
        for pat in patterns:
            m = list(re.finditer(pat, raw))
            if m:
                match_idx = m[0].start()
                break

        if match_idx is not None:
            # Slices text up to 4000 characters or until next likely section marker
            chunk = raw[match_idx:min(len(raw), match_idx + 4000)]
            
            # Find boundary to next section
            next_num = str(i + 1)
            next_pat = rf'(?:\n|\s{{2,}})(?:Section\s+|S\.\s*)?{next_num}\s*[\.\-\–\—\:]'
            m_next = re.search(next_pat, chunk[20:])
            
            body = chunk[:m_next.start() + 20] if m_next else chunk
            clean_body = clean_txt(body)
            
            if len(clean_body) > 15:
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=clean_body,
                    searchable_chunk=f"{short} | Section {c_str} | {clean_body}"
                )

    secs = [sec_map[k] for k in sorted(sec_map.keys())]

    model = StatuteModel(
        statute_id=statute_id,
        statute_title=title,
        short_title=short,
        year=year,
        total_sections_found=len(secs),
        expected_sections=max_sec,
        sections=secs
    )

    with open(OUT / out_name, "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2, ensure_ascii=False)

    pct = (len(secs) / max_sec) * 100
    print(f"[✓] {short:<25}: {len(secs):>3} / {max_sec} ({pct:.1f}%) -> {out_name}")

if __name__ == "__main__":
    extract_statute("evidence_act_2011", "Evidence Act 2011", "Evidence Act 2011", 2011, 259, "evidence-act-2011.pdf", 10, "evidence_act_2011.json")
    extract_statute("police_act_2020", "Nigeria Police Act 2020", "Police Act 2020", 2020, 142, "police_act_2020.pdf", 8, "police_act_2020.json")
    extract_statute("labour_act", "Labour Act", "Labour Act", 2004, 92, "labour-act.pdf", 4, "labour_act.json")
