import json
import re
from pathlib import Path
import fitz

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
OUT_PATH = Path("data/json_laws/acja_2015.json")

doc = fitz.open(str(PDF_PATH))

# ACJA substantive pages: Page 21 (index 20) to Page 197 (index 196)
START_PAGE = 20
END_PAGE = 197

# 1. First Pass: Read Arrangement of Sections (TOC) from pages 1-20 for official titles
toc_titles = {}
for p_idx in range(START_PAGE):
    page_text = doc[p_idx].get_text("text")
    for match in re.finditer(r'(?:^|\n)\s*([0-9]+)\.\s+([^\n\.]+)', page_text):
        sec_n = int(match.group(1))
        title = match.group(2).strip()
        if 1 <= sec_n <= 495 and sec_n not in toc_titles:
            toc_titles[sec_n] = title

print(f"[✓] Extracted {len(toc_titles)} / 495 official section titles from Arrangement of Sections.")

# 2. Second Pass: Extract Clean Main Column Text (excluding margins X > 500)
clean_body_pages = []

for p_idx in range(START_PAGE, min(END_PAGE, len(doc))):
    page = doc[p_idx]
    w, h = page.rect.width, page.rect.height
    
    # Bounding box for legal body: X in [40, 500], Y in [50, h-45] (skips running headers/footers)
    body_rect = fitz.Rect(40, 50, 500, h - 45)
    page_body = page.get_text("text", clip=body_rect)
    clean_body_pages.append(page_body)

full_statute_body = "\n".join(clean_body_pages)

# Normalize spaces while preserving structure
full_statute_body = re.sub(r'[ \t]+', ' ', full_statute_body)

# 3. Third Pass: Slice Sections by Number Markers (e.g. "\n1. ", "\n2. ")
sections = []
current_part = "PART 1 – PRELIMINARY"

# Find all section start boundaries
sec_starts = list(re.finditer(r'(?:^|\n)\s*([0-9]+)\.\s+', full_statute_body))

for i in range(len(sec_starts)):
    curr_match = sec_starts[i]
    sec_num = int(curr_match.group(1))
    
    # Ensure section numbers stay sequential (1 to 495)
    if not (1 <= sec_num <= 495):
        continue
        
    start_pos = curr_match.start()
    end_pos = sec_starts[i + 1].start() if i + 1 < len(sec_starts) else len(full_statute_body)
    
    sec_block = full_statute_body[start_pos:end_pos].strip()
    
    # Check for PART header transitions inside this slice
    part_match = re.search(r'\n\s*(PART\s+[0-9IVXLCDM]+\s*[-–—][^\n]+)', sec_block, re.IGNORECASE)
    if part_match:
        # Update Part context
        current_part = part_match.group(1).strip()
        # Cut trailing part text from the current section's body
        sec_block = sec_block[:part_match.start()].strip()

    title = toc_titles.get(sec_num, f"Section {sec_num}")
    
    # Clean whitespace in section text
    clean_text = re.sub(r'\n\s*\n+', '\n\n', sec_block).strip()

    sections.append({
        "section_number": str(sec_num),
        "section_title": title,
        "part": current_part,
        "full_text": clean_text,
        "searchable_chunk": f"Administration of Criminal Justice Act, 2015 | {current_part} | {sec_num}. {title} | {clean_text}"
    })

# Deduplicate in case of sub-clause numbering collisions
unique_sections = {int(s["section_number"]): s for s in sections}
final_sections = [unique_sections[k] for k in sorted(unique_sections.keys())]

out_data = {
    "statute_id": "ng-act-2015-acja",
    "short_title": "Administration of Criminal Justice Act, 2015",
    "year": 2015,
    "jurisdiction": "Federal Republic of Nigeria",
    "total_sections": len(final_sections),
    "sections": final_sections
}

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2, ensure_ascii=False)

print("=" * 80)
print(f"[✓] Spatial Parsing Complete!")
print(f"    Total Extracted Sections: {len(final_sections)} / 495")
print(f"    Output: {OUT_PATH}")
print("=" * 80)
