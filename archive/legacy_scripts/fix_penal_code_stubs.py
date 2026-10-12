import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_PATH = Path("data/json_laws/penal_code_act_1960.json")
PDF_PATH = Path("data/raw_pdfs/penal-code-act.pdf")

if JSON_PATH.exists() and PDF_PATH.exists():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    reader = PdfReader(str(PDF_PATH))
    full_pdf_text = "\n".join(p.extract_text() or "" for p in reader.pages[4:])
    
    for sec in data.get("sections", []):
        num = str(sec.get("section_number"))
        txt = sec.get("full_text", "").strip()
        if len(txt) < 45:
            # Broadened anchor for Penal Code dash-formatting
            pat = rf'(?:\n|\b){num}\.\s*[\—\-\–]?\s*([A-Z][a-zA-Z\s,\-\(\)]+)(.*?)(?=(?:\n|\b)\d+\.\s*[\—\-\–]?|[A-Z]|\Z)'
            m = re.search(pat, full_pdf_text, re.DOTALL)
            if m:
                heading = m.group(1).strip()
                body = m.group(2).strip()
                reconstructed = f"{num}. {heading} {body}"
                cleaned = re.sub(r'\s+', ' ', reconstructed).strip()
                if cleaned and cleaned[-1].isalnum():
                    cleaned += "."
                sec["full_text"] = cleaned
                sec["searchable_chunk"] = f"Penal Code Act | Section {num} | {cleaned}"

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("[✓] Penal Code Act stubs fully patched.")

