import json
import re
from pathlib import Path

JSON_DIR = Path("data/json_laws")

# Common OCR corruption patterns found in Nigerian Gazette print layers
SUSPICIOUS_PATTERNS = {
    "Broken Subsection Parens": r'\(\]|\(l\s*\)|\(I\s*\)|\b0\)',
    "Number-for-Word (01' / 01 for or)": r"\b01\'\b|\b01\b\s+[a-z]",
    "Number-for-Word (1I1 / 111 for in)": r'\b1I1\b|\b111\b\s+[a-z]',
    "Letter-for-Word (lo for to / hv for by)": r'\blo\b|\bhv\b',
    "Punctuation Glitches (u!' / asmay / whether->)": r"u!\'|asmay|whether->|certificate\s*—\.",
    "Merged Words (ofthe / inthe / forthe)": r'\bofthe\b|\binthe\b|\bforthe\b|\bbythe\b',
    "Marginal Note Leaks": r'Adnussibilu|dfKII|Official\s+Gazette',
}

def scan():
    print("=" * 80)
    print("SCANNING ENTIRE CORPUS (1,844 SECTIONS) FOR OCR & STRUCTURAL DEFECTS")
    print("=" * 80)

    total_flagged = 0
    statute_flags = {}

    for j_file in sorted(JSON_DIR.glob("*.json")):
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        s_name = data.get("short_title", j_file.stem)
        statute_flags[s_name] = []

        for sec in data.get("sections", []):
            sec_num = sec.get("section_number", "?")
            text = sec.get("full_text", "")
            issues = []

            # Check 1: Regex OCR glitches
            for label, pat in SUSPICIOUS_PATTERNS.items():
                if re.search(pat, text):
                    issues.append(label)

            # Check 2: Unterminated sentence endings (excluding short header sections)
            if len(text) > 60 and not text.rstrip().endswith((".", ";", ":", '"', "'", ")", "—", "-")):
                issues.append("Unterminated Ending / Cutoff")

            # Check 3: Duplicate subsection markers like (b) followed by (b)
            sub_markers = re.findall(r'\(([a-z]|\d+)\)', text)
            if len(sub_markers) != len(set(sub_markers)):
                # Filter out valid repetitive markers across different parent sub-clauses
                dups = [m for m in set(sub_markers) if sub_markers.count(m) > 1 and m in ['a', 'b', 'c', 'd']]
                if dups and not re.search(r'\(\d+\)', text): # only flag if single-level enumeration repeats
                    issues.append(f"Repeated Subsection Markers: {dups}")

            if issues:
                statute_flags[s_name].append((sec_num, issues))
                total_flagged += 1

        flag_count = len(statute_flags[s_name])
        icon = "⚠" if flag_count > 0 else "✓"
        print(f"{icon} {s_name:<35} : {flag_count:>3} sections flagged")

    print("\n" + "=" * 80)
    print(f"TOTAL SECTIONS FLAGGED WITH ARTIFACTS: {total_flagged} / 1,844")
    print("=" * 80)

    # Detailed breakdown sample
    for s_name, flaws in statute_flags.items():
        if flaws:
            print(f"\n[{s_name}] Sample Issues:")
            for sec_num, issues in flaws[:5]:
                print(f"  • Section {sec_num:>3}: {', '.join(issues)}")
            if len(flaws) > 5:
                print(f"    ... and {len(flaws) - 5} more sections.")

if __name__ == "__main__":
    scan()
