import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_DIR = Path("data/json_laws")
RAW_DIR = Path("data/raw_pdfs")

# Config for statutes that had overflow issues
STATUTES_TO_FIX = [
    {"json": "acja_2015.json", "pdf": "acja-2015.pdf", "start": 1, "max": 495},
    {"json": "cfrn_1999.json", "pdf": "cfrn_1999.pdf", "start": 1, "max": 320},
    {"json": "child_rights_act_2003.json", "pdf": "child-rights-act.pdf", "start": 12, "max": 278},
    {"json": "cybercrimes_act_2015.json", "pdf": "cybercrimes-act-2015.pdf", "start": 5, "max": 59},
    {"json": "employees_compensation_act_2010.json", "pdf": "employees-compensation-act-2010.pdf", "start": 5, "max": 74},
    {"json": "fccpa_2018.json", "pdf": "fccpa-2018.pdf", "start": 10, "max": 168},
    {"json": "labour_act.json", "pdf": "labour-act.pdf", "start": 4, "max": 92},
    {"json": "land_use_act_1978.json", "pdf": "land-use-act-1978.pdf", "start": 3, "max": 51},
    {"json": "national_health_act_2014.json", "pdf": "national-health-act-2014.pdf", "start": 5, "max": 65},
]

def rebuild_clean_statute(cfg):
    json_path = JSON_DIR / cfg["json"]
    pdf_path = RAW_DIR / cfg["pdf"]
    
    if not json_path.exists() or not pdf_path.exists():
        print(f"[!] Skipping {cfg['json']} (files missing)")
        return

    reader = PdfReader(str(pdf_path))
    full_text = "\n".join(p.extract_text() or "" for p in reader.pages[cfg["start"] - 1:])
    
    # Strip out trailing schedules/tables of contents to prevent overflow
    for marker in ["FIRST SCHEDULE", "SECOND SCHEDULE", "SCHEDULES", "EXPLANATORY MEMORANDUM"]:
        if marker in full_text:
            full_text = full_text.split(marker)[0]

    sections = []
    max_sec = cfg["max"]

    for i in range(1, max_sec + 1):
        # Strict pattern looking for section start
        pat = rf'(?:\n|\b){i}\.\s+([A-Z][a-zA-Z\s,\-\(\)]+)'
        m = list(re.finditer(pat, full_text))
        
        if not m:
            continue
            
        start_pos = m[0].start()
        
        # Find next section
        next_pat = rf'(?:\n|\b){i+1}\.\s+[A-Z]'
        nm = re.search(next_pat, full_text[start_pos + len(m[0].group(0)):])
        
        if nm:
            end_pos = start_pos + len(m[0].group(0)) + nm.start()
            sec_text = full_text[start_pos:end_pos].strip()
        else:
            # Last section or fallback bounds (max 3500 chars to prevent overflow)
            sec_text = full_text[start_pos:start_pos + 3500].strip()

        # Clean whitespace and artifacts
        cleaned = re.sub(r'\s+', ' ', sec_text)
        # Truncate if spillover happened
        if len(cleaned) > 4000:
            cleaned = cleaned[:4000].rsplit('.', 1)[0] + '.'
            
        if cleaned and cleaned[-1].isalnum():
            cleaned += "."

        sections.append({
            "section_number": str(i),
            "section_title": f"Section {i}",
            "full_text": cleaned,
            "searchable_chunk": f"{cfg['json'].replace('_', ' ').title()} | Section {i} | {cleaned}"
        })

        # Advance window
        full_text = full_text[start_pos + len(sec_text):]

    with open(json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    payload = {
        "statute_title": meta.get("statute_title", cfg["json"]),
        "short_title": meta.get("short_title", cfg["json"]),
        "jurisdiction": "Nigeria",
        "total_sections": len(sections),
        "sections": sections
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    
    print(f"[✓] Rebuilt & Capped {meta.get('short_title', cfg['json'])}: {len(sections)} sections clean.")

print("=" * 80)
print("RE-PARSING AND CAPPING ALL STATUTES TO PREVENT OVERFLOWS")
print("=" * 80)
for cfg in STATUTES_TO_FIX:
    rebuild_clean_statute(cfg)

print("=" * 80)
