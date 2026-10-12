import re
from pathlib import Path
from pypdf import PdfReader

for name, path in [("Health Act", "data/raw_pdfs/national-health-act-2014.pdf"), ("FCCPA", "data/raw_pdfs/fccpa-2018.pdf")]:
    p = Path(path)
    if not p.exists():
        continue
    reader = PdfReader(str(p))
    # Combine first 10 pages
    sample = "\n".join(page.extract_text() or "" for page in reader.pages[2:8])
    print(f"\n{'='*55}\nLAYOUT SNIPPET: {name}\n{'='*55}")
    # Print lines containing digits followed by words
    lines = [line for line in sample.split("\n") if re.search(r'\b\d{1,3}\b', line)]
    for l in lines[:15]:
        print(f"  > {repr(l)}")
