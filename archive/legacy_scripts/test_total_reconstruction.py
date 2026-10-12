import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_PATH = Path("data/json_laws/acja_2015.json")
PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Combine preamble + all 495 sections
preamble = data.get("preamble_raw", "")
sections_text = " ".join(s["full_text"] for s in data["sections"])
json_full_combined = f"{preamble} {sections_text}".strip()
json_norm = re.sub(r'\s+', ' ', json_full_combined).strip()

# Extract substantive text from the PDF (page 21 up to FIRST SCHEDULE)
reader = PdfReader(str(PDF_PATH))
pdf_raw = "\n".join(reader.pages[i].extract_text() or "" for i in range(20, len(reader.pages)))
pdf_raw = pdf_raw.replace('\xa0', ' ')

sched_match = re.search(r'\n\s*FIRST\s+SCHEDULE\b', pdf_raw)
if sched_match:
    pdf_substantive = pdf_raw[:sched_match.start()]
else:
    pdf_substantive = pdf_raw

pdf_norm = re.sub(r'\s+', ' ', pdf_substantive).strip()

print("=" * 80)
print("TOTAL RECONSTRUCTION & VERBATIM MATCH AUDIT (ACJA 2015)")
print("=" * 80)
print(f"Total Normalized PDF Characters:  {len(pdf_norm):,}")
print(f"Total Normalized JSON Characters: {len(json_norm):,}")
print(f"Difference:                       {abs(len(pdf_norm) - len(json_norm))} chars")

if json_norm == pdf_norm:
    print("\n[✓] 100% PERFECT VERBATIM MATCH: Every character from the long title to Section 495 matches the PDF exactly.")
else:
    if json_norm in pdf_norm:
        print("\n[✓] JSON is a clean contiguous subset of the substantive PDF text.")
    else:
        print("\n[!] Discrepancy detected between JSON and PDF text.")

print("=" * 80)
