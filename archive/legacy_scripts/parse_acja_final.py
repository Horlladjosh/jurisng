import json
import re
from pathlib import Path
import fitz

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
OUT_PATH = Path("data/json_laws/acja_2015.json")

doc = fitz.open(str(PDF_PATH))

START_PAGE = 20  # Page 21 (0-indexed)
END_PAGE = 231   # Page 231

# 1. First pass: Collect all margin titles with vertical positions per page
margin_titles = {}
page_bodies = []
current_part = "PART 1 – PRELIMINARY"

for p_idx in range(START_PAGE, END_PAGE + 1):
    page = doc[p_idx]
    blocks = page.get_text("blocks")
    blocks.sort(key=lambda b: (b[1], b[0]))
    
    page_text_blocks = []
    
    for b in blocks:
        if b[6] != 0:
            continue
        
        x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4].strip()
        if not text:
            continue
            
        # Track PART headers
        if x0 < 450 and re.match(r'^PART\s+[0-9IVXLCDM]+\s*[-–—]', text, re.IGNORECASE):
            current_part = text.replace('\n', ' ').strip()
            continue

        # Marginal side notes (X0 >= 500)
        if x0 >= 500:
            title_clean = text.replace('\n', ' ').strip()
            margin_titles.setdefault(p_idx, []).append((y0, title_clean))
            continue
            
        # Substantive Main Column (X0 < 500, skipping headers/footers)
        if y0 >= 45 and y1 <= page.rect.height - 40:
            page_text_blocks.append((x0, y0, text, current_part, p_idx))
            
    page_bodies.append(page_text_blocks)

# 2. Build full sequence of all substantive blocks
all_blocks = [blk for p_blocks in page_bodies for blk in p_blocks]

# 3. Locate each section 1..495 in order
section_indices = []

for sec_n in range(1, 496):
    pattern = rf'(?:^|\n)\s*{sec_n}\.?\s+'
    found = False
    
    # Search forward through blocks starting from the last found position
    start_search_idx = section_indices[-1]["blk_idx"] if section_indices else 0
    
    for idx in range(start_search_idx, len(all_blocks)):
        blk = all_blocks[idx]
        txt = blk[2]
        
        m = re.search(pattern, txt)
        if m:
            section_indices.append({
                "sec_num": sec_n,
                "blk_idx": idx,
                "match_start": m.start(),
                "x0": blk[0],
                "y0": blk[1],
                "part": blk[3],
                "page": blk[4]
            })
            found = True
            break
            
    if not found:
        print(f"[!] Warning: Section {sec_n} not found!")

print(f"[i] Located {len(section_indices)} / 495 sections across document blocks.")

# 4. Extract section texts between boundaries
extracted_sections = []

for i in range(len(section_indices)):
    curr = section_indices[i]
    sec_n = curr["sec_num"]
    curr_blk_idx = curr["blk_idx"]
    
    if i + 1 < len(section_indices):
        next_sec = section_indices[i + 1]
        next_blk_idx = next_sec["blk_idx"]
        next_start = next_sec["match_start"]
    else:
        next_blk_idx = len(all_blocks) - 1
        next_start = len(all_blocks[-1][2])
        
    # Gather text between curr_blk_idx and next_blk_idx
    if curr_blk_idx == next_blk_idx:
        sec_raw = all_blocks[curr_blk_idx][2][curr["match_start"]:next_start]
    else:
        chunks = [all_blocks[curr_blk_idx][2][curr["match_start"]:]]
        for b_i in range(curr_blk_idx + 1, next_blk_idx):
            chunks.append(all_blocks[b_i][2])
        if next_blk_idx < len(all_blocks):
            chunks.append(all_blocks[next_blk_idx][2][:next_start])
        sec_raw = "\n\n".join(chunks)

    # Clean whitespace and strip stray Part header from text body
    sec_raw = re.sub(r'\n\s*(PART\s+[0-9IVXLCDM]+\s*[-–—][^\n]+)', '', sec_raw, flags=re.IGNORECASE)
    sec_text = re.sub(r'[ \t]+', ' ', sec_raw)
    sec_text = re.sub(r'\n\s*\n+', '\n\n', sec_text).strip()

    # Match closest margin title on the page
    p_idx = curr["page"]
    page_margins = margin_titles.get(p_idx, [])
    best_title = f"Section {sec_n}"
    
    if page_margins:
        closest = min(page_margins, key=lambda m: abs(m[0] - curr["y0"]))
        if abs(closest[0] - curr["y0"]) <= 80:
            best_title = closest[1]

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
print(f"[✓] SUCCESS: Total Extracted Sections: {len(extracted_sections)} / 495")
print(f"    Saved to: {OUT_PATH}")
print("=" * 80)
