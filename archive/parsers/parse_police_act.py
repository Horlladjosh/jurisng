import re
import json
import sys
from pathlib import Path
from pypdf import PdfReader

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.schema import Statute, Section


def normalize_gazette_text(text: str) -> str:
    # 1. Clean repetitive Gazette headers and footers
    text = re.sub(r'A\s*\d+\s+\d{4}\s+No\.\s*\d+\s+Nigeria Police Act,?\s*\d*', '', text)
    text = re.sub(r'Nigeria Police Act,?\s*\d*\s*\d{4}\s+No\.\s*\d*', '', text)
    text = re.sub(r'202[01]\s+No\.\s*2\s+Nigeria Police Act,?\s*\d*', '', text)

    # 2. Fix specific font encoding bugs on Page 63
    text = re.sub(r'\b1211\s*\.\s*--', '128.--', text)
    text = re.sub(r'\b1311\s*\.\s*--', '130.--', text)

    # 3. Fix OCR glyph swaps for 1
    text = re.sub(r'\bI\s*(\d{2})\b', r'1\1', text)
    text = re.sub(r'\bI\s*(\d)\s*([\.\-—–])', r'1\1\2', text)

    # 4. Collapse split digits before dots/dashes
    text = re.sub(r'(\d)\s+(\d)\s+(\d)(?=[\s\.\-—–])', r'\1\2\3', text)
    text = re.sub(r'(\d)\s+(\d)(?=[\s\.\-—–])', r'\1\2', text)

    return text


def extract_police_act():
    pdf_path = Path("data/raw_pdfs/police_act_2020.pdf")
    output_path = Path("data/json_laws/police_act_2020.json")

    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found.")
        return

    print("Reading Police Act PDF...")
    reader = PdfReader(str(pdf_path))
    pages = [p.extract_text() or "" for p in reader.pages]

    # --- 1. Extract TOC Titles ---
    toc_text = normalize_gazette_text("\n".join(pages[:8]))
    toc_matches = re.findall(r'(?:^|\n)\s*(\d{1,3})\s*\.\s+([A-Za-z][^\n\.]+)', toc_text)

    titles_map = {}
    for num_str, title in toc_matches:
        num = int(num_str)
        if 1 <= num <= 142 and num not in titles_map:
            titles_map[num] = title.strip()

    # Manual fallback for titles if TOC truncated
    titles_map.setdefault(128, "Discipline")
    titles_map.setdefault(130, "Instruction of traffic warden")

    # --- 2. Process Body Text ---
    body_text = normalize_gazette_text("\n".join(pages[6:]))

    section_spans = {}
    last_pos = 0

    for i in range(1, 143):
        num_str = str(i)
        num_pattern = r'\s*'.join(list(num_str))

        # Look for section marker
        pattern = re.compile(
            rf'(?:^|\n|[a-zA-Z]\s+|[\.\-—–]\s*)({num_pattern})\s*[\.\-—–]+(?:\s*[\{{\(\[]?\s*(?:\d+|[a-zA-Z]|I)\s*[\}}\)\]]?|\s+[A-Z])'
        )
        match = pattern.search(body_text, last_pos)
        if match:
            start_idx = match.start(1)
            section_spans[i] = start_idx
            last_pos = start_idx
        else:
            fb_pattern = re.compile(rf'(?:^|\n|[a-zA-Z]\s+|[\.\-—–]\s*)({num_pattern})\s*[\.\-—–]')
            fb_match = fb_pattern.search(body_text, last_pos)
            if fb_match:
                start_idx = fb_match.start(1)
                section_spans[i] = start_idx
                last_pos = start_idx

    print(f"Located {len(section_spans)} / 142 section boundaries in the text.")

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
        search_chunk = f"Nigeria Police Act 2020 | Section {sec_num}: {title} | {clean_chunk}"

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
        statute_id="police_act_2020",
        statute_title="Nigeria Police Act 2020",
        short_title="Police Act 2020",
        year=2020,
        total_sections_expected=142,
        sections=sections
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(statute.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"Extraction complete! Saved {len(sections)} sections to {output_path}")


if __name__ == "__main__":
    extract_police_act()
