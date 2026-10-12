import re
import json
from pathlib import Path
from pypdf import PdfReader
from pydantic import BaseModel
from typing import List

class SectionModel(BaseModel):
    section_number: str
    section_title: str
    full_text: str
    searchable_chunk: str

class StatuteModel(BaseModel):
    statute_id: str
    statute_title: str
    short_title: str
    year: int
    total_sections_found: int
    expected_sections: int
    sections: List[SectionModel]

class UniversalGazetteExtractor:
    def __init__(self, statute_id: str, statute_title: str, short_title: str, year: int, total_sections: int, pdf_path: str, output_path: str):
        self.statute_id = statute_id
        self.statute_title = statute_title
        self.short_title = short_title
        self.year = year
        self.expected_sections = total_sections
        self.pdf_path = Path(pdf_path)
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def extract_text(self) -> str:
        full_text = []
        reader = PdfReader(str(self.pdf_path))
        for page in reader.pages:
            txt = page.extract_text() or ""
            # Clean common gazette headers/footers
            txt = re.sub(r'Page\s+\d+\s+of\s+\d+', '', txt, flags=re.IGNORECASE)
            txt = re.sub(r'Federal Republic of Nigeria Official Gazette', '', txt, flags=re.IGNORECASE)
            full_text.append(txt)
        return "\n".join(full_text)

    def parse_sections(self, raw_text: str) -> List[SectionModel]:
        # Primary pattern: "12. Title" or "Section 12. Title" or "12. (1)"
        pattern = re.compile(
            r'(?:\n|\A)(?:Section\s+)?(\d{1,4}[A-Z]?)\s*[\.\-\–]\s*([^\n\(\)\.\—]{2,120})?(?:\n|\s{2,}|\s*(?=\([0-9a-zA-Z]+\)|[A-Z]))',
            re.MULTILINE
        )

        matches = list(pattern.finditer(raw_text))
        
        # Fallback pattern for standalone numbers preceding subsections
        if len(matches) < (self.expected_sections * 0.35):
            pattern = re.compile(
                r'(?:\n\s*\n\s*)(\d{1,4}[A-Z]?)\s*[\.\-\–]?\s*(?:\n|\s+)(?:\((?:1|[a-zA-Z])\)|[A-Z][a-z]+)',
                re.MULTILINE
            )
            matches = list(pattern.finditer(raw_text))

        sections_dict = {}
        
        for i, match in enumerate(matches):
            sec_num = match.group(1).strip()
            
            try:
                num_int = int(re.sub(r'\D', '', sec_num))
                if num_int > (self.expected_sections + 50) or num_int == 0:
                    continue
            except ValueError:
                continue

            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
            
            raw_title = match.group(2).strip() if (match.lastindex and match.lastindex >= 2 and match.group(2)) else ""
            raw_body = raw_text[start_pos:end_pos].strip()
            
            if not raw_title and "\n" in raw_body:
                lines = [l.strip() for l in raw_body.split("\n") if l.strip()]
                if lines and len(lines[0]) < 80 and not lines[0].startswith("("):
                    raw_title = lines[0]
                    raw_body = "\n".join(lines[1:])

            clean_body = re.sub(r'\s+', ' ', raw_body).strip()
            clean_title = re.sub(r'\s+', ' ', raw_title).strip() or f"Section {sec_num}"

            if clean_body and sec_num not in sections_dict:
                search_chunk = f"{self.short_title} | Section {sec_num}: {clean_title} | {clean_body}"
                sections_dict[sec_num] = SectionModel(
                    section_number=sec_num,
                    section_title=clean_title,
                    full_text=clean_body,
                    searchable_chunk=search_chunk
                )

        def sec_sort_key(s_num):
            digits = re.findall(r'\d+', s_num)
            return int(digits[0]) if digits else 0

        sorted_sections = sorted(sections_dict.values(), key=lambda x: sec_sort_key(x.section_number))
        return sorted_sections

    def run(self):
        print(f"\n==========================================")
        print(f"Starting Universal Extraction: {self.short_title}")
        print(f"Target: {self.expected_sections} sections")
        print(f"==========================================")
        
        raw_text = self.extract_text()
        parsed = self.parse_sections(raw_text)
        
        statute_data = StatuteModel(
            statute_id=self.statute_id,
            statute_title=self.statute_title,
            short_title=self.short_title,
            year=self.year,
            total_sections_found=len(parsed),
            expected_sections=self.expected_sections,
            sections=parsed
        )

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(statute_data.dict(), f, indent=2, ensure_ascii=False)

        pct = (len(parsed) / self.expected_sections) * 100 if self.expected_sections else 100
        if len(parsed) >= (self.expected_sections * 0.85):
            print(f"SUCCESS: {pct:.1f}% Extracted ({len(parsed)}/{self.expected_sections}) -> {self.output_path}")
        else:
            print(f"ATTENTION: {len(parsed)}/{self.expected_sections} extracted ({pct:.1f}%). Output saved -> {self.output_path}")
