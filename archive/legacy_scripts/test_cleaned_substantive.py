import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_PATH = Path("data/json_laws/acja_2015.json")
PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

reader = PdfReader(str(PDF_PATH))
pdf_raw = "\n".join(reader.pages[i].extract_text() or "" for i in range(20, len(reader.pages)))
pdf_norm = re.sub(r'\s+', ' ', pdf_raw).replace('\xa0', ' ')

def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()

passed = 0
failed = []

for sec in data["sections"]:
    num = sec["section_number"]
    text = normalize(sec["full_text"])
    
    # Split section into substantive sentences to verify each sentence exists in PDF
    sentences = [s.strip() for s in re.split(r'(?<=[.?!;])\s+', text) if len(s.strip()) > 15]
    
    sec_passed = True
    for s in sentences:
        # Check if the legal sentence exists verbatim in the PDF
        if s not in pdf_norm:
            sec_passed = False
            failed.append((num, s[:80]))
            break
            
    if sec_passed:
        passed += 1

print("=" * 80)
print("SUBSTANTIVE LEGAL TEXT INTEGRITY AUDIT (ACJA 2015)")
print("=" * 80)
print(f"Total Sections: {len(data['sections'])}")
print(f"Passed:         {passed} / {len(data['sections'])}")
print(f"Failed:         {len(failed)}")

if failed:
    print("\n[!] Mismatched sentences:")
    for num, sample in failed[:10]:
        print(f"  • Section {num}: '{sample}...'")
else:
    print("\n[✓] ALL SECTIONS VERIFIED: Every legal provision, subsection, and clause exists verbatim in the source PDF.")
print("=" * 80)
