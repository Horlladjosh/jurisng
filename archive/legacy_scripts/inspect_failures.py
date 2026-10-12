import json
from pathlib import Path

JSON_DIR = Path("data/json_laws")

def inspect():
    for j_file in JSON_DIR.glob("*.json"):
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for sec in data.get("sections", []):
            if len(sec.get("full_text", "").strip()) < 45:
                print(f"[{data.get('short_title')}] Section {sec.get('section_number')}: {repr(sec.get('full_text'))}")

inspect()
