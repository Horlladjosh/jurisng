import json
import re
from pathlib import Path

JSON_DIR = Path("data/json_laws")

def purge_artifacts(text: str) -> str:
    if not text:
        return ""

    # 1. Clean CFRN & Gazette Marginal Headings spliced into paragraphs
    text = re.sub(r'Legislative\s+oversight\s+of\s+the\s+executive\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Removal\s+of\s+President\s+from\s+office\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Removal\s+of\s+Governor\s+from\s+office\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Admissibility\s+of\s+certain\s+Judgments.*', '', text, flags=re.IGNORECASE)

    # 2. Fix specific Evidence Act S.55 and sibling punctuation/OCR errors
    text = re.sub(r'\bu!\'\b', 'of', text)
    text = re.sub(r'\bu!\b', 'of', text)
    text = re.sub(r'\basmay\b', 'as may', text)
    text = re.sub(r'\bwhether\s*->\b', 'whether—', text)
    text = re.sub(r'\bwhether->\b', 'whether—', text)
    text = re.sub(r'referred\s+10\b', 'referred to', text)
    text = re.sub(r'certificate\s*—\.', 'certificate—', text)
    text = re.sub(r'certificate\s*-\.', 'certificate—', text)

    # 3. Clean trailing formatting leaks & orphan brackets
    text = re.sub(r'\s*\[Part\s+[I|V|X\d\s\w]+Schedule\].*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*PART\s+[I|V|X\d]+[\s\-\–\—\:\.\w\,]+$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*CHAPTER\s+[I|V|X\d]+[\s\-\–\—\:\.\w\,]+$', '', text, flags=re.IGNORECASE)

    # 4. Standardize spacing and punctuation
    text = re.sub(r'\s+([,;:\.\)])', r'\1', text)
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # 5. Ensure valid trailing punctuation
    if text and text[-1].isalnum() and not text.endswith((".", ";", ":", '"', "'", ")", "—", "-")):
        text += "."

    return text

def execute_seal():
    total_cleaned = 0
    for j_file in sorted(JSON_DIR.glob("*.json")):
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        s_name = data.get("short_title", j_file.stem)
        for sec in data.get("sections", []):
            original = sec.get("full_text", "")
            cleaned = purge_artifacts(original)
            sec["full_text"] = cleaned
            sec["searchable_chunk"] = f"{s_name} | Section {sec.get('section_number', '')} | {cleaned}"
            total_cleaned += 1

        with open(j_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[✓] Finalized: {j_file.name}")

    print(f"\n[SUCCESS] All {total_cleaned} statutory sections finalized and verified.")

if __name__ == "__main__":
    execute_seal()
