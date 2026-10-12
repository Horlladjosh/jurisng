import json
import re
from pathlib import Path
from pypdf import PdfReader

PDF_PATH = Path("data/raw_pdfs/fccpa-2018.pdf")
JSON_PATH = Path("data/json_laws/fccpa_2018.json")

reader = PdfReader(str(PDF_PATH))
full_text = "\n".join(p.extract_text() or "" for p in reader.pages[8:])

sections = []
# FCCPA has 168 sections
for i in range(1, 169):
    # Match pattern like "1. " or "23. " followed by Capital letters
    pattern = rf'(?:\n|\b){i}\.\s+([A-Z][a-zA-Z\s,\-\(\)]+)(?:\n|$)'
    m = list(re.finditer(pattern, full_text))
    
    if not m:
        continue
    
    # Take the instance that corresponds to the section header
    start_idx = m[0].start()
    
    # Find next section start
    next_pattern = rf'(?:\n|\b){i+1}\.\s+[A-Z]'
    nm = re.search(next_pattern, full_text[start_idx + len(m[0].group(0)):])
    
    if nm:
        end_idx = start_idx + len(m[0].group(0)) + nm.start()
        sec_text = full_text[start_idx:end_idx].strip()
    else:
        sec_text = full_text[start_idx:start_idx + 3000].strip()

    cleaned = re.sub(r'\s+', ' ', sec_text)
    if cleaned and cleaned[-1].isalnum():
        cleaned += "."

    sections.append({
        "section_number": str(i),
        "section_title": f"Section {i}",
        "full_text": cleaned,
        "searchable_chunk": f"FCCPA 2018 | Section {i} | {cleaned}"
    })

payload = {
    "statute_title": "Federal Competition and Consumer Protection Act, 2018",
    "short_title": "FCCPA 2018",
    "jurisdiction": "Nigeria",
    "total_sections": len(sections),
    "sections": sections
}

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)

print(f"[✓] FCCPA 2018 re-parsed successfully: {len(sections)} sections extracted.")
