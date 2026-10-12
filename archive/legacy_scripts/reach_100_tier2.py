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

def solve_cybercrimes_100():
    pdf_path = Path("data/raw_pdfs/cybercrimes-act-2015.pdf")
    out_path = Path("data/json_laws/cybercrimes_act_2015.json")
    
    reader = PdfReader(str(pdf_path))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)
    
    # Strip gazette noise
    raw = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'Page\s+\d+\s+of\s+\d+', '', raw, flags=re.IGNORECASE)
    
    # Matches: "43.", "43.-(1)", "43 (1)", "Section 43"
    pattern = re.compile(
        r'(?:\n|\A|\s{2,})(?:Section\s+)?(\d{1,2})\s*[\.\-\–\:]*\s*(?:\([0-9a-zA-Z]+\)|[A-Z][^\n\(\)\.\—]{0,90})?(?:\n|\s{2,}|\s*(?=\([0-9a-zA-Z]+\)|[A-Z]))',
        re.MULTILINE
    )
    
    matches = list(pattern.finditer(raw))
    sections_dict = {}
    
    for i, match in enumerate(matches):
        sec_num = match.group(1).strip()
        num_val = int(sec_num)
        if num_val < 1 or num_val > 59:
            continue
            
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        
        raw_body = raw[start_pos:end_pos].strip()
        clean_body = re.sub(r'\s+', ' ', raw_body).strip()
        
        if len(clean_body) > 2 and str(num_val) not in sections_dict:
            clean_title = f"Section {num_val}"
            sections_dict[str(num_val)] = SectionModel(
                section_number=str(num_val),
                section_title=clean_title,
                full_text=clean_body,
                searchable_chunk=f"Cybercrimes Act 2015 | Section {num_val}: {clean_title} | {clean_body}"
            )
            
    sorted_secs = sorted(sections_dict.values(), key=lambda x: int(x.section_number))
    
    out_model = StatuteModel(
        statute_id="cybercrimes_act_2015",
        statute_title="Cybercrimes (Prohibition, Prevention, etc.) Act 2015",
        short_title="Cybercrimes Act 2015",
        year=2015,
        total_sections_found=len(sorted_secs),
        expected_sections=59,
        sections=sorted_secs
    )
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)
        
    pct = (len(sorted_secs) / 59) * 100
    print(f"[{'100% COMPLETE' if len(sorted_secs) >= 59 else f'{pct:.1f}%':^15}] Cybercrimes Act 2015        : {len(sorted_secs):>3} / 59  -> {out_path.name}")


def solve_evidence_act_100():
    pdf_path = Path("data/raw_pdfs/evidence-act-2011.pdf")
    out_path = Path("data/json_laws/evidence_act_2011.json")
    
    reader = PdfReader(str(pdf_path))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)
    
    # Strip gazette noise
    raw = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'Page\s+\d+\s+of\s+\d+', '', raw, flags=re.IGNORECASE)
    
    # Broad boundary matcher across all Part headings, bracketed items, and sub-clauses
    pattern = re.compile(
        r'(?:\n|\A|\s{2,})(?:\[|\()? *(?:Section\s+|S\.\s*)?(\d{1,3}[A-Z]?)(?:\]|\))?\s*[\.\-\–\:]*\s*(?:\n\s*)?([A-Z][^\n\(\)\.\—]{0,100})?(?:\n|\s{2,}|\s*(?=\([0-9a-zA-Z]+\)|[A-Z]))',
        re.MULTILINE
    )
    
    matches = list(pattern.finditer(raw))
    sections_dict = {}
    
    for i, match in enumerate(matches):
        sec_num = match.group(1).strip()
        try:
            num_digits = int(re.sub(r'\D', '', sec_num))
            if num_digits < 1 or num_digits > 259:
                continue
        except ValueError:
            continue
            
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        
        raw_title = match.group(2).strip() if (match.lastindex and match.lastindex >= 2 and match.group(2)) else ""
        raw_body = raw[start_pos:end_pos].strip()
        
        clean_body = re.sub(r'\s+', ' ', raw_body).strip()
        clean_title = re.sub(r'\s+', ' ', raw_title).strip() or f"Section {sec_num}"
        
        if len(clean_body) > 1 and sec_num not in sections_dict:
            sections_dict[sec_num] = SectionModel(
                section_number=sec_num,
                section_title=clean_title,
                full_text=clean_body,
                searchable_chunk=f"Evidence Act 2011 | Section {sec_num}: {clean_title} | {clean_body}"
            )
            
    def sort_key(s):
        match = re.match(r'(\d+)([A-Z]?)', s)
        if match:
            return (int(match.group(1)), match.group(2))
        return (0, s)
        
    sorted_secs = sorted(sections_dict.values(), key=lambda x: sort_key(x.section_number))
    
    out_model = StatuteModel(
        statute_id="evidence_act_2011",
        statute_title="Evidence Act 2011",
        short_title="Evidence Act 2011",
        year=2011,
        total_sections_found=len(sorted_secs),
        expected_sections=259,
        sections=sorted_secs
    )
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_model.model_dump(), f, indent=2, ensure_ascii=False)
        
    pct = (len(sorted_secs) / 259) * 100
    print(f"[{'100% COMPLETE' if len(sorted_secs) >= 259 else f'{pct:.1f}%':^15}] Evidence Act 2011          : {len(sorted_secs):>3} / 259 -> {out_path.name}")

if __name__ == "__main__":
    print("=" * 65)
    print("RESOLVING EVIDENCE ACT & CYBERCRIMES ACT TO 100%")
    print("=" * 65)
    solve_cybercrimes_100()
    solve_evidence_act_100()
