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

def parse_full_cybercrimes():
    pdf_path = Path("data/raw_pdfs/cybercrimes-act-2015.pdf")
    out_path = Path("data/json_laws/cybercrimes_act_2015.json")
    
    if not pdf_path.exists():
        print(f"[-] File not found at {pdf_path}")
        return

    reader = PdfReader(str(pdf_path))
    raw_pages = []
    for p in reader.pages:
        t = p.extract_text() or ""
        t = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', t, flags=re.IGNORECASE)
        t = re.sub(r'Page\s+\d+\s+of\s+\d+', '', t, flags=re.IGNORECASE)
        raw_pages.append(t)
        
    raw = "\n".join(raw_pages)
    
    # Bypass Table of Contents
    start_body = re.search(r'PART\s+I\s*[-–—]?\s*OBJECTIVES|1\.\s+The objectives of this Act', raw, re.IGNORECASE)
    body_text = raw[start_body.start():] if start_body else raw

    # Section matching pattern
    pattern = re.compile(
        r'(?:\n|\A|\s{2,})(?:Section\s+|S\.\s*)?(\d{1,2})\s*[\.\-\–\:]*\s*(?:\n\s*)?([^\n\(\)\.\—]{0,100})?(?:\n|\s{2,}|\s*(?=\([0-9a-zA-Z]+\)|[A-Z]))',
        re.MULTILINE
    )
    
    matches = list(pattern.finditer(body_text))
    sections_dict = {}
    
    for i, m in enumerate(matches):
        sec_num = m.group(1).strip()
        num_val = int(sec_num)
        if num_val < 1 or num_val > 59:
            continue
            
        start_pos = m.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)
        
        chunk = body_text[start_pos:end_pos].strip()
        clean_body = re.sub(r'\s+', ' ', chunk).strip()
        
        raw_title = m.group(2).strip() if (m.lastindex and m.lastindex >= 2 and m.group(2)) else ""
        clean_title = re.sub(r'\s+', ' ', raw_title).strip() or f"Section {num_val}"
        
        if len(clean_body) > 5 and num_val not in sections_dict:
            sections_dict[num_val] = SectionModel(
                section_number=str(num_val),
                section_title=clean_title,
                full_text=clean_body,
                searchable_chunk=f"Cybercrimes Act 2015 | Section {num_val}: {clean_title} | {clean_body}"
            )
            
    # Rescue pass for any missed number (1 to 59)
    for target in range(1, 60):
        if target not in sections_dict:
            m_sec = re.search(rf'(?:^|\n|\s+){target}\s*[\.\-\–\:\)]\s*(.*?)(?=\n\s*\d{{1,2}}\s*[\.\-\–\:\)]|\Z)', body_text, re.DOTALL)
            if m_sec and m_sec.group(1):
                clean_body = re.sub(r'\s+', ' ', m_sec.group(1)).strip()
                if len(clean_body) > 5:
                    title = f"Section {target}"
                    sections_dict[target] = SectionModel(
                        section_number=str(target),
                        section_title=title,
                        full_text=clean_body[:3000],
                        searchable_chunk=f"Cybercrimes Act 2015 | Section {target}: {title} | {clean_body[:3000]}"
                    )

    sorted_secs = [sections_dict[k] for k in sorted(sections_dict.keys())]
    
    out_model = StatuteModel(
        statute_id="cybercrimes_act_2015",
        statute_title="Cybercrimes (Prohibition, Prevention, etc.) Act 2015",
        short_title="Cybercrimes Act 2015",
        year=2015,
        total_sections_found=len(sorted_secs),
        expected_sections=59,
        sections=sorted_secs
    )
    
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)
        
    pct = (len(sorted_secs) / 59) * 100
    tag = "100% COMPLETE" if len(sorted_secs) == 59 else f"{pct:.1f}%"
    print(f"[{tag:^15}] Cybercrimes Act 2015: {len(sorted_secs):>2} / 59 -> {out_file.name}")

if __name__ == "__main__":
    parse_full_cybercrimes()
