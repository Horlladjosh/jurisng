import json
import re
from pathlib import Path

JSON_DIR = Path("data/json_laws")

def resolve_statute_flaws(text: str) -> str:
    if not text:
        return ""

    # 1. Broken Subsection Parens (Handle internal l, I, ], 0 inside clauses)
    text = re.sub(r'\(\s*\]\s*', '(1) ', text)
    text = re.sub(r'\(\s*[lI]\s*\)', '(1)', text)
    text = re.sub(r'\(\s*[lI]\s+', '(1) ', text)
    text = re.sub(r'\b0\)', '(3)', text)
    text = re.sub(r'\(\s*([a-z\d]+)\s*\]', r'(\1)', text)
    text = re.sub(r'\[\s*([a-z\d]+)\s*\)', r'(\1)', text)

    # 2. Lingering Marginal Notes & Gazette Watermarks
    text = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Adnussibilu[^\.\(]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'dfKII1J1clll', 'document', text)
    text = re.sub(r'Investigation\s+by\s+the\s+National\s+Assembly.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Removal\s+of\s+President.*', '', text, flags=re.IGNORECASE)

    # 3. Punctuation Glitches & Typo Variants
    replacements = [
        (r"\bu!\'\b", "of"),
        (r"\bu!\b", "of"),
        (r"\basmay\b", "as may"),
        (r"\bwhether->\b", "whether—"),
        (r'\bwhether\s*->\b', "whether—"),
        (r'combinations\s+OJ\b', "combinations of"),
        (r'\"lorthe\b', "for the"),
        (r'certificate\s*—\.', "certificate—"),
        (r'certificate\s*-\.', "certificate—"),
    ]
    for pat, rep in replacements:
        text = re.sub(pat, rep, text)

    # 4. Strip dangling schedule references & headers at ends
    tail_patterns = [
        r'\s*\[Part\s+[I|V|X\d\s\w]+Schedule\]\s*PART\s+[I|V|X\d]+.*$',
        r'\s*\[Part\s+[I|V|X\d\s\w]+Schedule\].*$',
        r'\s*PART\s+[I|V|X\d]+[\s\-\–\—\:\.\w\,]+$',
        r'\s*CHAPTER\s+[I|V|X\d]+[\s\-\–\—\:\.\w\,]+$',
    ]
    for pat in tail_patterns:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)

    # 5. Spacing and Punctuation Cleanup
    text = re.sub(r'\s+([,;:\.\)])', r'\1', text)
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # 6. Ensure proper termination
    if text and text[-1].isalnum() and not text.endswith((".", ";", ":", '"', "'", ")", "—", "-")):
        text += "."

    return text

def execute():
    total_processed = 0
    for j_file in sorted(JSON_DIR.glob("*.json")):
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        s_name = data.get("short_title", j_file.stem)
        for sec in data.get("sections", []):
            original = sec.get("full_text", "")
            cleaned = resolve_statute_flaws(original)
            sec["full_text"] = cleaned
            sec["searchable_chunk"] = f"{s_name} | Section {sec.get('section_number', '')} | {cleaned}"
            total_processed += 1

        with open(j_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[✓] Refined: {j_file.name}")

    print(f"\n[COMPLETE] Cleaned {total_processed} sections across all statutes.")

if __name__ == "__main__":
    execute()
