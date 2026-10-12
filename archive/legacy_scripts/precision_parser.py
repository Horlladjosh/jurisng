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

def parse_health_act_complete():
    pdf_path = Path("data/raw_pdfs/national-health-act-2014.pdf")
    output_path = Path("data/json_laws/national_health_act_2014.json")
    
    reader = PdfReader(str(pdf_path))
    raw = "\n".join(p.extract_text() or "" for p in reader.pages)
    
    # Matches:
    # 1. "1. Establishment of..."
    # 2. "1.-(1)" or "1 (1)"
    # 3. "\n1\nEstablishment" or "\n 1.\n"
    pattern = re.compile(
        r'(?:\n|\A)\s*([0-9]{1,2})\s*[\.\-\–]?\s*(?:\n\s*)?([A-Z][^\n\(\)\.\—]{2,100})?(?:\n|\s{2,}|\s*(?=\([0-9a-zA-Z]+\)|[A-Z]))',
        re.MULTILINE
    )
    
    matches = list(pattern.finditer(raw))
    sections_dict = {}
    
    for i, match in enumerate(matches):
        sec_num = match.group(1).strip()
        num_int = int(sec_num)
        if num_int > 65 or num_int == 0:
            continue
            
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        
        raw_title = match.group(2).strip() if (match.lastindex and match.lastindex >= 2 and match.group(2)) else ""
        raw_body = raw[start_pos:end_pos].strip()
        
        clean_body = re.sub(r'\s+', ' ', raw_body).strip()
        clean_title = re.sub(r'\s+', ' ', raw_title).strip() or f"Section {sec_num}"
        
        if len(clean_body) > 10 and sec_num not in sections_dict:
            search_chunk = f"National Health Act 2014 | Section {sec_num}: {clean_title} | {clean_body}"
            sections_dict[sec_num] = SectionModel(
                section_number=sec_num,
                section_title=clean_title,
                full_text=clean_body,
                searchable_chunk=search_chunk
            )
            
    sorted_secs = sorted(sections_dict.values(), key=lambda x: int(x.section_number))
    
    model = StatuteModel(
        statute_id="national_health_act_2014",
        statute_title="National Health Act 2014",
        short_title="National Health Act 2014",
        year=2014,
        total_sections_found=len(sorted_secs),
        expected_sections=65,
        sections=sorted_secs
    )
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2, ensure_ascii=False)
        
    pct = (len(sorted_secs) / 65) * 100
    print(f"[✓] National Health Act 2014: {len(sorted_secs):>3} / 65 sections ({pct:.1f}%) -> {output_path.name}")

def parse_fccpa_complete():
    pdf_path = Path("data/raw_pdfs/fccpa-2018.pdf")
    output_path = Path("data/json_laws/fccpa_2018.json")
    
    reader = PdfReader(str(pdf_path))
    pages_text = []
    for p in reader.pages:
        t = p.extract_text() or ""
        t = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', t, flags=re.IGNORECASE)
        t = re.sub(r'A\s+\d+\s+2019\s+No\.\s+\d+', '', t)
        pages_text.append(t)
    raw = "\n".join(pages_text)
    
    pattern = re.compile(
        r'(?:\n|\A)\s*([0-9]{1,3})\s*[\.\-\–]\s*(?:\n\s*)?([^\n\(\)\.\—]{2,120})?(?:\n|\s{2,}|\s*(?=\([0-9a-zA-Z]+\)|[A-Z]))',
        re.MULTILINE
    )
    
    matches = list(pattern.finditer(raw))
    sections_dict = {}
    
    for i, match in enumerate(matches):
        sec_num = match.group(1).strip()
        num_int = int(sec_num)
        if num_int > 168 or num_int == 0:
            continue
            
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        
        raw_title = match.group(2).strip() if (match.lastindex and match.lastindex >= 2 and match.group(2)) else ""
        raw_body = raw[start_pos:end_pos].strip()
        
        clean_body = re.sub(r'\s+', ' ', raw_body).strip()
        clean_title = re.sub(r'\s+', ' ', raw_title).strip() or f"Section {sec_num}"
        
        if len(clean_body) > 10 and sec_num not in sections_dict:
            search_chunk = f"FCCPA 2018 | Section {sec_num}: {clean_title} | {clean_body}"
            sections_dict[sec_num] = SectionModel(
                section_number=sec_num,
                section_title=clean_title,
                full_text=clean_body,
                searchable_chunk=search_chunk
            )
            
    sorted_secs = sorted(sections_dict.values(), key=lambda x: int(x.section_number))
    
    model = StatuteModel(
        statute_id="fccpa_2018",
        statute_title="Federal Competition and Consumer Protection Act 2018",
        short_title="FCCPA 2018",
        year=2018,
        total_sections_found=len(sorted_secs),
        expected_sections=168,
        sections=sorted_secs
    )
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2, ensure_ascii=False)
        
    pct = (len(sorted_secs) / 168) * 100
    print(f"[✓] FCCPA 2018:              {len(sorted_secs):>3} / 168 sections ({pct:.1f}%) -> {output_path.name}")

if __name__ == "__main__":
    parse_health_act_complete()
    parse_fccpa_complete()
