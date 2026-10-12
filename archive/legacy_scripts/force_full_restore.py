import json
from pathlib import Path

# Let's check what JSON files exist and their section counts before indexing
JSON_DIR = Path("data/json_laws")

print("=" * 80)
print("INSPECTING LOCAL JSON SECTION COUNTS")
print("=" * 80)

total_sections = 0
for f in sorted(JSON_DIR.glob("*.json")):
    with open(f, "r", encoding="utf-8") as file:
        data = json.load(file)
        count = len(data.get("sections", []))
        total_sections += count
        print(f"  • {data.get('short_title', f.stem)}: {count} sections")

print(f"\nTotal sections across all files on disk: {total_sections}")
print("=" * 80)
