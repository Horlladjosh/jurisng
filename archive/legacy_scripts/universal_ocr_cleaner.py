import json
import re
from pathlib import Path

JSON_DIR = Path("data/json_laws")

def clean_statutory_text(text: str) -> str:
    if not text:
        return ""
    
    # 1. Strip gazette headers, footers & page numbers
    text = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'B\s+\d+\s+[A-Z\s]+', '', text)
    
    # 2. Fix common subsection bracket OCR artifacts
    text = re.sub(r'\(\]\)', '(1)', text)
    text = re.sub(r'\(l\s*\)', '(1)', text)
    text = re.sub(r'\(I\s*\)', '(1)', text)
    text = re.sub(r'\b0\)', '(3)', text)
    text = re.sub(r'\ba\'\>', 'as', text)
    text = re.sub(r'\bhv\b', 'by', text)
    text = re.sub(r'\blo\b', 'to', text)
    text = re.sub(r'referred\s+10\b', 'referred to', text)
    text = re.sub(r'combinations\s+OJ\b', 'combinations of', text)
    text = re.sub(r'\"lorthe\b', 'for the', text)
    text = re.sub(r'u!\'\b', 'of', text)
    text = re.sub(r'\bmanner\s+111\b', 'manner in', text)
    text = re.sub(r'\b111\s+the\b', 'in the', text)
    text = re.sub(r'\b1I1\s+the\b', 'in the', text)
    text = re.sub(r'ofthe\b', 'of the', text)
    text = re.sub(r'a\'>may', 'as may', text)
    
    # 3. Strip spliced marginal title noise (standalone title phrases on broken lines)
    text = re.sub(r'Adnussibilu[^\.\(]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'dfKII1J1clll', 'document', text)
    
    # 4. Standardize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def scrub_all_json():
    total_cleaned = 0
    for j_file in sorted(JSON_DIR.glob("*.json")):
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        statute_short = data.get("short_title", j_file.stem)
        for sec in data.get("sections", []):
            original = sec.get("full_text", "")
            cleaned = clean_statutory_text(original)
            sec["full_text"] = cleaned
            sec["searchable_chunk"] = f"{statute_short} | Section {sec.get('section_number', '')} | {cleaned}"
            total_cleaned += 1

        with open(j_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"[✓] Scrubbed OCR noise from: {j_file.name}")

    print(f"\n[DONE] Normalized {total_cleaned} sections across all statutes.")

if __name__ == "__main__":
    scrub_all_json()
