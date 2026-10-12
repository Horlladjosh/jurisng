import json
import re
from pathlib import Path

DATA_PATH = Path("data/json_laws/acja_2015.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

for sec in data["sections"]:
    # 1. Clean Section 300 title
    if sec["section_number"] == "300":
        sec["section_title"] = "Presentation of case for prosecution"
        
    # 2. Clean Section 495 title
    if sec["section_number"] == "495":
        sec["section_title"] = "Citation"
        
    # Strip any accidental leading/trailing punctuation or "Schedule" artifacts in titles
    sec["section_title"] = re.sub(r'\s+Schedule$', '', sec["section_title"], flags=re.IGNORECASE).strip().rstrip('.')

    # Rebuild searchable chunk
    sec["searchable_chunk"] = f"Administration of Criminal Justice Act, 2015 | {sec['part']} | {sec['section_number']}. {sec['section_title']} | {sec['full_text']}"

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("[✓] Cleaned Section 300 and 495 titles.")
