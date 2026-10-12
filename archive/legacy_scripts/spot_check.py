import sys
import json
from pathlib import Path

def inspect_section(json_filename, section_number):
    path = Path("data/json_laws") / json_filename
    if not path.exists():
        print(f"File not found: {path}")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sec = next((s for s in data.get("sections", []) if str(s.get("section_number")) == str(section_number)), None)
    if not sec:
        print(f"Section {section_number} not found in {json_filename}.")
        return
    
    print("=" * 70)
    print(f"STATUTE: {data.get('statute_title', json_filename)}")
    print(f"SECTION: {sec['section_number']} — {sec.get('section_title', '')}")
    print(f"LENGTH : {len(sec['full_text'])} characters")
    print("-" * 70)
    print(sec["full_text"])
    print("=" * 70)

if __name__ == "__main__":
    statute = sys.argv[1] if len(sys.argv) > 1 else "evidence_act_2011.json"
    sec_num = sys.argv[2] if len(sys.argv) > 2 else "84"
    inspect_section(statute, sec_num)
