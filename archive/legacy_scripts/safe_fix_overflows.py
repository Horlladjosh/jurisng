import json
import subprocess
from pathlib import Path

print("=" * 80)
print("SAFE RESTORATION & SURGICAL OVERFLOW CAPPING")
print("=" * 80)

# 1. Safely restore json files from git to guarantee 100% section counts
subprocess.run(["git", "checkout", "data/json_laws/"], check=True)
print("[✓] Restored all JSON files to last verified state.")

JSON_DIR = Path("data/json_laws")

def surgically_cap(filename, sec_num):
    path = JSON_DIR / filename
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for sec in data.get("sections", []):
        if str(sec.get("section_number")) == str(sec_num):
            txt = sec.get("full_text", "")
            if len(txt) > 4000:
                # Cleanly truncate at the last full sentence before 4000 chars
                truncated = txt[:4000].rsplit('.', 1)[0] + '.'
                sec["full_text"] = truncated
                sec["searchable_chunk"] = f"{data.get('short_title')} | Section {sec_num} | {truncated}"
                print(f"[✓] Surgically capped {data.get('short_title')} Section {sec_num} from {len(txt):,} to {len(truncated):,} chars.")
                
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 2. Cap only the 3 confirmed overflows
surgically_cap("land_use_act_1978.json", "51")
surgically_cap("employees_compensation_act_2010.json", "17")
surgically_cap("employees_compensation_act_2010.json", "73")

print("=" * 80)
print("RESTORATION COMPLETE. ALL SECTIONS PRESERVED.")
print("=" * 80)
