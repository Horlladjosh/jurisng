import json
import re
from pathlib import Path
import fitz

PDF_PATH = Path("data/raw_pdfs/cybercrimes-act-2015.pdf")
JSON_PATH = Path("data/json_laws/cybercrimes_act_2015.json")

doc = fitz.open(str(PDF_PATH))
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

json_sections = {int(s["section_number"]): s for s in data["sections"]}
target_sections = [1, 7, 10, 13, 38, 59]

def clean(s):
    return s.replace('\xa0', ' ').replace('\xad', '').replace('\r', '').replace('\t', ' ').strip()

def get_raw_pdf_snippet(sec_num):
    for p_idx in range(4, len(doc)):
        txt = clean(doc[p_idx].get_text("text"))
        if re.search(rf'(?:^|\n)\s*{sec_num}\.?\s+', txt):
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            for i, line in enumerate(lines):
                if re.match(rf'^{sec_num}\.?\b', line):
                    snippet_lines = lines[max(0, i): min(len(lines), i + 10)]
                    return p_idx + 1, "\n".join(snippet_lines)
    return None, "Raw match not found"

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

print("\n" + "=" * 102)
print("CYBERCRIMES ACT, 2015: SIDE-BY-SIDE VERIFICATION")
print("=" * 102)

for sec_n in target_sections:
    sec = json_sections.get(sec_n)
    p_num, raw_snippet = get_raw_pdf_snippet(sec_n)
    
    json_repr = f"TITLE: {sec['section_title']}\n\n{sec['full_text']}"
    
    col1 = wrap_text(raw_snippet, 46)
    col2 = wrap_text(json_repr, 46)
    
    max_len = max(len(col1), len(col2))
    col1 += [""] * (max_len - len(col1))
    col2 += [""] * (max_len - len(col2))
    
    print(f"\nSECTION {sec_n:>2}  |  RAW PDF (Page {p_num}) vs CLEAN JSON")
    print("-" * 102)
    print(f"{'--- RAW PDF STREAM ---':<48} | {'--- PARSED JSON ---':<48}")
    print("-" * 102)
    
    preview_limit = min(max_len, 14)
    for i in range(preview_limit):
        print(f"{col1[i]:<48} | {col2[i]:<48}")
    
    if max_len > preview_limit:
        print(f"{'... [more lines in PDF] ...':<48} | {'... [more lines in JSON] ...':<48}")

print("\n" + "=" * 102)
