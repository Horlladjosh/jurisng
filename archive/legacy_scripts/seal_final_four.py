import json
import re
from pathlib import Path
from pypdf import PdfReader

RAW = Path("data/raw_pdfs")
JSON_DIR = Path("data/json_laws")

def clean_txt(t: str) -> str:
    return re.sub(r'\s+', ' ', t or '').strip()

# 1. EXACT PDF SYNC FOR EVIDENCE ACT SECTION 100
ev_path = JSON_DIR / "evidence_act_2011.json"
ev_pdf = RAW / "evidence-act-2011.pdf"
if ev_path.exists() and ev_pdf.exists():
    with open(ev_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    reader = PdfReader(str(ev_pdf))
    full_pdf = "\n".join(p.extract_text() or "" for p in reader.pages[9:])
    
    # Locate verbatim Section 100
    m = re.search(r'(?:100\b|Evidence\s+of\s+terms).*?(?=(?:\n|\s{2,})101\b)', full_pdf, re.DOTALL | re.IGNORECASE)
    if m:
        raw_slice = clean_txt(m.group(0))
        for sec in data["sections"]:
            if str(sec["section_number"]) == "100":
                sec["full_text"] = raw_slice
                sec["searchable_chunk"] = f"Evidence Act 2011 | Section 100 | {raw_slice}"
                break
        with open(ev_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("[✓] Evidence Act 2011: Section 100 synced.")

# 2. EXACT PDF SYNC FOR PENAL CODE (410, 465, 477)
penal_path = JSON_DIR / "penal_code_act_1960.json"
penal_pdf = RAW / "penal-code-northern-states-1960.pdf"
if penal_path.exists() and penal_pdf.exists():
    with open(penal_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    reader = PdfReader(str(penal_pdf))
    full_pdf = "\n".join(p.extract_text() or "" for p in reader.pages)
    
    sec_map = {int(re.findall(r'\d+', s["section_number"])[0]): s for s in data["sections"] if re.findall(r'\d+', s["section_number"])}
    
    for sec_num in [410, 465, 477]:
        m = re.search(rf'(?:\n|\A|\s){sec_num}\b[\.\-\–\—\:]?\s*([^\n]{{0,80}})?\n?(.*?)(?=(?:\n|\s)\d{{1,3}}\b|\Z)', full_pdf, re.DOTALL)
        if m:
            raw_slice = clean_txt(f"{m.group(1) or ''} {m.group(2)}".strip())
            if len(raw_slice) > 25 and sec_num in sec_map:
                sec_map[sec_num]["full_text"] = raw_slice[:3500]
                sec_map[sec_num]["searchable_chunk"] = f"Penal Code Act | Section {sec_num} | {raw_slice[:3500]}"
                
    data["sections"] = [sec_map[k] for k in sorted(sec_map.keys())]
    with open(penal_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("[✓] Penal Code Act: Sections 410, 465, 477 synced.")
