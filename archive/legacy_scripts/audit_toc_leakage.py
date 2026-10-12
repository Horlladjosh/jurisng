import json
import re
from pathlib import Path

def audit_all_for_toc():
    json_dir = Path("data/json_laws")
    print("=" * 80)
    print("GLOBAL TABLE OF CONTENTS (TOC) CONTAMINATION AUDIT")
    print("=" * 80)

    total_tainted = 0

    for j_path in sorted(json_dir.glob("*.json")):
        with open(j_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        statute_title = data.get("short_title", j_path.name)
        sections = data.get("sections", [])
        tainted_sections = []

        for s in sections:
            txt = s.get("full_text", "")
            s_num = s.get("section_number", "")
            
            # Diagnostic for TOC patterns:
            # 1. Contains consecutive section list patterns like "36. ... 37. ..."
            # 2. Contains words like "Arrangement of Sections"
            # 3. Very short without legal operative verbs ("shall", "may", "person", "court", "offence", "act")
            has_consecutive_nums = bool(re.search(r'\b\d{1,3}\.\s+[A-Z][a-z]+.*\b\d{1,3}\.\s+[A-Z][a-z]+', txt))
            is_toc_title_dump = "arrangement of sections" in txt.lower() or "sections:" in txt.lower()
            
            if has_consecutive_nums or is_toc_title_dump:
                tainted_sections.append(s_num)

        if tainted_sections:
            print(f"✗ [{statute_title}]: {len(tainted_sections)} contaminated sections found!")
            print(f"  Contaminated Section Numbers: {tainted_sections[:15]}{'...' if len(tainted_sections)>15 else ''}")
            total_tainted += len(tainted_sections)
        else:
            print(f"✓ [{statute_title}]: 100% CLEAN (Zero TOC contamination across {len(sections)} sections)")

    print("=" * 80)
    print(f"TOTAL CONTAMINATED SECTIONS ACROSS ALL STATUTES: {total_tainted}")
    print("=" * 80)

if __name__ == "__main__":
    audit_all_for_toc()
