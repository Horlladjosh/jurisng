import json

with open("data/json_laws/cybercrimes_act_2015.json", "r", encoding="utf-8") as f:
    data = json.load(f)

sections = {int(s["section_number"]): s for s in data["sections"]}

for sec_num in [5, 14, 24, 44, 58, 59]:
    sec = sections.get(sec_num)
    if sec:
        print(f"=== Section {sec_num}: {sec['section_title']} ===")
        print(f"Text Preview: {repr(sec['full_text'][:150])}\n")
