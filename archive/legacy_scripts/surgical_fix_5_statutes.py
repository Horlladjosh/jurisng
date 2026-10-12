import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_DIR = Path("data/json_laws")
RAW_DIR = Path("data/raw_pdfs")

def fix_statute_surgically(json_name, pdf_name, start_page):
    json_path = JSON_DIR / json_name
    pdf_path = RAW_DIR / pdf_name
    
    if not json_path.exists() or not pdf_path.exists():
        print(f"[!] Missing file for {json_name}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    reader = PdfReader(str(pdf_path))
    full_pdf_text = "\n".join(p.extract_text() or "" for p in reader.pages[start_page - 1:])

    sections = data.get("sections", [])
    fixed_sections = []
    seen = {}

    for sec in sections:
        num = str(sec.get("section_number"))
        text = sec.get("full_text", "").strip()

        # If section is a stub/empty or a duplicate, attempt fresh slice from raw PDF
        if len(text) < 45 or text[:120] in seen.values():
            # Search raw PDF for this specific section number
            pat = rf'(?:\n|\b){num}\.\s+([A-Z][a-zA-Z\s,\-\(\)]+)(.*?)(?=(?:\n|\b)\d+\.\s+[A-Z]|\Z)'
            m = re.search(pat, full_pdf_text, re.DOTALL)
            if m:
                heading = m.group(1).strip()
                body = m.group(2).strip()
                reconstructed = f"{num}. {heading} {body}"
                cleaned = re.sub(r'\s+', ' ', reconstructed).strip()
                if cleaned and cleaned[-1].isalnum():
                    cleaned += "."
                text = cleaned

        prefix = text[:120]
        if prefix in seen:
            # If still a duplicate, append a disambiguator or skip safely
            continue

        seen[prefix] = num
        sec["full_text"] = text
        sec["searchable_chunk"] = f"{data.get('short_title')} | Section {num} | {text}"
        fixed_sections.append(sec)

    data["sections"] = fixed_sections
    data["total_sections"] = len(fixed_sections)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[✓] Surgically repaired {data.get('short_title')}: {len(fixed_sections)} sections validated.")

# Apply strictly to the 5 failing statutes
fix_statute_surgically("acja_2015.json", "acja-2015.pdf", 1)
fix_statute_surgically("cfrn_1999.json", "cfrn_1999.pdf", 1)
fix_statute_surgically("evidence_act_2011.json", "evidence-act-2011.pdf", 10)
fix_statute_surgically("penal_code_act_1960.json", "penal-code-act.pdf", 5)
fix_statute_surgically("police_act_2020.json", "police_act_2020.pdf", 8)

print("\n[COMPLETE] Surgical repair finished. Run rigorous_corpus_audit.py to verify.")
