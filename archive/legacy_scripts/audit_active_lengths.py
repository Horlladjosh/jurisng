import json
from pathlib import Path

JSON_DIR = Path("data/json_laws")

print("=" * 80)
print("ACTIVE CORPUS LENGTH AUDIT (> 5,000 CHARS)")
print("=" * 80)

anomalies = 0
for j_file in sorted(JSON_DIR.glob("*.json")):
    with open(j_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    sections = data.get("sections", [])
    if not sections:
        continue  # Skip empty statutes
        
    title = data.get("short_title", j_file.stem)
    for sec in sections:
        txt = sec.get("full_text", "")
        if len(txt) > 5000:
            anomalies += 1
            print(f"[!] {title} Section {sec.get('section_number')}: {len(txt):,} chars")

if anomalies == 0:
    print("[✓] All active statutes verified. Zero abnormal text lengths.")
else:
    print(f"[!] Found {anomalies} anomalous sections.")
print("=" * 80)
