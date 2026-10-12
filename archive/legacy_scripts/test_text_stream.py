from pathlib import Path
from pypdf import PdfReader

files = {
    "Money Laundering": "data/raw_pdfs/money-laundering-act-2011.pdf",
    "National Health Act": "data/raw_pdfs/national-health-act-2014.pdf",
    "FCCPA 2018": "data/raw_pdfs/fccpa-2018.pdf"
}

for name, path in files.items():
    p = Path(path)
    if not p.exists():
        continue
    reader = PdfReader(str(p))
    total_text = "".join(page.extract_text() or "" for page in reader.pages)
    print(f"[{name}] Total Pages: {len(reader.pages):<3} | Total Extracted Characters: {len(total_text):,}")
    if len(total_text) > 0:
        print(f"   Preview Page 1 text snippet:\n   {repr(total_text[:200])}\n")
