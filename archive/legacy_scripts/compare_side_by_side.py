import json
import re
from pathlib import Path
import fitz

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
JSON_PATH = Path("data/json_laws/acja_2015.json")

doc = fitz.open(str(PDF_PATH))
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

json_sections = {int(s["section_number"]): s for s in data["sections"]}

# Test sections across different parts
target_sections = [1, 6, 39, 110, 306, 495]

def get_raw_pdf_snippet(sec_num):
    # Find page containing the section
    for p_idx in range(20, 232):
        txt = doc[p_idx].get_text("text")
        if re.search(rf'(?:^|\n)\s*{sec_num}\.?\s+', txt):
            # Extract roughly 12 lines from that match
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            for i, line in enumerate(lines):
                if re.match(rf'^{sec_num}\.?\b', line):
                    snippet_lines = lines[max(0, i - 1): min(len(lines), i + 10)]
                    return p_idx + 1, "\n".join(snippet_lines)
    return None, "Not found in raw search"

def wrap_text(text, width=46):
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split()
        cur_line = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 > width:
                lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_len = len(w)
            else:
                cur_line.append(w)
                cur_len += len(w) + 1
        if cur_line:
            lines.append(" ".join(cur_line))
    return lines

for sec_n in target_sections:
    sec = json_sections.get(sec_n)
    p_num, raw_snippet = get_raw_pdf_snippet(sec_n)
    
    json_repr = f"TITLE: {sec['section_title']}\nPART : {sec['part']}\n\n{sec['full_text']}"
    
    col1 = wrap_text(raw_snippet, 46)
    col2 = wrap_text(json_repr, 46)
    
    max_len = max(len(col1), len(col2))
    col1 += [""] * (max_len - len(col1))
    col2 += [""] * (max_len - len(col2))
    
    print("\n" + "=" * 102)
    print(f"SECTION {sec_n:>3}  |  RAW PDF (Page {p_num}) vs CLEAN JSON")
    print("=" * 102)
    print(f"{'--- RAW PDF (Raw Column Stream) ---':<48} | {'--- CLEAN JSON (Parsed & Normalized) ---':<48}")
    print("-" * 102)
    
    # Print up to first 18 lines per preview
    preview_limit = min(max_len, 16)
    for i in range(preview_limit):
        print(f"{col1[i]:<48} | {col2[i]:<48}")
    
    if max_len > preview_limit:
        print(f"{'... [more lines in PDF] ...':<48} | {'... [more lines in JSON] ...':<48}")

print("\n" + "=" * 102)
