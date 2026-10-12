import re
import json
import sys
from pathlib import Path
from pypdf import PdfReader

# Add root directory to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.schema import Statute, Section


def extract_cfrn():
    pdf_path = Path("data/raw_pdfs/cfrn_1999.pdf")
    output_path = Path("data/json_laws/cfrn_1999.json")

    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found. Please run the download command first.")
        return

    print("Reading PDF...")
    reader = PdfReader(str(pdf_path))
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    print("Extracting sections...")
    # Normalize multiple whitespaces/tabs but preserve newlines
    cleaned_text = re.sub(r'Constitution of the Federal Republic of Nigeria\s*\d*', '', full_text)
    
    # Enhanced pattern: handles optional hyphens, spaces, and newline-wrapped titles
    # e.g., "101. Regulation...", "101. - Regulation...", or "101.\nRegulation..."
    section_pattern = re.compile(
        r'\n(?P<num>\d{1,3})\.\s*(?:-\s*)?(?P<title>[A-Za-z][^\n]+)\n(?P<body>[\s\S]*?)(?=(?:\n\d{1,3}\.\s*(?:-\s*)?[A-Za-z][^\n]+\n)|\Z)'
    )
    
    matches = list(section_pattern.finditer(cleaned_text))
    print(f"Found {len(matches)} potential section matches.")

    sections_dict = {}

    for m in matches:
        sec_num_str = m.group("num").strip()
        sec_num = int(sec_num_str)
        
        # Valid sections in CFRN 1999 are 1 to 320
        if sec_num < 1 or sec_num > 320:
            continue

        sec_title = m.group("title").strip()
        body = m.group("body").strip()

        # If we encounter a duplicate match, prefer the longer body (avoids TOC hits)
        if sec_num in sections_dict:
            if len(body) <= len(sections_dict[sec_num].full_text):
                continue

        # Extract subsections
        subsections = re.findall(r'(\(\d+\)[\s\S]*?)(?=(?:\(\d+\))|\Z)', body)
        cleaned_subs = [s.strip() for s in subsections if s.strip()]

        chunk = (
            f"Constitution of the Federal Republic of Nigeria 1999 | "
            f"Section {sec_num}: {sec_title} | {body}"
        )

        section_obj = Section(
            section_number=str(sec_num),
            section_title=sec_title,
            chapter=None,
            part=None,
            full_text=body,
            subsections=cleaned_subs,
            searchable_chunk=chunk
        )
        sections_dict[sec_num] = section_obj

    sections = [sections_dict[k] for k in sorted(sections_dict.keys())]

    statute = Statute(
        statute_id="cfrn_1999",
        statute_title="Constitution of the Federal Republic of Nigeria 1999 (as amended)",
        short_title="CFRN 1999",
        year=1999,
        total_sections_expected=320,
        sections=sections
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(statute.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"Extraction complete! Saved {len(sections)} unique sections to {output_path}")


if __name__ == "__main__":
    extract_cfrn()
