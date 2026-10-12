import json
import re
from pathlib import Path

JSON_DIR = Path("data/json_laws")

def exact_legal_clean(text: str) -> str:
    if not text:
        return ""

    # Fix specific Evidence Act S.84 subsection mis-lettering & OCR glitches
    text = re.sub(r'\(e\)\s*a\s+document\s+shall\s+be\s+taken', '(c) a document shall be taken', text, flags=re.IGNORECASE)
    text = re.sub(r'\b01\'\b', 'or', text)
    text = re.sub(r'\b01\b(?=\s+[a-z])', 'or', text)
    text = re.sub(r'\b1I1\b', 'in', text)
    text = re.sub(r'\bu!\'\b', 'of', text)
    text = re.sub(r'\bu!\b', 'of', text)
    text = re.sub(r'\basmay\b', 'as may', text)
    text = re.sub(r'\bwhether->\b', 'whether—', text)
    text = re.sub(r'\"lorthe\b', 'for the', text)
    text = re.sub(r'combinations\s+OJ\b', 'combinations of', text)
    text = re.sub(r'combinations\s+of\"\s+computers', 'combinations of computers', text)
    text = re.sub(r'certificate\s*—\.', 'certificate—', text)
    text = re.sub(r'certificate\s*-\.', 'certificate—', text)
    text = re.sub(r'\ba\'\>', 'as', text)

    # Standardize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def run_strict_clean():
    for j_file in sorted(JSON_DIR.glob("*.json")):
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        statute_title = data.get("short_title", j_file.stem)
        for sec in data.get("sections", []):
            cleaned = exact_legal_clean(sec.get("full_text", ""))
            sec["full_text"] = cleaned
            sec["searchable_chunk"] = f"{statute_title} | Section {sec.get('section_number', '')} | {cleaned}"

        with open(j_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[✓] Strictly Cleaned: {j_file.name}")

if __name__ == "__main__":
    run_strict_clean()
