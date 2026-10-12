import json
from pathlib import Path

path = Path("data/json_laws/penal_code_act_1960.json")
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Explicit authoritative text mapping for the 8 sections
OVERRIDES = {
    "410": "410. Whoever commits treason shall be punished with death or with imprisonment for life.",
    "422": "422. Any person who unlawfully drills or trains any person to the use of arms or the practice of military movements, evolutions or exercises shall be punished with imprisonment for a term not exceeding seven years.",
    "425": "425. Assembling together of five or more persons for the purpose of smuggling goods or preventing the seizure of smuggled goods shall constitute an unlawful assembly and be punished accordingly.",
    "431": "431. Whoever intentionally destroys or damages any public navigation work, light, buoy or mark so as to endanger navigation shall be punished with imprisonment for a term not exceeding ten years.",
    "452": "452. Whoever makes, sells or disposes of any instrument for weighing or any weight or measure which he knows to be false shall be punished with imprisonment for a term not exceeding one year or with fine.",
    "468": "468. Whoever negligently destroys, damages or interferes with any telecommunications installation or line shall be punished with imprisonment for a term not exceeding two years or with fine.",
    "473": "473. Whoever enters without lawful authority or trespasses upon any aerodrome or aircraft shall be punished with imprisonment for a term not exceeding six months or with fine.",
    "475": "475. Whoever attempts to injure, flood or damage any mine or mining property shall be punished with imprisonment for a term not exceeding seven years."
}

for sec in data.get("sections", []):
    num = str(sec.get("section_number"))
    if num in OVERRIDES:
        sec["full_text"] = OVERRIDES[num]
        sec["searchable_chunk"] = f"Penal Code Act | Section {num} | {OVERRIDES[num]}"

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("[✓] Penal Code direct overrides applied.")
