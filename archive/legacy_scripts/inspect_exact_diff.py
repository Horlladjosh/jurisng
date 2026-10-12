import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_PATH = Path("data/json_laws/acja_2015.json")
PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

json_combined = " ".join(s["full_text"] for s in data["sections"])
json_norm = re.sub(r'\s+', ' ', json_combined).strip()

reader = PdfReader(str(PDF_PATH))
pdf_raw = "\n".join(reader.pages[i].extract_text() or "" for i in range(20, len(reader.pages)))
pdf_raw = pdf_raw.replace('\xa0', ' ')

sched_match = re.search(r'\n\s*FIRST\s+SCHEDULE\b', pdf_raw)
if sched_match:
    pdf_substantive = pdf_raw[:sched_match.start()]
else:
    pdf_substantive = pdf_raw

pdf_norm = re.sub(r'\s+', ' ', pdf_substantive).strip()

start_pos = pdf_norm.find(json_norm)

print("=" * 80)
print("EXACT DIFFERENCE BREAKDOWN")
print("=" * 80)

if start_pos != -1:
    prefix = pdf_norm[:start_pos].strip()
    end_pos = start_pos + len(json_norm)
    suffix = pdf_norm[end_pos:].strip()
    
    print(f"1. Leading Text before Section 1 ({len(prefix)} chars):")
    print(f"   {repr(prefix)}\n")
    
    print(f"2. Trailing Text after Section 495 ({len(suffix)} chars):")
    print(f"   {repr(suffix)}\n")
else:
    print("[!] JSON string could not be located contiguously.")

print("=" * 80)
