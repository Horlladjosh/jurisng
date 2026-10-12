import json
import re
import sys
from pathlib import Path
import fitz

def clean_text(s):
    if not s:
        return ""
    s = s.replace('\xa0', ' ').replace('\xad', '').replace('\r', '').replace('\t', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()

class UniversalGazetteParser:
    def __init__(self, pdf_path, statute_id, short_title, year, jurisdiction="Federal Republic of Nigeria"):
        self.pdf_path = Path(pdf_path)
        self.statute_id = statute_id
        self.short_title = short_title
        self.year = year
        self.jurisdiction = jurisdiction
        self.doc = fitz.open(str(self.pdf_path))
        self.total_pages = len(self.doc)

    def find_start_page(self):
        for p_idx in range(min(25, self.total_pages)):
            txt = clean_text(self.doc[p_idx].get_text("text"))
            if "ARRANGEMENT OF SECTIONS" in txt.upper() or "EXPLANATORY MEMORANDUM" in txt.upper():
                continue
            if re.search(r'(?:^|\n)\s*1\.\s+', txt):
                return p_idx
        return 4

    def extract_toc_titles(self, start_sec_page):
        toc_dict = {}
        full_toc = ""
        for p_idx in range(start_sec_page):
            full_toc += self.doc[p_idx].get_text("text") + "\n"
            
        lines = [clean_text(l) for l in full_toc.split("\n") if clean_text(l)]
        i = 0
        while i < len(lines):
            line = lines[i]
            m = re.match(r'^([0-9]{1,3})\.?\s*(.*)', line)
            if m:
                sec_num = int(m.group(1))
                title_cand = m.group(2).strip()
                if not title_cand and i + 1 < len(lines):
                    i += 1
                    title_cand = lines[i]
                
                while i + 1 < len(lines):
                    nxt = lines[i + 1]
                    if re.match(r'^[0-9]{1,3}\.?', nxt) or re.match(r'^PART\s+[0-9IVXLCDM]+\b', nxt, re.IGNORECASE) or "ARRANGEMENT" in nxt.upper() or "SECTION:" in nxt.upper():
                        break
                    title_cand += " " + nxt
                    i += 1
                    if len(title_cand) > 100 or title_cand.endswith('.'):
                        break

                title_clean = re.sub(r'[\.\s\-_]+[0-9]+$', '', title_cand).strip().rstrip('.')
                if 1 <= sec_num <= 600 and sec_num not in toc_dict and len(title_clean) > 2:
                    toc_dict[sec_num] = title_clean
            i += 1
        return toc_dict

    def parse(self, output_path=None):
        start_page = self.find_start_page()
        print("=" * 80)
        print(f"INGESTION RUNNER: {self.short_title}")
        print(f"Total Pages: {self.total_pages} | Substantive Text Starts: Page {start_page + 1}")
        print("=" * 80)
        
        toc_titles = self.extract_toc_titles(start_page)
        total_expected = max(toc_titles.keys()) if toc_titles else 59
        print(f"[✓] Extracted {len(toc_titles)} titles from Table of Contents (Max Section: {total_expected}).")

        sample_page = self.doc[start_page]
        margin_x_threshold = sample_page.rect.width * 0.82
        page_height = sample_page.rect.height

        # 1. Collect all substantive text blocks
        substantive_stream = []
        current_part = "PART I - OBJECT AND APPLICATION"

        for p_idx in range(start_page, self.total_pages):
            page = self.doc[p_idx]
            blocks = page.get_text("blocks")
            blocks.sort(key=lambda b: (b[1], b[0]))
            
            for b in blocks:
                if b[6] != 0: continue
                x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], clean_text(b[4])
                if not text: continue
                
                # Check for schedules at end
                if p_idx > self.total_pages * 0.7 and re.match(r'^(FIRST|SECOND|THIRD|FOURTH)?\s*SCHEDULE\b', text, re.IGNORECASE):
                    break
                
                # Part track
                if x0 < margin_x_threshold and re.match(r'^PART\s+[0-9IVXLCDM]+\s*[-–—]', text, re.IGNORECASE):
                    current_part = text
                    continue

                is_pure_margin = (x0 >= margin_x_threshold)
                is_in_bounds_y = (y0 >= 45 and y1 <= (page_height - 35))

                if not is_pure_margin and is_in_bounds_y:
                    if not (re.match(r'^[A-Z\s,0-9\(\)\.\-]+$', text) and len(text) > 15 and ("ACT" in text or "GAZETTE" in text or "BILL" in text)):
                        substantive_stream.append((text, current_part, p_idx))

        # Join full document stream
        doc_full_text = "\n\n".join([item[0] for item in substantive_stream])

        # 2. Match each section individually
        section_locations = {}

        for sec_n in range(1, total_expected + 1):
            pattern = re.compile(rf'(?:^|\n)\s*{sec_n}\.?\s+', re.MULTILINE)
            # Find all occurrences of this section number header
            matches = list(pattern.finditer(doc_full_text))
            if matches:
                # If multiple matches (e.g. cross references), choose the best one
                chosen = matches[0]
                if len(matches) > 1 and sec_n > 1 and (sec_n - 1) in section_locations:
                    prev_pos = section_locations[sec_n - 1]["start"]
                    # Pick the first match that appears reasonably close after previous section
                    after_prev = [m for m in matches if m.start() >= prev_pos - 1500]
                    if after_prev:
                        chosen = after_prev[0]
                section_locations[sec_n] = {
                    "sec_num": sec_n,
                    "start": chosen.start(),
                    "match_end": chosen.end()
                }

        # Order matches by their document position for clean text slicing
        matched_secs = sorted(section_locations.values(), key=lambda x: x["start"])
        print(f"[✓] Located {len(matched_secs)} / {total_expected} section boundaries.")

        # 3. Extract text cleanly between matched boundaries
        extracted_sections = []
        for i, curr in enumerate(matched_secs):
            sec_n = curr["sec_num"]
            start = curr["start"]
            end = matched_secs[i + 1]["start"] if i + 1 < len(matched_secs) else len(doc_full_text)
            
            raw_text = doc_full_text[start:end].strip()
            clean_body = re.split(r'\n\s*(?:FIRST|SECOND|THIRD|FOURTH)?\s*SCHEDULE\b', raw_text, flags=re.IGNORECASE)[0]
            clean_body = re.sub(r'\n\s*(PART\s+[0-9IVXLCDM]+\s*[-–—][^\n]+)', '', clean_body, flags=re.IGNORECASE)
            clean_body = re.sub(r'\n\s*\n+', '\n\n', clean_body).strip()

            # Ensure clean start
            clean_body = re.sub(rf'^[^\n]*\n+(\s*{sec_n}\.?)', r'\1', clean_body)

            title = toc_titles.get(sec_n, f"Section {sec_n}")
            title = re.sub(r'\s+Schedule$', '', title, flags=re.IGNORECASE).strip().rstrip('.')

            extracted_sections.append({
                "section_number": str(sec_n),
                "section_title": title,
                "part": current_part,
                "full_text": clean_body,
                "searchable_chunk": f"{self.short_title} | {sec_n}. {title} | {clean_body}"
            })

        # Sort extracted sections numerically 1..59
        extracted_sections.sort(key=lambda s: int(s["section_number"]))

        out_data = {
            "statute_id": self.statute_id,
            "short_title": self.short_title,
            "year": self.year,
            "jurisdiction": self.jurisdiction,
            "total_sections": len(extracted_sections),
            "sections": extracted_sections
        }

        if output_path is None:
            output_path = Path(f"data/json_laws/{self.statute_id}.json")
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2, ensure_ascii=False)

        print(f"[✓] Successfully saved {len(extracted_sections)} sections to {output_path}")
        print("=" * 80)
        return out_data

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 ingest_statute_engine.py <pdf_path> <statute_id> <short_title> <year>")
        sys.exit(1)
        
    parser = UniversalGazetteParser(
        pdf_path=sys.argv[1],
        statute_id=sys.argv[2],
        short_title=sys.argv[3],
        year=int(sys.argv[4])
    )
    parser.parse()
