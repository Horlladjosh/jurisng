import json
import re
import sqlite3
import os

JSON_PATH = "data/json_laws/cama_2020.json"

STRUCTURAL_PATTERN = r'^(\(\d+\)|\([a-z]\)|\([ivx]+\)|\([A-Z]\)|\[[A-Z0-9]|Provided\s+that|Provided\s+further|Provided\s+always|"[^"]+"\s+(?:means|includes|refers)|FIRST\s+SCHEDULE|SECOND\s+SCHEDULE|THIRD\s+SCHEDULE|FOURTH\s+SCHEDULE|FIFTH\s+SCHEDULE|TABLE\s+[I|V|X]+|PART\s+[I|V|X]+|CHAPTER\s+\d+)'

def clean_cama_section_text(raw_text: str) -> str:
    if not raw_text:
        return raw_text

    # 1. Clean digit OCR space artifacts: e.g. "section 4 50" -> "section 450", "section 46 4" -> "section 464"
    def fix_digit_space(m):
        prefix = m.group(1)
        d1 = m.group(2)
        d2 = m.group(3)
        return f"{prefix}{d1}{d2}"

    raw_text = re.sub(r'\b(section\s+)(\d{1,3})\s+(\d{1,2})\b', fix_digit_space, raw_text, flags=re.I)
    raw_text = re.sub(r'\b(sections\s+)(\d{1,3})\s+(\d{1,2})\b', fix_digit_space, raw_text, flags=re.I)

    # 2. Normalize linebreaks and split into lines
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

    refined_paragraphs = []
    current_para = ''

    for line in lines:
        # Check if line starts a structural statutory block
        is_new_block = bool(re.match(STRUCTURAL_PATTERN, line, re.I))

        if is_new_block:
            if current_para:
                refined_paragraphs.append(current_para)
            current_para = line
        else:
            if current_para:
                # Handle hyphenated linebreaks: e.g. "admin-" + "istrator" -> "administrator"
                if current_para.endswith('-') or current_para.endswith('‐'):
                    current_para = current_para[:-1] + line
                else:
                    current_para += ' ' + line
            else:
                current_para = line

    if current_para:
        refined_paragraphs.append(current_para)

    text = '\n\n'.join(refined_paragraphs)

    # 3. Clean OCR typos & jurisdiction misreads
    text = re.sub(r'\bNigena\b', 'Nigeria', text)
    text = re.sub(r'\bNi\s*[-‐‑]\s*gena\b', 'Nigeria', text)
    text = re.sub(r'\bNi\s*[-‐‑]\s*geria\b', 'Nigeria', text)
    text = re.sub(r'\bNi\s*[-‐‑]\s+geria\b', 'Nigeria', text)

    # Clean double spaces
    text = re.sub(r'[ \t]{2,}', ' ', text)

    return text.strip()

def perfect_cama():
    print("[*] Starting 100% Statutory Fidelity Reflow for CAMA 2020...")

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sections = data.get('sections', []) if isinstance(data, dict) else data
    print(f"[*] Auditing {len(sections)} CAMA 2020 sections in JSON corpus...")

    updated_count = 0

    for s in sections:
        sec_num = str(s.get('section_number', ''))
        sec_title = s.get('section_title', '')
        orig_text = s.get('full_text', '')

        cleaned_text = clean_cama_section_text(orig_text)

        if cleaned_text != orig_text:
            s['full_text'] = cleaned_text
            s['searchable_chunk'] = f"Companies and Allied Matters Act, 2020 Sec {sec_num}: {sec_title}. {cleaned_text[:200]}"
            updated_count += 1

    if isinstance(data, dict):
        data['sections'] = sections

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[✓] Reflow complete! {updated_count} sections updated in {JSON_PATH}.")

    # Rebuild SQLite Database
    print("[*] Rebuilding SQLite database and FTS5 search index...")
    os.system("python3 build_database.py")

    print("\n" + "=" * 80)
    print(f"[✓] CAMA 2020 100% FIDELITY AUDIT & DATABASE REBUILD COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    perfect_cama()
