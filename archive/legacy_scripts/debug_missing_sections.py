from pathlib import Path
import fitz
import re

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
doc = fitz.open(str(PDF_PATH))
print(f"Total Document Pages: {len(doc)}")

targets = [39, 210, 360, 437, 495]

for p_idx in range(20, len(doc)):
    page = doc[p_idx]
    blocks = page.get_text("blocks")
    for b in blocks:
        text = b[4].strip()
        for t in targets:
            if re.search(rf'(?:^|\n)\s*{t}\.\s+', text):
                print(f"Section {t:>3} found on Page {p_idx+1:>3} (index {p_idx}): x0={b[0]:.1f}, y0={b[1]:.1f} | Text: '{text.replace(chr(10), ' ')[:60]}'")
