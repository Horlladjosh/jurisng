import json
import re
from pathlib import Path
import fitz

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
DATA_PATH = Path("data/json_laws/acja_2015.json")

doc = fitz.open(str(PDF_PATH))

# 1. Collect all non-empty lines from TOC pages (Pages 1 to 20 / index 0 to 19)
toc_lines = []
for p_idx in range(20):
    text = doc[p_idx].get_text("text")
    for line in text.split("\n"):
        l = line.strip()
        if l:
            toc_lines.append(l)

# 2. Extract section number -> title mapping
toc_dict = {}
i = 0
while i < len(toc_lines):
    line = toc_lines[i]
    
    # Check if line is purely a section number
    if line.isdigit():
        sec_num = int(line)
        if 1 <= sec_num <= 495:
            # Look ahead for title lines
            j = i + 1
            title_parts = []
            while j < len(toc_lines):
                next_l = toc_lines[j]
                
                # Stop if we hit the next section number
                if next_l.isdigit() and int(next_l) == sec_num + 1:
                    break
                if next_l.isdigit():
                    break
                    
                # Skip standalone PART headers in the title extraction
                if re.match(r'^PART\s+[0-9IVXLCDM]+\b', next_l, re.IGNORECASE):
                    j += 1
                    continue
                    
                # Skip running headers
                if "ADMINISTRATION OF CRIMINAL JUSTICE ACT" in next_l or next_l == "Section:" or next_l == "ARRANGEMENT OF SECTIONS":
                    j += 1
                    continue
                    
                title_parts.append(next_l)
                j += 1
                
                # Most titles are 1 or 2 lines
                if len(title_parts) >= 2 and (title_parts[-1].endswith('.') or j < len(toc_lines) and toc_lines[j].isdigit()):
                    break

            if title_parts:
                full_title = " ".join(title_parts).strip().rstrip('.')
                if sec_num not in toc_dict:
                    toc_dict[sec_num] = full_title
            i = j - 1
    i += 1

print(f"[✓] Successfully extracted {len(toc_dict)} / 495 official titles from the Table of Contents!")

# 3. Update the existing clean body JSON dataset
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

for sec in data["sections"]:
    sec_num = int(sec["section_number"])
    if sec_num in toc_dict:
        sec["section_title"] = toc_dict[sec_num]
    
    # Rebuild search chunk
    sec["searchable_chunk"] = f"Administration of Criminal Justice Act, 2015 | {sec['part']} | {sec['section_number']}. {sec['section_title']} | {sec['full_text']}"

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"[✓] Updated {DATA_PATH} with official titles.")
