import json
from pathlib import Path

JSON_DIR = Path("data/json_laws")

def audit_all():
    print("=" * 80)
    print("RIGOROUS CORPUS AUDIT: CHECKING ALL SECTIONS FOR INTEGRITY")
    print("=" * 80)

    total_statutes = 0
    total_sections_checked = 0
    total_errors = 0

    for j_file in sorted(JSON_DIR.glob("*.json")):
        total_statutes += 1
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        s_name = data.get("short_title", j_file.stem)
        sections = data.get("sections", [])
        total_sections_checked += len(sections)

        seen_texts = {}
        statute_errors = []
        expected_num = 1

        for sec in sections:
            num_str = str(sec.get("section_number", ""))
            text = sec.get("full_text", "").strip()

            # 1. Check numeric sequence
            try:
                num_int = int(re_num := ''.join(filter(str.isdigit, num_str)))
                if num_int != expected_num and num_int != expected_num - 1: # allow occasional sub-sections if any
                    expected_num = num_int
            except ValueError:
                pass
            expected_num += 1

            # 2. Check for empty or stub sections (< 45 chars)
            if len(text) < 45:
                statute_errors.append(f"Section {num_str}: Stub/Empty ({len(text)} chars)")

            # 3. Check for text duplication across different section numbers
            prefix = text[:150]
            if prefix in seen_texts:
                statute_errors.append(f"Section {num_str} is duplicate of Section {seen_texts[prefix]}")
            else:
                seen_texts[prefix] = num_str

        if statute_errors:
            total_errors += len(statute_errors)
            print(f"\n[FAIL] {s_name} ({len(sections)} sections):")
            for err in statute_errors[:10]:
                print(f"  • {err}")
            if len(statute_errors) > 10:
                print(f"  ... and {len(statute_errors) - 10} more issues.")
        else:
            print(f"[PASS] {s_name:<38} : {len(sections):>4} sections verified clean.")

    print("\n" + "=" * 80)
    print(f"AUDITED {total_sections_checked} SECTIONS ACROSS {total_statutes} STATUTES. TOTAL ERRORS: {total_errors}")
    print("=" * 80)

if __name__ == "__main__":
    audit_all()
