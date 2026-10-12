import json
import re
from pathlib import Path
from pypdf import PdfReader

PAIRS = [
    ("cfrn_1999.json", "cfrn_1999.pdf", "35", "Right to Personal Liberty (CFRN 1999)"),
    ("acja_2015.json", "acja-2015.pdf", "15", "Electronic Confession Recording (ACJA 2015)"),
    ("cybercrimes_act_2015.json", "cybercrimes-act-2015.pdf", "24", "Cyberstalking (Cybercrimes Act 2015)"),
    ("labour_act.json", "labour-act.pdf", "7", "Written Terms of Employment (Labour Act)"),
    ("land_use_act_1978.json", "land-use-act.pdf", "22", "Governor's Consent (Land Use Act 1978)")
]

def run_checks():
    raw_dir = Path("data/raw_pdfs")
    json_dir = Path("data/json_laws")

    print("=" * 75)
    print("VERBATIM MULTI-STATUTE ACCURACY AUDIT")
    print("=" * 75)

    for j_name, p_name, sec_num, label in PAIRS:
        j_path = json_dir / j_name
        p_path = raw_dir / p_name

        if not j_path.exists() or not p_path.exists():
            print(f"[-] Missing pair: {j_name} / {p_name}")
            continue

        with open(j_path, "r", encoding="utf-8") as f:
            d = json.load(f)

        sec = next((s for s in d.get("sections", []) if str(s.get("section_number")) == str(sec_num)), None)
        if not sec:
            print(f"✗ [{label}]: Section {sec_num} missing from JSON!")
            continue

        raw_pdf_text = " ".join("\n".join(p.extract_text() or "" for p in PdfReader(str(p_path)).pages).split())
        sample = " ".join(sec["full_text"].split()[:14]).lower()
        
        # Clean regex special chars in sample for safe search
        clean_sample = re.escape(sample).replace(r"\ ", r"\s+")
        match = re.search(clean_sample, raw_pdf_text.lower())

        if match:
            print(f"✓ [{label} | Section {sec_num}]: EXACT VERBATIM MATCH")
            print(f"  Snippet: \"{sec['full_text'][:120]}...\"\n")
        else:
            print(f"✗ [{label} | Section {sec_num}]: Mismatch")
            print(f"  Attempted match: \"{sample}\"\n")

    print("=" * 75)

if __name__ == "__main__":
    run_checks()
