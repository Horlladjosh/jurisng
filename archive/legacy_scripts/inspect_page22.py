from pathlib import Path
import fitz

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
doc = fitz.open(str(PDF_PATH))
page = doc[21]  # Page 22

print(f"Page 22 Width: {page.rect.width}\n")
print(f"{'X0':>6} {'Y0':>6} {'X1':>6} {'Y1':>6} | {'TEXT PREVIEW'}")
print("-" * 75)

for b in page.get_text("blocks"):
    if b[6] == 0:
        preview = b[4].replace('\n', ' ')[:50]
        print(f"{b[0]:6.1f} {b[1]:6.1f} {b[2]:6.1f} {b[3]:6.1f} | {preview}")
