import json
import re
from pathlib import Path

JSON_DIR = Path("data/json_laws")

def clean_statute_section(text: str) -> str:
    if not text:
        return ""

    # 1. Strip internal gazette running noise
    text = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\d{4}\s+No\.\s*\d+.*?Nigeria\s+Police\s+Act.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Adnussibilu[^\.\(]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'dfKII1J1clll', 'document', text)

    # 2. Fix OCR artifacts & character swaps
    text = re.sub(r'\(\]\)', '(1)', text)
    text = re.sub(r'\(l\s*\)', '(1)', text)
    text = re.sub(r'\(I\s*\)', '(1)', text)
    text = re.sub(r'\b0\)', '(3)', text)
    text = re.sub(r"\b01\'\b", "or", text)
    text = re.sub(r"\b01\b(?=\s+[a-z])", "or", text)
    text = re.sub(r"\b1I1\b", "in", text)
    text = re.sub(r"\b111\b(?=\s+[a-z])", "in", text)
    text = re.sub(r"\bhv\b", "by", text)
    text = re.sub(r"\blo\b", "to", text)
    text = re.sub(r"\bu!\'\b", "of", text)
    text = re.sub(r"\bu!\b", "of", text)
    text = re.sub(r"\basmay\b", "as may", text)
    text = re.sub(r"\bwhether->\b", "whether—", text)
    text = re.sub(r'\ba\'\>', "as", text)
    text = re.sub(r'\bofthe\b', "of the", text)
    text = re.sub(r'\binthe\b', "in the", text)
    text = re.sub(r'\bforthe\b', "for the", text)
    text = re.sub(r'\bbythe\b', "by the", text)
    text = re.sub(r'\btothe\b', "to the", text)
    text = re.sub(r'\bandthe\b', "and the", text)
    text = re.sub(r'referred\s+10\b', "referred to", text)
    text = re.sub(r'combinations\s+OJ\b', "combinations of", text)
    text = re.sub(r'\"lorthe\b', "for the", text)
    text = re.sub(r'certificate\s*—\.', "certificate—", text)
    text = re.sub(r'certificate\s*-\.', "certificate—", text)

    # 3. Strip trailing Part/Chapter/Schedule headers erroneously captured at the tail
    trailing_headers = [
        r'\s*PART\s+[I|V|X\d]+[\s\-\–\—\:\.\w\,]+$',
        r'\s*CHAPTER\s+[I|V|X\d]+[\s\-\–\—\:\.\w\,]+$',
        r'\s*\[Part\s+[I|V|X\d\s\w]+Schedule\]\s*PART\s+[I|V|X\d]+.*$',
        r'\s*Admissibility of evidence under other legislation.*$',
        r'\s*Evidence In accordance with section.*$',
        r'\s*·+\s*·+-+·*\s*Nigeria Police Act.*$',
    ]
    for pattern in trailing_headers:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # 4. Normalize spacing & punctuation
    text = re.sub(r'\s+([,;:\.\)])', r'\1', text)
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # 5. Ensure valid sentence termination if it ends cleanly without one
    if text and text[-1].isalnum() and not text.endswith((".", ";", ":", '"', "'", ")", "—", "-")):
        text += "."

    return text

def run_trim():
    total_trimmed = 0
    for j_file in sorted(JSON_DIR.glob("*.json")):
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        s_name = data.get("short_title", j_file.stem)
        for sec in data.get("sections", []):
            cleaned = clean_statute_section(sec.get("full_text", ""))
            sec["full_text"] = cleaned
            sec["searchable_chunk"] = f"{s_name} | Section {sec.get('section_number', '')} | {cleaned}"
            total_trimmed += 1

        with open(j_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[✓] Trimmed & Normalized: {j_file.name}")

    print(f"\n[COMPLETE] Cleaned and trimmed boundary leaks across {total_trimmed} sections.")

if __name__ == "__main__":
    run_trim()
