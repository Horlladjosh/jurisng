import os
import json
import re

JSON_DIR = "data/json_laws"

# Targeted word replacements for OCR scanning artifacts
OCR_REPLACEMENTS = {
    # Nigeria typos & split variants
    r'\bNigena\b': 'Nigeria',
    r'\bNi\s*[-‐‑]\s*gena\b': 'Nigeria',
    r'\bNi\s*[-‐‑]\s*geria\b': 'Nigeria',
    r'\bNi\s*[-‐‑]\s*gnia\b': 'Nigeria',
    r'\bNi\s*[-‐‑]\s+geria\b': 'Nigeria',

    # FCCPA / scanned OCR font confusions (rv -> w, n -> m, etc.)
    r'\brvith\b': 'with',
    r'\brvho\b': 'who',
    r'\brvhich\b': 'which',
    r'\bothenvise\b': 'otherwise',
    r'\bcomnrission\b': 'commission',
    r'\bnrerger\b': 'merger',
    r'\binfornratiorr\b': 'information',
    r'\bu\'ith\b': 'with',
    r'\bCoJmnencement\b': 'Commencement',
    r'\boriginaI\b': 'original',
    r'\bcoorporation\b': 'corporation',
    r'\bauthorised\s+ofiicer\b': 'authorised officer',
    r'\bconrpluitturrl\b': 'complainant',
    r'\bconrpetitors\b': 'competitors',
    r'\bconrsurtter\b': 'consumer',
    r'\bconrpelition\b': 'competition',

    # Labour Act / old font OCR confusions (b -> h)
    r'\btbe\b': 'the',
    r'\btbat\b': 'that',
    r'\bwitb\b': 'with',
    r'\btbeir\b': 'their',
    r'\bIbis\b': 'this',
    r'\botber\b': 'other',

    # Common OCR section & digit typos
    r'\bsection\s+I\s+of\b': 'section 1 of',
    r'\bsubsection\s+\(I\)\b': 'subsection (1)',
    r'\bparagraph\s+\(I\)\b': 'paragraph (1)',
}

def reflow_statutory_text(text: str) -> str:
    """
    Removes artificial mid-sentence PDF line wraps while preserving true statutory structural blocks
    (subsections, paragraphs, citations, and defined terms).
    """
    if not text:
        return text

    lines = text.split("\n")
    cleaned_paragraphs = []
    curr_para = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if curr_para:
                cleaned_paragraphs.append(curr_para)
                curr_para = ""
            continue

        # Check if line starts a structural statutory block:
        # e.g., (1), (2), (a), (b), (i), (ii), (A), [Cap., [1993, "Defined Term" means
        is_new_block = bool(re.match(r"^(\(\d+\)|\([a-z]\)|\([ivx]+\)|\([A-Z]\)|\[[A-Z0-9]|\"[^\"]+\"\s+(?:means|includes|refers))", stripped))

        if is_new_block:
            if curr_para:
                cleaned_paragraphs.append(curr_para)
            curr_para = stripped
        else:
            if curr_para:
                curr_para += " " + stripped
            else:
                curr_para = stripped

    if curr_para:
        cleaned_paragraphs.append(curr_para)

    return "\n\n".join(cleaned_paragraphs)

def clean_text(text: str) -> str:
    if not text:
        return text

    # 1. Merge hyphenated words split across line breaks: e.g. "busi- \nness" -> "business", "Ni- \ngeria" -> "Nigeria"
    def merge_hyphen(m):
        prefix = m.group(1)
        suffix = m.group(2)
        if prefix.lower() == 'ni' and suffix.lower() in ['gena', 'geria', 'gnia']:
            return 'Nigeria'
        return f"{prefix}{suffix}"

    text = re.sub(r'\b([a-zA-Z]{2,})[-‐‑\xad]\s*\n\s*([a-zA-Z]{2,})\b', merge_hyphen, text)

    # 2. Apply targeted OCR string replacements
    for pattern, replacement in OCR_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text)

    # 3. Apply paragraph reflow to remove false PDF margin linebreaks
    text = reflow_statutory_text(text)

    # 4. Clean trailing whitespace before linebreaks and strip double spaces
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)

    return text.strip()

def process_corpus():
    files = sorted([f for f in os.listdir(JSON_DIR) if f.endswith('.json')])
    print(f"[*] Auditing and reflowing text across {len(files)} statutory JSON files...")

    total_files_modified = 0
    total_sections_modified = 0

    for filename in files:
        filepath = os.path.join(JSON_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        is_dict = isinstance(data, dict)
        sections = data.get('sections', []) if is_dict else data

        file_modified = False
        sections_modified_count = 0

        for sec in sections:
            orig_text = sec.get('full_text', '')
            orig_title = sec.get('section_title', '')

            cleaned_text = clean_text(orig_text)
            cleaned_title = clean_text(orig_title)

            if cleaned_text != orig_text or cleaned_title != orig_title:
                sec['full_text'] = cleaned_text
                sec['section_title'] = cleaned_title
                sec['searchable_chunk'] = f"{sec.get('statute_title', '')} Sec {sec.get('section_number', '')}: {cleaned_title}. {cleaned_text[:200]}"
                file_modified = True
                sections_modified_count += 1

        if file_modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            total_files_modified += 1
            total_sections_modified += sections_modified_count
            print(f"    [+] Reflowed & Sanitized: {filename} ({sections_modified_count} sections updated)")
        else:
            print(f"    [-] Clean: {filename}")

    print("\n" + "=" * 70)
    print(f"[✓] CORPUS REFLOW & SANITIZATION COMPLETE!")
    print(f"    • Files Modified: {total_files_modified}/{len(files)}")
    print(f"    • Total Sections Reflowed: {total_sections_modified}")
    print("=" * 70)

if __name__ == "__main__":
    process_corpus()
