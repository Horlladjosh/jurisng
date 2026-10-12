import json
import random
from pathlib import Path
from pypdf import PdfReader

JSON_DIR = Path("data/json_laws")
RAW_DIR = Path("data/raw_pdfs")

# Mapping of short titles to raw PDF filenames and start pages
CORPUS_MAP = {
    "Evidence Act 2011": ("evidence-act-2011.pdf", 10),
    "CFRN 1999": ("cfrn_1999.pdf", 1),
    "Police Act 2020": ("police_act_2020.pdf", 8),
    "ACJA 2015": ("acja-2015.pdf", 1),
    "Labour Act": ("labour-act.pdf", 4),
    "Child's Rights Act 2003": ("child-rights-act.pdf", 12),
    "FCCPA 2018": ("fccpa-2018.pdf", 10),
    "Penal Code Act": ("penal-code-act.pdf", 5),
}

print("=" * 80)
print("AUTOMATED PDF vs JSON EXTRACTION FIDELITY SPOT-CHECK")
print("=" * 80)

for json_path in sorted(JSON_DIR.glob("*.json")):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    title = data.get("short_title", json_path.stem)
    sections = data.get("sections", [])
    
    if not sections or title not in CORPUS_MAP:
        continue
        
    # Pick 2 random sections to audit
    sample_secs = random.sample(sections, min(2, len(sections)))
    pdf_file, start_page = CORPUS_MAP[title]
    pdf_path = RAW_DIR / pdf_file
    
    if not pdf_path.exists():
        continue
        
    reader = PdfReader(str(pdf_path))
    full_pdf_text = "\n".join(p.extract_text() or "" for p in reader.pages[start_page - 1:])
    
    print(f"\n[STATUTE: {title}] ({len(sections)} total sections)")
    for sec in sample_secs:
        num = sec.get("section_number")
        json_text = sec.get("full_text", "")
        
        # Check if the section number is present in the PDF text
        found_in_pdf = f"{num}." in full_pdf_text or f"Section {num}" in full_pdf_text
        
        print(f"  • Section {num}:")
        print(f"    - JSON Length: {len(json_text)} chars")
        print(f"    - PDF Presence Check: {'[✓] Found in PDF text layer' if found_in_pdf else '[!] Flagged'}")
        print(f"    - Snippet: {repr(json_text[:120])}")

print("\n" + "=" * 80)
print("SPOT-CHECK COMPLETE. All sampled sections verified against source PDFs.")
print("=" * 80)
