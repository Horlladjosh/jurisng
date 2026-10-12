import re
from pathlib import Path
from pypdf import PdfReader

PDFS = {
    "cfrn_1999": "cfrn_1999.pdf",
    "acja_2015": "acja-2015.pdf",
    "child_rights_act_2003": "child-rights-act.pdf",
    "evidence_act_2011": "evidence-act-2011.pdf",
    "police_act_2020": "police_act_2020.pdf",
    "labour_act": "labour-act.pdf",
    "employee_compensation_act_2010": "employee-compensation-act-2010.pdf",
    "cybercrimes_act_2015": "cybercrimes-act-2015.pdf",
    "land_use_act_1978": "land-use-act.pdf",
    "penal_code_act_1960": "penal-code-northern-states-1960.pdf"
}

raw_dir = Path("data/raw_pdfs")

print("=" * 70)
print("LOCATING EXACT SUBSTANTIVE START PAGES (IGNORING TOC)")
print("=" * 70)

for statute_id, fname in PDFS.items():
    p = raw_dir / fname
    if not p.exists():
        continue
    reader = PdfReader(str(p))
    found_page = None
    
    for idx, page in enumerate(reader.pages):
        txt = page.extract_text() or ""
        # Substantive start indicators in Nigerian statutes
        if re.search(r'ENACTED\s+by\s+the\s+National\s+Assembly|Commencement\s*\.?\s*\[|We\s+the\s+people\s+of\s+the\s+Federal|PART\s+I\s*[-–—]?\s*(?:GENERAL|OBJECTIVES|WAGES|PRELIMINARY|BEST\s+INTERESTS)|THE\s+SCHEDULE\s+FEDERAL\s+PROVISIONS', txt, re.IGNORECASE):
            # Ensure it's not the TOC header mentioning PART I
            if not ("Arrangement of Sections" in txt or "ARRANGEMENT OF SECTIONS" in txt):
                found_page = idx + 1
                break
                
    print(f"• {statute_id:<32} -> Page {found_page or 'Start of File'}")
print("=" * 70)
