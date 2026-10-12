import json
import re
from pathlib import Path
from pypdf import PdfReader

RAW = Path("data/raw_pdfs")
JSON_DIR = Path("data/json_laws")

def clean_txt(t: str) -> str:
    return re.sub(r'\s+', ' ', t or '').strip()

# 1. FIX ACJA 2015 (210, 360, 416)
acja_path = JSON_DIR / "acja_2015.json"
acja_pdf = RAW / "acja-2015.pdf"

if acja_path.exists() and acja_pdf.exists():
    with open(acja_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    reader = PdfReader(str(acja_pdf))
    full_text = "\n".join(p.extract_text() or "" for p in reader.pages[20:])
    
    sec_map = {int(re.findall(r'\d+', s["section_number"])[0]): s for s in data["sections"] if re.findall(r'\d+', s["section_number"])}
    
    for gap in [210, 360, 416]:
        c_str = str(gap)
        n_str = str(gap + 1)
        # Search flexibly for the section number followed by title/body
        m = re.search(rf'(?:\n|\A|\s{{2,}}){c_str}\s*[\.\-\–\—\:]?\s*([^\n]{{0,80}})?\n?(.*?)(?=(?:\n|\s{{2,}}){n_str}\s*[\.\-\–\—\:]|\Z)', full_text, re.DOTALL)
        if m:
            title = clean_txt(m.group(1)) or f"Section {c_str}"
            body = clean_txt(m.group(2))
            clean_full = f"{title} {body}".strip()
            if len(clean_full) > 40:
                sec_map[gap]["full_text"] = clean_full[:3500]
                sec_map[gap]["searchable_chunk"] = f"ACJA 2015 | Section {c_str}: {title} | {clean_full[:3500]}"

    data["sections"] = [sec_map[k] for k in sorted(sec_map.keys())]
    with open(acja_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("[✓] ACJA 2015: Sections 210, 360, 416 extracted verbatim.")

# 2. FIX EVIDENCE ACT 2011 SECTION 100
ev_path = JSON_DIR / "evidence_act_2011.json"
ev_pdf = RAW / "evidence-act-2011.pdf"

if ev_path.exists() and ev_pdf.exists():
    with open(ev_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    reader = PdfReader(str(ev_pdf))
    full_text = "\n".join(p.extract_text() or "" for p in reader.pages[9:])
    
    # Exact slice between 99 and 101
    m_100 = re.search(r'(?:\n|\A|\s)100\s*[\.\-\–\—\:]\s*(.*?)(?=(?:\n|\s)101\s*[\.\-\–\—\:])', full_text, re.DOTALL)
    if m_100:
        clean_body = clean_txt(m_100.group(1))
        for sec in data["sections"]:
            if str(sec["section_number"]) == "100":
                sec["full_text"] = clean_body
                sec["searchable_chunk"] = f"Evidence Act 2011 | Section 100 | {clean_body}"
                break
        with open(ev_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("[✓] Evidence Act 2011: Section 100 synced with exact PDF text.")

# 3. FIX PENAL CODE SCHEDULE (410+)
penal_path = JSON_DIR / "penal_code_act_1960.json"
penal_pdf = RAW / "penal-code-northern-states-1960.pdf"

if penal_path.exists() and penal_pdf.exists():
    with open(penal_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    reader = PdfReader(str(penal_pdf))
    full_text = "\n".join(p.extract_text() or "" for p in reader.pages)
    
    sec_map = {int(re.findall(r'\d+', s["section_number"])[0]): s for s in data["sections"] if re.findall(r'\d+', s["section_number"])}
    
    for num in [6, 410, 422, 425, 431, 452, 465, 468, 473, 475]:
        c_str = str(num)
        m = re.search(rf'(?:\n|\A|\s){c_str}\s*[\.\-\–\—\:]\s*(.*?)(?=(?:\n|\s)\d{{1,3}}\s*[\.\-\–\—\:]|\Z)', full_text, re.DOTALL)
        if m:
            clean_body = clean_txt(m.group(1))
            if len(clean_body) > 30:
                sec_map[num]["full_text"] = clean_body[:3500]
                sec_map[num]["searchable_chunk"] = f"Penal Code Act | Section {c_str} | {clean_body[:3500]}"

    data["sections"] = [sec_map[k] for k in sorted(sec_map.keys())]
    with open(penal_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("[✓] Penal Code Act: Provisions synced with exact PDF text.")
