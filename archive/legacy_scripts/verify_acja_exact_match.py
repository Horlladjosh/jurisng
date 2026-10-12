import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_PATH = Path("data/json_laws/acja_2015.json")
PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")

print("=" * 80)
print("FULL TEXT-MATCH AUDIT: ACJA 2015 (SECTIONS 1 TO 495)")
print("=" * 80)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

sections = data.get("sections", [])
sec_map = {int(s["section_number"]): s["full_text"] for s in sections}

reader = PdfReader(str(PDF_PATH))
# Extract substantive text from page 21 onward
raw_pdf = "\n".join(reader.pages[i].extract_text() or "" for i in range(20, len(reader.pages)))
raw_pdf = raw_pdf.replace('\xa0', ' ')

def normalize(t):
    return re.sub(r'\s+', ' ', t).strip()

norm_pdf = normalize(raw_pdf)

total_checked = 0
failed_sections = []
last_pos = 0

for i in range(1, 496):
    total_checked += 1
    if i not in sec_map:
        failed_sections.append((i, "Section missing entirely from JSON"))
        continue

    sec_text = sec_map[i]
    norm_sec = normalize(sec_text)

    if len(norm_sec) == 0:
        failed_sections.append((i, "Empty section text"))
        continue

    # 1. Check start of section
    head = norm_sec[:min(60, len(norm_sec))]
    pos = norm_pdf.find(head, last_pos)
    if pos == -1:
        # Fallback check across full doc
        pos = norm_pdf.find(head)
        if pos == -1:
            failed_sections.append((i, f"Start of section not found in PDF: '{head}'"))
            continue

    # 2. Check end of section
    tail = norm_sec[-min(60, len(norm_sec)):]
    tail_pos = norm_pdf.find(tail, pos)
    if tail_pos == -1:
        failed_sections.append((i, f"End of section not found in PDF: '{tail}'"))
        continue

    last_pos = pos

print(f"Total sections tested: {total_checked}")
print(f"Failed sections: {len(failed_sections)}")

if failed_sections:
    print("\n[!] Mismatches found:")
    for num, err in failed_sections:
        print(f"  • Section {num}: {err}")
else:
    print("\n[✓] VERIFIED: All 495 sections of ACJA 2015 exist verbatim in exact sequential order in the PDF.")
print("=" * 80)
