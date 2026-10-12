import json
from pathlib import Path

DATA_PATH = Path("data/json_laws/acja_2015.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

sections = data.get("sections", [])
print("=" * 80)
print(f"ACT INTEGRITY AUDIT: {data.get('short_title')}")
print("=" * 80)
print(f"Total Sections in JSON: {len(sections)} / 495")

# 1. Check sequence integrity
missing_nums = []
for i in range(1, 496):
    if not any(int(s["section_number"]) == i for s in sections):
        missing_nums.append(i)

if missing_nums:
    print(f"[!] Warning: Missing section numbers: {missing_nums}")
else:
    print("[✓] Sequence Check: Perfect (1 to 495 contiguous)")

# 2. Inspect key benchmark sections
benchmarks = [1, 6, 17, 39, 306, 495]
print("\n" + "=" * 80)
print("BENCHMARK SAMPLE INSPECTION")
print("=" * 80)

for sec in sections:
    num = int(sec["section_number"])
    if num in benchmarks:
        print(f"\n--- SECTION {num}: {sec['section_title']} ({sec['part']}) ---")
        lines = sec["full_text"].split("\n")
        preview = "\n".join(lines[:4])
        print(preview)
        if len(lines) > 4:
            print(f"... [{len(lines) - 4} more lines] ...")

print("=" * 80)
