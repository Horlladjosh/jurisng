import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_PATH = Path("data/json_laws/acja_2015.json")
PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")

if not JSON_PATH.exists() or not PDF_PATH.exists():
    print("[!] Missing JSON or PDF file.")
    exit(1)

# 1. Load existing parsed sections
with open(JSON_PATH, "r", encoding="utf-8") as f:
    current_data = json.load(f)

# 2. Extract preamble text from page 21 before Section 1
reader = PdfReader(str(PDF_PATH))
p21_text = (reader.pages[20].extract_text() or "").replace('\xa0', ' ')

# Locate the start of Section 1
sec1_match = re.search(r'(?:\n|^)\s*1\.\s*(?:\([0-9a-zA-Z]+\)|[A-Z])', p21_text)
preamble_text = p21_text[:sec1_match.start()].strip() if sec1_match else ""

# Structure the full metadata payload
updated_payload = {
    "statute_id": "acja_2015",
    "statute_title": "Administration of Criminal Justice Act, 2015",
    "short_title": "ACJA 2015",
    "year": "2015",
    "commencement_date": "26th May 2015",
    "long_title": "An Act to provide for the administration of criminal justice in the courts of the Federal Capital Territory and other federal courts in Nigeria; and for related matters.",
    "enactment_clause": "ENACTED by the National Assembly of the Federal Republic of Nigeria:",
    "preamble_raw": re.sub(r'\s+', ' ', preamble_text).strip(),
    "total_sections": len(current_data.get("sections", [])),
    "sections": current_data.get("sections", [])
}

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(updated_payload, f, indent=2, ensure_ascii=False)

print("=" * 80)
print(f"[✓] Successfully updated {JSON_PATH.name}")
print(f"    Total Sections: {updated_payload['total_sections']}")
print(f"    Commencement:   {updated_payload['commencement_date']}")
print(f"    Long Title:     {updated_payload['long_title'][:70]}...")
print("=" * 80)
