import json
import re
from pathlib import Path

DATA_PATH = Path("data/json_laws/acja_2015.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. Clean Section 495 to remove First Schedule bleed
for sec in data["sections"]:
    if sec["section_number"] == "495":
        # Cut off at schedule or citation note
        cleaned_text = re.split(r'\n\s*FIRST SCHEDULE', sec["full_text"], flags=re.IGNORECASE)[0].strip()
        # Remove trailing margin rubric if present
        cleaned_text = re.sub(r'\n\s*Citation\.?\s*$', '', cleaned_text).strip()
        sec["full_text"] = cleaned_text
        sec["section_title"] = "Citation."

# 2. Re-map complete margin titles from the PDF blocks
import fitz
doc = fitz.open("data/raw_pdfs/acja-2015.pdf")

# Extract complete margin text blocks per page
full_margin_blocks = {}
for p_idx in range(20, 231):
    page = doc[p_idx]
    for b in page.get_text("blocks"):
        if b[6] == 0 and b[0] >= 500:
            title_text = " ".join(b[4].split()).strip()
            if title_text:
                full_margin_blocks.setdefault(p_idx, []).append((b[1], title_text))

# Update incomplete titles
for sec in data["sections"]:
    sec_num = int(sec["section_number"])
    # If title looks truncated (e.g. ends with "of", "and", "to", or is just "Section N")
    t = sec["section_title"]
    if sec_num != 495:
        # Find closest full margin block on its page
        # Search which page has this section
        for p_idx, margins in full_margin_blocks.items():
            txt = doc[p_idx].get_text("text")
            if re.search(rf'(?:^|\n)\s*{sec_num}\.?\s+', txt):
                # Pick the block closest to the section occurrence
                # Find matching margin block containing the truncated prefix
                for m_y, m_txt in margins:
                    if t.lower().rstrip('.') in m_txt.lower():
                        sec["section_title"] = m_txt.rstrip('.')
                        break

    # Rebuild searchable chunk
    sec["searchable_chunk"] = f"Administration of Criminal Justice Act, 2015 | {sec['part']} | {sec['section_number']}. {sec['section_title']} | {sec['full_text']}"

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("[✓] Cleaned Section 495 Schedule bleed and updated full margin titles.")
