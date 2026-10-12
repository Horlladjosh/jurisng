import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_PATH = Path("data/json_laws/acja_2015.json")
PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")

print("=" * 80)
print("COMPREHENSIVE INTEGRITY & MISMATCH AUDIT: ACJA 2015 (SECTIONS 1-494)")
print("=" * 80)

if not JSON_PATH.exists() or not PDF_PATH.exists():
    print("[!] Missing JSON or PDF file.")
    exit(1)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

json_sections = data.get("sections", [])
sec_map = {int(s["section_number"]): s["full_text"] for s in json_sections}

reader = PdfReader(str(PDF_PATH))
# Substantive text from page 21 onward
pdf_pages_text = [reader.pages[i].extract_text() or "" for i in range(20, len(reader.pages))]
raw_pdf_text = "\n".join(pdf_pages_text)

# Clean whitespace for comparison
def normalize(txt):
    return re.sub(r'\s+', ' ', txt).strip()

norm_pdf = normalize(raw_pdf_text)

mismatches = []
empty_sections = []
short_sections = []
missing_in_json = []

last_found_pos = 0

for i in range(1, 495):
    if i not in sec_map:
        missing_in_json.append(i)
        continue

    sec_text = sec_map[i]
    norm_sec = normalize(sec_text)

    if len(norm_sec) == 0:
        empty_sections.append(i)
        continue

    if len(norm_sec) < 40:
        short_sections.append((i, norm_sec))

    # Check if this section's normalized text exists verbatim in the PDF
    # We take the first 80 chars and last 80 chars to test exact boundary matching
    head = norm_sec[:min(80, len(norm_sec))]
    tail = norm_sec[-min(80, len(norm_sec)):]

    head_pos = norm_pdf.find(head, last_found_pos)
    if head_pos == -1:
        # Fallback search anywhere in PDF
        head_pos = norm_pdf.find(head)
        if head_pos == -1:
            mismatches.append((i, "Header string not found in PDF", head))
        else:
            mismatches.append((i, "Out of order sequence in PDF", head))
    else:
        last_found_pos = head_pos

print(f"Total sections checked: 494")
print(f"Missing from JSON: {len(missing_in_json)} -> {missing_in_json}")
print(f"Empty sections: {len(empty_sections)} -> {empty_sections}")
print(f"Potential text/boundary mismatches: {len(mismatches)}")
if mismatches:
    for m in mismatches[:10]:
        print(f"  • Section {m[0]}: {m[1]} -> '{m[2]}'")

print(f"\nVery short sections (<40 chars): {len(short_sections)}")
for s in short_sections[:5]:
    print(f"  • Section {s[0]}: \"{s[1]}\"")

print("=" * 80)
