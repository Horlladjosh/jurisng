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

def rebuild_clean_cfrn():
    pdf_path = Path("data/raw_pdfs/cfrn_1999.pdf")
    out_path = Path("data/json_laws/cfrn_1999.json")

    reader = PdfReader(str(pdf_path))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)
    
    # Strip running headers/footers
    raw = re.sub(r'Constitution of the Federal Republic of Nigeria.*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'Page\s+\d+\s+of\s+\d+', '', raw, flags=re.IGNORECASE)

    # Substantive start: 2nd occurrence of "CHAPTER I" or after "We the people"
    preamble = re.search(r'We\s+the\s+people\s+of\s+the\s+Federal\s+Republic\s+of\s+Nigeria|PART\s+I\s*[-–—]?\s*FEDERAL\s+REPUBLIC', raw, re.IGNORECASE)
    substantive_body = raw[preamble.start():] if preamble else raw

    sec_map = {}
    for i in range(1, 321):
        c_str = str(i)
        n_str = str(i + 1) if i < 320 else r'(?:SCHEDULE|\Z)'

        # Match section number and capture until next section number
        pat = rf'(?:^|\n|\s{{2,}}){c_str}\s*[\.\-\–\:]\s*(.*?)(?=(?:\n|\s{{2,}}){n_str}\s*[\.\-\–\:]|\Z)'
        m = re.search(pat, substantive_body, re.DOTALL)

        if m and len(m.group(1).strip()) > 35:
            clean = re.sub(r'\s+', ' ', m.group(1)).strip()
            sec_map[i] = SectionModel(
                section_number=c_str,
                section_title=f"Section {c_str}",
                full_text=clean,
                searchable_chunk=f"CFRN 1999 | Section {c_str}: Section {c_str} | {clean}"
            )
        else:
            # Fallback anchor
            m_iso = list(re.finditer(rf'(?:^|\n|\s){c_str}\s*[\.\-\–\:]\s*', substantive_body))
            if m_iso:
                # Pick match that occurs after preamble
                s_idx = m_iso[0].end()
                clean = re.sub(r'\s+', ' ', substantive_body[s_idx:min(len(substantive_body), s_idx + 2500)]).strip()
                sec_map[i] = SectionModel(
                    section_number=c_str,
                    section_title=f"Section {c_str}",
                    full_text=clean,
                    searchable_chunk=f"CFRN 1999 | Section {c_str}: Section {c_str} | {clean}"
                )

    secs = [sec_map[k] for k in sorted(sec_map.keys())]

    model = StatuteModel(
        statute_id="cfrn_1999",
        statute_title="Constitution of the Federal Republic of Nigeria 1999",
        short_title="CFRN 1999",
        year=1999,
        total_sections_found=len(secs),
        expected_sections=320,
        sections=secs
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"[✓] CFRN 1999 Cleaned: {len(secs)} / 320 -> {out_path.name}")

if __name__ == "__main__":
    rebuild_clean_cfrn()
