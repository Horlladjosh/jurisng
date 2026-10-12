import json
import re
from pathlib import Path

DATA_PATH = Path("data/json_laws/acja_2015.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Patterns that represent isolated running headers/footers in the Gazette
noise_patterns = [
    r'(?mi)^\s*ADMINISTRATION\s+OF\s+CRIMINAL\s+JUSTICE\s+(?:ACT,?\s*2015)?\s*$',
    r'(?mi)^\s*FEDERAL\s+REPUBLIC\s+OF\s+NIGERIA\s+(?:OFFICIAL\s+GAZETTE)?\s*$',
    r'(?mi)^\s*B\s+[0-9]+\s*$'  # Gazette page numbers like B 104
]

cleaned_count = 0

for sec in data["sections"]:
    sec_num = int(sec["section_number"])
    original_text = sec["full_text"]
    text = original_text
    
    for pat in noise_patterns:
        # Don't strip citation line from Section 495 (which is the actual statutory sentence)
        if sec_num == 495 and "may be cited as" in text:
            continue
        text = re.sub(pat, '', text)
    
    # Normalize leftover empty lines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
    
    if text != original_text:
        cleaned_count += 1
        sec["full_text"] = text
        sec["searchable_chunk"] = f"Administration of Criminal Justice Act, 2015 | {sec['part']} | {sec['section_number']}. {sec['section_title']} | {text}"

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"[✓] Sanitized running headers across {cleaned_count} sections.")
