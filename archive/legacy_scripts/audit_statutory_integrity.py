import json
import re
from pathlib import Path

JSON_DIR = Path("data/json_laws")

REAL_OCR_DEFECTS = {
    "Broken Subsection Parens": r'\(\s*\]|\(l\s*\)|\(I\s*\)|\b0\)',
    "Corrupted Word (01' / 01 for or)": r"\b01\'\b|\b01\b\s+[a-z]",
    "Corrupted Word (1I1 / 111 for in)": r'\b1I1\b|\b111\b\s+[a-z]',
    "Corrupted Word (lo for to / hv for by)": r'\blo\b|\bhv\b',
    "Punctuation Glitch (u!' / asmay / whether->)": r"u!\'|asmay|whether->|certificate\s*—\.",
    "Merged Words (ofthe / inthe / forthe)": r'\bofthe\b|\binthe\b|\bforthe\b|\bbythe\b',
    "Gazette Watermark / Marginal Leaks": r'Adnussibilu|dfKII|Official\s+Gazette\s+No\.',
}

def audit():
    print("=" * 80)
    print("RIGOROUS STATUTORY AUDIT: VERIFYING TEXTUAL PERFECTION")
    print("=" * 80)

    total_flaws = 0
    for j_file in sorted(JSON_DIR.glob("*.json")):
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        s_name = data.get("short_title", j_file.stem)
        statute_issues = []

        for sec in data.get("sections", []):
            sec_num = sec.get("section_number", "?")
            text = sec.get("full_text", "")
            issues = []

            for label, pat in REAL_OCR_DEFECTS.items():
                if re.search(pat, text):
                    issues.append(label)

            if issues:
                statute_issues.append((sec_num, issues))
                total_flaws += 1

        status = "✓ Clean" if not statute_issues else f"⚠ {len(statute_issues)} issues"
        print(f"[{status:<8}] {s_name:<38} ({len(data.get('sections', []))} sections)")

    print("=" * 80)
    print(f"VERDICT: {total_flaws} REAL OCR / MARGINAL DEFECTS REMAINING")
    print("=" * 80)

if __name__ == "__main__":
    audit()
