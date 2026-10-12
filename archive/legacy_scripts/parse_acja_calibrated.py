import json
import re
from pathlib import Path
import fitz

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
OUT_PATH = Path("data/json_laws/acja_2015.json")

doc = fitz.open(str(PDF_PATH))

START_PAGE = 20  # Page 21 (0-indexed)
END_PAGE = 197   # Schedule starts around page 197

# Structure to collect all extracted sections
sections_dict = {}
current_part = "PART 1 – PRELIMINARY"

# Collect all substantive text blocks with spatial coordinates
all_body_blocks = []
margin_titles = {}

for p_idx in range(START_PAGE, min(END_PAGE, len(doc))):
    page = doc[p_idx]
    blocks = page.get_text("blocks")
    
    # Sort blocks top-to-bottom
    blocks.sort(key=lambda b: (b[1], b[0]))
    
    for b in blocks:
        if b[6] != 0:  # skip image blocks
            continue
        
        x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4].strip()
        if not text:
            continue
            
        # 1. Check for PART headings in the main column
        if 40 <= x0 <= 250 and re.match(r'^PART\s+[0-9IVXLCDM]+\s*[-–—]', text, re.IGNORECASE):
            current_part = text.replace('\n', ' ').strip()
            continue

        # 2. Check for Margin Titles (X0 >= 500)
        if x0 >= 500:
            # Associate margin title with page and vertical position Y0
            # Clean up linebreaks in title
            title_clean = text.replace('\n', ' ').strip()
            margin_titles.setdefault(p_idx, []).append((y0, y1, title_clean))
            continue
            
        # 3. Main column text (X0 < 500 and within Y boundaries)
        if y0 >= 45 and y1 <= page.rect.height - 40:
            all_body_blocks.append({
                "page": p_idx,
                "x0": x0,
                "y0": y0,
                "text": text,
                "part": current_part
            })

# Reconstruct full text and track section starts
full_text_stream = ""
section_positions = []

for blk in all_body_blocks:
    txt = blk["text"]
    
    # Check if this block starts a new section (starts at left margin x0 <= 55 with "N.")
    m = re.match(r'^([0-9]{1,3})\.\s+', txt)
    if m and blk["x0"] <= 55:
        sec_n = int(m.group(1))
        if 1 <= sec_n <= 495:
            section_positions.append({
                "sec_num": sec_n,
                "pos": len(full_text_stream),
                "page": blk["page"],
                "y0": blk["y0"],
                "part": blk["part"]
            })
            
    full_text_stream += txt + "\n\n"

# Slice contiguous sections
extracted_sections = []
for i in range(len(section_positions)):
    curr = section_positions[i]
    sec_n = curr["sec_num"]
    start_pos = curr["pos"]
    end_pos = section_positions[i+1]["pos"] if i + 1 < len(section_positions) else len(full_text_stream)
    
    sec_text = full_text_stream[start_pos:end_pos].strip()
    
    # Match the closest margin title on the same page around Y0
    p_idx = curr["page"]
    page_margins = margin_titles.get(p_idx, [])
    best_title = f"Section {sec_n}"
    
    if page_margins:
        # Find the margin title closest to curr["y0"]
        closest = min(page_margins, key=lambda m: abs(m[0] - curr["y0"]))
        # Only accept if within a reasonable vertical range (within 60pt)
        if abs(closest[0] - curr["y0"]) <= 60:
            best_title = closest[2]

    # Clean whitespace
    sec_text = re.sub(r'[ \t]+', ' ', sec_text)
    sec_text = re.sub(r'\n\s*\n+', '\n\n', sec_text).strip()

    extracted_sections.append({
        "section_number": str(sec_n),
        "section_title": best_title,
        "part": curr["part"],
        "full_text": sec_text,
        "searchable_chunk": f"Administration of Criminal Justice Act, 2015 | {curr['part']} | {sec_n}. {best_title} | {sec_text}"
    })

# Deduplicate
unique_map = {}
for s in extracted_sections:
    num = int(s["section_number"])
    if num not in unique_map or len(s["full_text"]) > len(unique_map[num]["full_text"]):
        unique_map[num] = s

final_list = [unique_map[k] for k in sorted(unique_map.keys())]

out_data = {
    "statute_id": "ng-act-2015-acja",
    "short_title": "Administration of Criminal Justice Act, 2015",
    "year": 2015,
    "jurisdiction": "Federal Republic of Nigeria",
    "total_sections": len(final_list),
    "sections": final_list
}

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2, ensure_ascii=False)

print("=" * 80)
print(f"[✓] Spatial Extraction Results:")
print(f"    Total Unique Sections: {len(final_list)} / 495")
missing = [i for i in range(1, 496) if i not in unique_map]
if missing:
    print(f"    Missing Sections ({len(missing)}): {missing[:20]}...")
else:
    print("    [✓] ALL 495 SECTIONS EXTRACTED!")
print("=" * 80)
