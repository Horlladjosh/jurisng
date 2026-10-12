import re
import json
import sys
from pathlib import Path
from pypdf import PdfReader

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.schema import Statute, Section


def extract_labour_act():
    pdf_path = Path("data/raw_pdfs/labour_act.pdf")
    output_path = Path("data/json_laws/labour_act.json")

    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found. Please run the download command first.")
        return

    print("Reading Labour Act PDF...")
    reader = PdfReader(str(pdf_path))
    pages = [p.extract_text() or "" for p in reader.pages]

    # --- 1. Extract TOC Titles ---
    toc_text = "\n".join(pages[:6])
    toc_matches = re.findall(r'(?:^|\n)\s*(\d{1,2})\s*\.\s+([A-Za-z][^\n\.]+)', toc_text)
    
    titles_map = {}
    for num_str, title in toc_matches:
        num = int(num_str)
        if 1 <= num <= 92 and num not in titles_map:
            titles_map[num] = title.strip()

    # --- 2. Process Body Text ---
    body_text = "\n".join(pages[3:])
    body_text = re.sub(r'LABOUR ACT\s*-\s*CAP\.?\s*L1\s*LFN\s*2004', '', body_text, flags=re.IGNORECASE)
    body_text = re.sub(r'LAWS OF THE FEDERATION OF NIGERIA', '', body_text, flags=re.IGNORECASE)

    section_spans = {}
    last_pos = 0

    for i in range(1, 93):
        num_str = str(i)
        pattern = re.compile(
            rf'(?:^|\n|[a-zA-Z]\s+|[\.\-—–]\s*)({num_str})\s*[\.\-—–]+(?:\s*[\{{\(\[]?\s*(?:\d+|[a-zA-Z]|I)\s*[\}}\)\]]?|\s+[A-Z])'
        )
        match = pattern.search(body_text, last_pos)
        if match:
            start_idx = match.start(1)
            section_spans[i] = start_idx
            last_pos = start_idx
        else:
            fb_pattern = re.compile(rf'(?:^|\n|[a-zA-Z]\s+|[\.\-—–]\s*)({num_str})\s*[\.\-—–]')
            fb_match = fb_pattern.search(body_text, last_pos)
            if fb_match:
                start_idx = fb_match.start(1)
                section_spans[i] = start_idx
                last_pos = start_idx

    print(f"Located {len(section_spans)} / 92 section boundaries in the text.")

    # --- 3. Slice and Construct ---
    sorted_nums = sorted(section_spans.keys())
    sections = []

    for idx, sec_num in enumerate(sorted_nums):
        start = section_spans[sec_num]
        if idx + 1 < len(sorted_nums):
            end = section_spans[sorted_nums[idx + 1]]
            raw_chunk = body_text[start:end].strip()
        else:
            raw_chunk = body_text[start:].strip()

        clean_chunk = re.sub(rf'^\d+\s*[\.\-—–]*\s*', '', raw_chunk).strip()

        subs = re.findall(r'(\([0-9a-zA-Z]+\)[\s\S]*?)(?=(?:\([0-9a-zA-Z]+\))|\Z)', clean_chunk)
        subsections = [s.strip() for s in subs if s.strip()]

        title = titles_map.get(sec_num, f"Section {sec_num}")
        search_chunk = f"Labour Act (Nigeria) | Section {sec_num}: {title} | {clean_chunk}"

        sec_obj = Section(
            section_number=str(sec_num),
            section_title=title,
            chapter=None,
            part=None,
            full_text=clean_chunk,
            subsections=subsections,
            searchable_chunk=search_chunk
        )
        sections.append(sec_obj)

    statute = Statute(
        statute_id="labour_act",
        statute_title="Labour Act (Chapter L1, Laws of the Federation of Nigeria 2004)",
        short_title="Labour Act",
        year=2004,
        total_sections_expected=92,
        sections=sections
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(statute.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"Extraction complete! Saved {len(sections)} sections to {output_path}")


if __name__ == "__main__":
    extract_labour_act()
