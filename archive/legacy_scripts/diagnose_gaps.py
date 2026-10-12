import json
from pathlib import Path

TARGETS = [
    ("evidence_act_2011.json", 259, "Evidence Act 2011"),
    ("police_act_2020.json", 142, "Police Act 2020"),
    ("labour_act.json", 92, "Labour Act")
]

base = Path("data/json_laws")
for fname, total, title in TARGETS:
    fpath = base / fname
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    found_nums = set()
    for s in data["sections"]:
        try:
            found_nums.add(int(s["section_number"]))
        except:
            pass
    missing = [i for i in range(1, total + 1) if i not in found_nums]
    print(f"\n{title} (Missing {len(missing)} sections):")
    print(f"Missing Numbers: {missing}")
