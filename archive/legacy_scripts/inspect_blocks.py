from pathlib import Path
import fitz

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
doc = fitz.open(str(PDF_PATH))
page = doc[20]

print(f"Page Width: {page.rect.width}, Height: {page.rect.height}\n")
print(f"{'X0':>6} {'Y0':>6} {'X1':>6} {'Y1':>6} | {'TEXT PREVIEW'}")
print("-" * 75)

# Extract blocks: (x0, y0, x1, y1, "text", block_no, block_type)
blocks = page.get_text("blocks")
for b in blocks:
    if b[6] == 0:  # text block
        preview = b[4].replace('\n', ' ')[:50]
        print(f"{b[0]:6.1f} {b[1]:6.1f} {b[2]:6.1f} {b[3]:6.1f} | {preview}")
