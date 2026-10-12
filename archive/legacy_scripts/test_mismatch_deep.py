import json
import re
from pathlib import Path

DATA_PATH = Path("data/json_laws/acja_2015.json")

if not DATA_PATH.exists():
    print(f"[!] File not found: {DATA_PATH}")
    exit(1)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

sections = data.get("sections", [])
total_expected = 495

print("=" * 80)
print(f"DEEP MISMATCH & INTEGRITY AUDIT: {data.get('short_title', 'ACJA 2015')}")
print("=" * 80)

issues_found = 0

# 1. Total Count & Duplicate Check
section_numbers = [int(s["section_number"]) for s in sections]
print(f"1. Total Count Check: {len(sections)} / {total_expected} sections parsed.")

duplicates = [num for num in set(section_numbers) if section_numbers.count(num) > 1]
if duplicates:
    print(f"   [!] DUPLICATE SECTIONS FOUND: {duplicates}")
    issues_found += len(duplicates)
else:
    print("   [✓] No duplicate section numbers.")

# 2. Missing Sequence Check
missing = [i for i in range(1, total_expected + 1) if i not in section_numbers]
if missing:
    print(f"   [!] MISSING SECTIONS: {missing}")
    issues_found += len(missing)
else:
    print("   [✓] Full contiguous range 1 to 495 present.")

# 3. Content Validation (Empty or clipped text)
short_sections = []
prefix_mismatches = []
truncated_titles = []
schedule_bleeds = []

preposition_ends = (" of", " the", " and", " in", " to", " with", " for", " by", " or", " on")

for s in sections:
    num_str = s["section_number"]
    num = int(num_str)
    body = s.get("full_text", "").strip()
    title = s.get("section_title", "").strip()
    
    # Body length check
    if len(body) < 20:
        short_sections.append((num, len(body), body))
        
    # Section prefix check (does body start with N. or N )
    if not re.match(rf'^{num}\b', body):
        prefix_mismatches.append((num, body[:40]))
        
    # Truncated title check
    if any(title.lower().endswith(p) for p in preposition_ends) or title == f"Section {num}":
        truncated_titles.append((num, title))
        
    # Schedule bleed check
    if re.search(r'\b(FIRST|SECOND|THIRD|FOURTH)\s+SCHEDULE\b', body, re.IGNORECASE):
        schedule_bleeds.append((num, title))

print("\n2. Content & Formatting Validation:")

if short_sections:
    print(f"   [!] Suspiciously short text ({len(short_sections)}):")
    for num, length, txt in short_sections[:5]:
        print(f"       - Sec {num} ({length} chars): {repr(txt)}")
    issues_found += len(short_sections)
else:
    print("   [✓] No empty or stub sections detected.")

if prefix_mismatches:
    print(f"   [!] Body prefix mismatches ({len(prefix_mismatches)}):")
    for num, txt in prefix_mismatches[:5]:
        print(f"       - Sec {num} starts with: {repr(txt)}")
    issues_found += len(prefix_mismatches)
else:
    print("   [✓] All section bodies begin with their matching section number.")

if truncated_titles:
    print(f"   [i] Potentially incomplete/clipped titles ({len(truncated_titles)}):")
    for num, title in truncated_titles[:10]:
        print(f"       - Sec {num:>3}: \"{title}\"")
    if len(truncated_titles) > 10:
        print(f"       ... and {len(truncated_titles) - 10} more.")
else:
    print("   [✓] All section titles are well-formed.")

if schedule_bleeds:
    print(f"   [!] Schedule markers bleeding into body text ({len(schedule_bleeds)}):")
    for num, title in schedule_bleeds:
        print(f"       - Sec {num}: {title}")
    issues_found += len(schedule_bleeds)
else:
    print("   [✓] No Schedule bleed detected in any section body.")

# 4. Spot-Check Sample Output
print("\n" + "=" * 80)
print("SPOT CHECK PREVIEW (Sections 1, 100, 200, 300, 400, 495)")
print("=" * 80)
spot_targets = [1, 100, 200, 300, 400, 495]
for s in sections:
    n = int(s["section_number"])
    if n in spot_targets:
        first_line = s["full_text"].split("\n")[0]
        print(f"[{n:>3}] Title : {s['section_title']}")
        print(f"      Part  : {s['part']}")
        print(f"      Start : {first_line[:90]}")
        print("-" * 75)

print("\n" + "=" * 80)
if issues_found == 0 and not truncated_titles:
    print("OVERALL RESULT: [✓] PERFECT ZERO-MISMATCH PASS")
elif issues_found == 0:
    print(f"OVERALL RESULT: [✓] CLEAN BODY TEXT PASS ({len(truncated_titles)} titles may need cosmetic check)")
else:
    print(f"OVERALL RESULT: [!] FOUND {issues_found} CRITICAL MISMATCHES")
print("=" * 80)
