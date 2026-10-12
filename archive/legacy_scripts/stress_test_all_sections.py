import json
import re
from pathlib import Path

DATA_PATH = Path("data/json_laws/acja_2015.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

sections = data["sections"]
total = len(sections)

print("=" * 80)
print(f"DEEP STRESS-TEST ACROSS ALL 495 SECTIONS: {data['short_title']}")
print("=" * 80)

boundary_leaks = []
header_leaks = []
odd_starts = []
suspicious_lengths = []

gazette_noise_patterns = [
    r'ADMINISTRATION OF CRIMINAL JUSTICE',
    r'FEDERAL REPUBLIC OF NIGERIA',
    r'OFFICIAL GAZETTE',
    r'ACT NO\.',
    r'B\s+[0-9]+', # Gazette page codes like B 123
]

for i, sec in enumerate(sections):
    num = int(sec["section_number"])
    body = sec["full_text"]
    title = sec["section_title"]
    part = sec["part"]
    
    # 1. Check for Next-Section Bleed (e.g. "45. " appearing inside section 44's body)
    if num < 495:
        next_num = num + 1
        # Look for next section pattern at line start
        leak_match = re.search(rf'\n\s*{next_num}\.?\s+', body)
        if leak_match:
            boundary_leaks.append((num, next_num, body[leak_match.start():leak_match.start()+60]))

    # 2. Check for Gazette Header/Footer artifacts
    for pat in gazette_noise_patterns:
        if re.search(pat, body, re.IGNORECASE):
            header_leaks.append((num, pat))

    # 3. Check for Odd Starts (should start strictly with "N." or "N ")
    if not re.match(rf'^{num}\b', body.strip()):
        odd_starts.append((num, body[:50]))

    # 4. Outlier length checks
    char_len = len(body)
    if char_len < 35:
        suspicious_lengths.append((num, title, char_len, "VERY SHORT"))

# Report results
print(f"1. Sequence & Bounding Box Checks:")
if not boundary_leaks:
    print("   [✓] 0 Boundary Leaks: Every section cuts off cleanly before the next begins.")
else:
    print(f"   [!] Found {len(boundary_leaks)} boundary leaks:")
    for cur, nxt, snip in boundary_leaks:
        print(f"       - Sec {cur} contains start of Sec {nxt}: {repr(snip)}")

print("\n2. Header / Footer / Watermark Noise Checks:")
if not header_leaks:
    print("   [✓] 0 Header/Footer Artifacts: Spatial boundary completely excluded running headers.")
else:
    print(f"   [!] Found {len(header_leaks)} header leak instances:")
    for num, pat in header_leaks:
        print(f"       - Sec {num} contains pattern: {pat}")

print("\n3. Prefix & Structure Alignment:")
if not odd_starts:
    print("   [✓] 100% Prefix Match: All 495 sections begin with their exact integer identifier.")
else:
    print(f"   [!] Found {len(odd_starts)} prefix mismatches:")
    for num, snip in odd_starts:
        print(f"       - Sec {num}: {repr(snip)}")

print("\n4. Length Outliers (Shortest Sections Spot-Check):")
if suspicious_lengths:
    for num, title, clen, tag in suspicious_lengths:
        print(f"   [i] Sec {num:>3} ({clen} chars) | Title: \"{title}\"")
        print(f"       Body: {repr(sections[num-1]['full_text'])}")
else:
    print("   [✓] All sections have substantial content.")

# 5. Full Section Range Statistics
lengths = [len(s["full_text"]) for s in sections]
print("\n" + "=" * 80)
print(f"DATASET STATS:")
print(f"  - Total Sections: {len(sections)}")
print(f"  - Total Word Count: {sum(len(s['full_text'].split()) for s in sections):,} words")
print(f"  - Shortest Section: Sec {lengths.index(min(lengths))+1} ({min(lengths)} chars)")
print(f"  - Longest Section: Sec {lengths.index(max(lengths))+1} ({max(lengths)} chars)")
print(f"  - Average Length: {sum(lengths)//len(lengths)} chars / section")
print("=" * 80)
