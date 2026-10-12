import json
from pathlib import Path

json_dir = Path("data/json_laws")
json_files = sorted(list(json_dir.glob("*.json")))

print("=" * 85)
print(f"COMPLETENESS & GAP AUDIT ({len(json_files)} INGESTED STATUTES)")
print("=" * 85)

for jf in json_files:
    with open(jf, "r", encoding="utf-8") as f:
        data = json.load(f)

    short_title = data.get("short_title", jf.stem)
    sections = data.get("sections", [])

    if not sections:
        print(f"\n❌ EMPTY: {short_title} ({jf.name}) -> 0 sections found!")
        continue

    numeric_secs = []
    non_numeric = []
    for s in sections:
        raw_num = s.get("section_number", "").strip().rstrip(".")
        if raw_num.isdigit():
            numeric_secs.append(int(raw_num))
        else:
            non_numeric.append(raw_num)

    numeric_secs = sorted(list(set(numeric_secs)))
    min_sec = numeric_secs[0] if numeric_secs else 0
    max_sec = numeric_secs[-1] if numeric_secs else 0
    total_parsed = len(sections)

    expected_range = set(range(min_sec, max_sec + 1))
    missing_numbers = sorted(list(expected_range - set(numeric_secs)))

    is_complete = (len(missing_numbers) == 0) and (min_sec in (1, 0))
    status = "✅ COMPLETE" if is_complete else "⚠️ CHECK GAPS"

    print(f"\n{status} | {short_title}")
    print(f"   • File: {jf.name}")
    print(f"   • Range: Section {min_sec} to {max_sec} (Total parsed: {total_parsed})")

    if missing_numbers:
        preview = missing_numbers[:10]
        more = "..." if len(missing_numbers) > 10 else ""
        print(f"   • Missing Section Numbers ({len(missing_numbers)} missing): {preview}{more}")
    if non_numeric:
        print(f"   • Non-numeric Sections: {non_numeric}")

print("\n" + "=" * 85)
