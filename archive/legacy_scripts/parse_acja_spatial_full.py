import json
import re
from pathlib import Path
import fitz

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
OUT_PATH = Path("data/json_laws/acja_2015.json")

doc = fitz.open(str(PDF_PATH))

START_PAGE = 20  # Page 21
END_PAGE = 231   # Page 231 (Section 495 is here)

current_part = "PART 1 – PRELIMINARY"
all_body_blocks = []
margin_titles = {}

for p_idx in range(START_PAGE, END_PAGE + 1):
    page = doc[p_idx]
    blocks = page.get_text("blocks")
    blocks.sort(key=lambda b: (b[1], b[0]))
    
    for b in blocks:
        if b[6] != 0:  # Skip image blocks
            continue
        
        x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4].strip()
        if not text:
            continue
            
        # 1. Update PART heading context
        if x0 < 450 and re.match(r'^PART\s+[0-9IVXLCDM]+\s*[-–—]', text, re.IGNORECASE):
            current_part = text.replace('\n', ' ').strip()
            continue

        # 2. Extract Margin Titles (X0 >= 500)
        if x0 >= 500:
            title_clean = text.replace('\n', ' ').strip()
            margin_titles.setdefault(p_idx, []).append((y0, y1, title_clean))
            continue
            
        # 3. Main column text (X0 < 500 and within header/footer bounds)
        if y0 >= 45 and y1 <= page.rect.height - 40:
            all_body_blocks.append({
                "page": p_idx,
                "x0": x0,
                "y0": y0,
                "text": text,
                "part": current_part
            })

# Stitch body stream while tracking exact section start locations
full_text_stream = ""
section_positions = []

for blk in all_body_blocks:
    txt = blk["text"]
    
    # Match any section number at line start or block start
    for m in re.finditer(r'(?:^|\n)\s*([0-9]{1,3})\.\s+', txt):
        sec_n = int(m.group(1))
        if 1 <= sec_n <= 495:
            # Approximate character offset in the stitched stream
            pos = len(full_text_stream) + m.start()
            section_positions.append({
                "sec_num": sec_n,
                "pos": pos,
                "page": blk["page"],
                "y0": blk["y0"],
                "part": blk["part"]
            })
            
    full_text_stream += txt + "\n\n"

# Sort and deduplicate section start positions sequentially
section_positions.sort(key=lambda s: s["pos"])

# Keep the earliest valid occurrence for each section number 1..495
filtered_positions = []
expected = 1

for pos_info in section_positions:
    if pos_info["sec_num"] == expected:
        filtered_positions.append(pos_info)
        expected += 1

print(f"[i] Located {len(filtered_positions)} / 495 sequential section boundaries in main column.")

# Slice sections
extracted_sections = []
for i in range(len(filtered_positions)):
    curr = filtered_positions[i]
    sec_n = curr["sec_num"]
    start_pos = curr["pos"]
    end_pos = filtered_positions[i+1]["pos"] if i + 1 < len(filtered_positions) else len(full_text_stream)
    
    sec_text = full_text_stream[start_pos:end_pos].strip()
    
    # Strip any trailing PART header from the substantive text
    part_match = re.search(r'\n\s*(PART\s+[0-9IVXLCDM]+\s*[-–—][^\n]+)', sec_text, re.IGNORECASE)
    if part_match:
        sec_text = sec_text[:part_match.start()].strip()

    # Match closest margin title from the same page
    p_idx = curr["page"]
    page_margins = margin_titles.get(p_idx, [])
    best_title = f"Section {sec_n}"
    
    if page_margins:
        closest = min(page_margins, key=lambda m: abs(m[0] - curr["y0"]))
        if abs(closest[0] - curr["y0"]) <= 70:
            best_title = closest[2]

    # Normalize whitespace
    sec_text = re.sub(r'[ \t]+', ' ', sec_text)
    sec_text = re.sub(r'\n\s*\n+', '\n\n', sec_text).strip()

    extracted_sections.append({
        "section_number": str(sec_n),
        "section_title": best_title,
        "part": curr["part"],
        "full_text": sec_text,
        "searchable_chunk": f"Administration of Criminal Justice Act, 2015 | {curr['part']} | {sec_n}. {best_title} | {sec_text}"
    })

out_data = {
    "statute_id": "ng-act-2015-acja",
    "short_title": "Administration of Criminal Justice Act, 2015",
    "year": 2015,
    "jurisdiction": "Federal Republic of Nigeria",
    "total_sections": len(extracted_sections),
    "sections": extracted_sections
}

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2, ensure_ascii=False)

print("=" * 80)
print("SPATIAL BOUNDING-BOX PARSING SUMMARY")
print("=" * 80)
print(f"Total Extracted Sections: {len(extracted_sections)} / 495")
missing = [i for i in range(1, 496) if i not in [int(s['section_number']) for s in extracted_sections]]
if missing:
    print(f"[!] Missing sections: {missing}")
else:
    print("[✓] SUCCESS: All 495 sections extracted cleanly with spatial geometry!")
print("=" * 80)
