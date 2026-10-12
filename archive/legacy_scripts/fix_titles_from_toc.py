import json
import re
from pathlib import Path
import fitz

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
DATA_PATH = Path("data/json_laws/acja_2015.json")

doc = fitz.open(str(PDF_PATH))

# 1. Extract official titles from the TOC (Pages 1 to 20 / index 0 to 19)
toc_text = ""
for p_idx in range(20):
    toc_text += doc[p_idx].get_text("text") + "\n"

# Match patterns like: "6. Notification of cause of arrest and rights of suspect."
toc_dict = {}
# Clean up dot leaders and page numbers from TOC lines
lines = toc_text.split("\n")
for line in lines:
    line_clean = line.strip()
    m = re.match(r'^([0-9]{1,3})\.\s+(.+)', line_clean)
    if m:
        sec_num = int(m.group(1))
        # Remove trailing page numbers, dots, and whitespace
        title_raw = m.group(2)
        title_clean = re.sub(r'[\.\s\-_]+[0-9]+$', '', title_raw).strip()
        title_clean = re.sub(r'[\.]{2,}', '', title_clean).strip()
        if 1 <= sec_num <= 495 and sec_num not in toc_dict:
            toc_dict[sec_num] = title_clean

print(f"[✓] Extracted {len(toc_dict)} / 495 authoritative titles from Arrangement of Sections.")

# 2. Update JSON with clean TOC titles
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

for sec in data["sections"]:
    sec_num = int(sec["section_number"])
    if sec_num in toc_dict and len(toc_dict[sec_num]) > 2:
        sec["section_title"] = toc_dict[sec_num].rstrip('.')
    # Rebuild searchable chunk
    sec["searchable_chunk"] = f"Administration of Criminal Justice Act, 2015 | {sec['part']} | {sec['section_number']}. {sec['section_title']} | {sec['full_text']}"

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("[✓] Updated acja_2015.json with official titles.")
