import json
import re
from pathlib import Path

JSON_PATH = Path("data/json_laws/acja_2015.json")

if not JSON_PATH.exists():
    print(f"[!] {JSON_PATH} not found.")
    exit(1)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned_sections = []
current_part = "PART 1 – PRELIMINARY"

for sec in data["sections"]:
    text = sec["full_text"]

    # 1. Detect and assign Part headers across sections
    part_match = re.search(r'\n\s*(PART\s+[0-9IVXLCDM]+\s*[-–—][^\n]+)', text, re.IGNORECASE)
    sec["part"] = current_part
    
    if part_match:
        current_part = part_match.group(1).strip()
        # Remove the trailing PART header from this section's text
        text = text[:part_match.start()].strip()

    # 2. Strip multi-line gazette marginal notes (isolated short phrase blocks)
    text = re.sub(r'(?:\n\s*[A-Z][a-z0-9\s\(\)\-–—,]+\.?\s*){1,4}(?=\n)', '\n', text)
    
    # 3. Clean up whitespace and paragraph breaks
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()

    sec["full_text"] = text
    sec["searchable_chunk"] = f"{data['short_title']} | {sec.get('part', '')} | {sec['section_title']} | {text}"
    cleaned_sections.append(sec)

data["sections"] = cleaned_sections

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("=" * 80)
print(f"[✓] Successfully cleaned all {len(cleaned_sections)} sections of ACJA 2015.")
print("=" * 80)
