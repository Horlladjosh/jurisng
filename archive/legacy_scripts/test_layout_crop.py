from pathlib import Path
import fitz  # PyMuPDF

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")

if not PDF_PATH.exists():
    print(f"[!] File not found: {PDF_PATH}")
    exit(1)

doc = fitz.open(str(PDF_PATH))

# Page 21 (0-indexed: index 20) where Section 1 and Section 2 reside
page = doc[20]
rect = page.rect  # Page dimensions (width, height)

# 1. Bounding box for Main Body Column (X from 110 to right margin, Y between header and footer)
# rect: (x0, y0, x1, y1)
main_rect = fitz.Rect(110, 50, rect.width - 40, rect.height - 50)
clean_body_text = page.get_text("text", clip=main_rect)

# 2. Bounding box for Margin Column (X from 30 to 110)
margin_rect = fitz.Rect(30, 50, 110, rect.height - 50)
margin_notes = page.get_text("text", clip=margin_rect)

print("=" * 80)
print("1. CLEANED MAIN BODY TEXT (No Margin Bleed)")
print("=" * 80)
print(clean_body_text.strip()[:600])

print("\n" + "=" * 80)
print("2. ISOLATED MARGIN TITLES (Extracted Directly as Metadata)")
print("=" * 80)
print(margin_notes.strip())
print("=" * 80)
