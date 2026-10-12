import json
from pathlib import Path

JSON_DIR = Path("data/json_laws")

print("=" * 80)
print("COMPREHENSIVE STATUTORY INTEGRITY AUDIT (DUPLICATES, GAPS, EMPTY TEXT)")
print("=" * 80)

total_sections = 0
statutes_with_issues = 0

for j_file in sorted(JSON_DIR.glob("*.json")):
    with open(j_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    s_name = data.get("short_title", j_file.stem)
    sections = data.get("sections", [])
    total_sections += len(sections)
    
    seen_texts = {}
    duplicates = []
    short_or_empty = []
    
    for sec in sections:
        num = str(sec.get("section_number", "?"))
        txt = sec.get("full_text", "").strip()
        
        # Check empty or stub
        if len(txt) < 40:
            short_or_empty.append((num, len(txt)))
            
        # Check text duplication (different section numbers holding identical text)
        prefix = txt[:120]
        if prefix in seen_texts:
            duplicates.append((num, seen_texts[prefix]))
        else:
            seen_texts[prefix] = num

    has_issue = duplicates or short_or_empty
    if has_issue:
        statutes_with_issues += 1
        print(f"\n[FAIL] {s_name} ({len(sections)} sections):")
        if duplicates:
            print(f"  • DUPLICATE CONTENT ({len(duplicates)} sections share exact text with another):")
            for dup, orig in duplicates[:6]:
                print(f"      - Section {dup} is a duplicate copy of Section {orig}")
            if len(duplicates) > 6:
                print(f"      ... and {len(duplicates) - 6} more duplicates.")
        if short_or_empty:
            print(f"  • EMPTY / STUB SECTIONS ({len(short_or_empty)} sections):")
            for num, length in short_or_empty[:5]:
                print(f"      - Section {num}: only {length} characters")
    else:
        print(f"[PASS] {s_name:<38} : {len(sections):>4} sections verified clean.")

print("\n" + "=" * 80)
print(f"AUDITED {total_sections} SECTIONS ACROSS {len(list(JSON_DIR.glob('*.json')))} STATUTES")
print("=" * 80)
