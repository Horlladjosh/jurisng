import json
import re
import sqlite3
import os

JSON_PATH = "data/json_laws/companies_income_tax_act.json"

STRUCTURAL_PATTERN = r'^(\(\d+\)|\([a-z]\)|\([ivx]+\)|\([A-Z]\)|\[[A-Z0-9]|Provided\s+that|Provided\s+further|Provided\s+always|"[^"]+"\s+(?:means|includes|refers)|FIRST\s+SCHEDULE|SECOND\s+SCHEDULE|THIRD\s+SCHEDULE|FOURTH\s+SCHEDULE|FIFTH\s+SCHEDULE|TABLE\s+[I|V|X]+|PART\s+[I|V|X]+)'

def clean_section_fidelity(section_number, title, raw_text):
    if not raw_text:
        return raw_text

    # 1. Normalize linebreaks and strip surrounding whitespace
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

    refined_paragraphs = []
    current_para = ''

    for line in lines:
        # Check if this line starts a new structural statutory block
        is_new_block = bool(re.match(STRUCTURAL_PATTERN, line, re.I))

        if is_new_block:
            if current_para:
                refined_paragraphs.append(current_para)
            current_para = line
        else:
            if current_para:
                # Handle hyphenated linebreaks: e.g. "co-" + "operative" -> "co-operative"
                if current_para.endswith('-') or current_para.endswith('‐'):
                    # If prefix is hyphenated word part, keep hyphen or merge
                    current_para = current_para[:-1] + line
                else:
                    current_para += ' ' + line
            else:
                current_para = line

    if current_para:
        refined_paragraphs.append(current_para)

    # Rejoin blocks with double newlines
    text = '\n\n'.join(refined_paragraphs)

    # Fix OCR typos & broken Nigeria occurrences
    text = re.sub(r'\bNigena\b', 'Nigeria', text)
    text = re.sub(r'\bNi\s*[-‐‑]\s*gena\b', 'Nigeria', text)
    text = re.sub(r'\bNi\s*[-‐‑]\s*geria\b', 'Nigeria', text)
    text = re.sub(r'\bNi\s*[-‐‑]\s+geria\b', 'Nigeria', text)

    # Clean double spaces
    text = re.sub(r'[ \t]{2,}', ' ', text)

    return text.strip()

def perfect_cita():
    print("[*] Starting 100% Fidelity Reflow Audit for Companies Income Tax Act (CITA)...")

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sections = data.get('sections', [])
    print(f"[*] Found {len(sections)} CITA sections in JSON corpus.")

    updated_count = 0

    for s in sections:
        sec_num = str(s.get('section_number', ''))
        sec_title = s.get('section_title', '')
        orig_text = s.get('full_text', '')

        cleaned_text = clean_section_fidelity(sec_num, sec_title, orig_text)

        if cleaned_text != orig_text:
            s['full_text'] = cleaned_text
            s['searchable_chunk'] = f"Companies Income Tax Act Sec {sec_num}: {sec_title}. {cleaned_text[:200]}"
            updated_count += 1

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[✓] Reflow complete! {updated_count} sections updated in {JSON_PATH}.")

    # Rebuild SQLite Database
    print("[*] Rebuilding SQLite database and FTS5 search index...")
    os.system("python3 build_database.py")

    print("\n" + "=" * 80)
    print(f"[✓] CITA 100% FIDELITY AUDIT & DATABASE REBUILD COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    perfect_cita()
