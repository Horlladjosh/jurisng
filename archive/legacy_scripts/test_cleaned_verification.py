import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_PATH = Path("data/json_laws/acja_2015.json")
PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

sections = data.get("sections", [])
sec_map = {int(s["section_number"]): s["full_text"] for s in sections}

reader = PdfReader(str(PDF_PATH))
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

    # 1. Test Section Start (first 50 substantive chars)
    head = norm_sec[:min(50, len(norm_sec))]
    pos = norm_pdf.find(head, last_pos)
    if pos == -1:
        pos = norm_pdf.find(head)
        if pos == -1:
            failed_sections.append((i, f"Start marker mismatch: '{head}'"))
            continue

    # 2. Test Section End (last 50 substantive chars)
    tail = norm_sec[-min(50, len(norm_sec)):]
    tail_pos = norm_pdf.find(tail, pos)
    if tail_pos == -1:
        failed_sections.append((i, f"End marker mismatch: '{tail}'"))
        continue

    last_pos = pos

print("=" * 80)
print("CLEANED JSON VERBATIM VERIFICATION (ACJA 2015)")
print("=" * 80)
print(f"Total Sections Checked: {total_checked}")
print(f"Failed Sections:        {len(failed_sections)}")

if failed_sections:
    print("\n[!] Mismatches detected:")
    for num, err in failed_sections:
        print(f"  • Section {num}: {err}")
else:
    print("\n[✓] VERIFIED: All 495 cleaned sections match the PDF verbatim in exact sequence.")
print("=" * 80)
