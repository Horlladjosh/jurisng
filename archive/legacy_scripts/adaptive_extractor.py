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

class AdaptiveStatuteExtractor:
    def __init__(self, statute_id: str, statute_title: str, short_title: str, year: int, total_sections: int, pdf_path: str, output_path: str):
        self.statute_id = statute_id
        self.statute_title = statute_title
        self.short_title = short_title
        self.year = year
        self.expected_sections = total_sections
        self.pdf_path = Path(pdf_path)
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def extract_clean_text(self) -> str:
        reader = PdfReader(str(self.pdf_path))
        pages_text = []
        for p in reader.pages:
            t = p.extract_text() or ""
            # Strip recurring gazette headers/footers
            t = re.sub(r'Page\s+\d+\s+of\s+\d+', '', t, flags=re.IGNORECASE)
            t = re.sub(r'Federal Republic of Nigeria Official Gazette', '', t, flags=re.IGNORECASE)
            t = re.sub(r'\[\s*Extm\s*\]', '', t, flags=re.IGNORECASE)
            pages_text.append(t)
        return "\n".join(pages_text)

    def parse(self) -> List[SectionModel]:
        raw = self.extract_clean_text()
        
        # Adaptive Multi-Tier Regex:
        # Tier 1: "Section 12. Title", "12. Title", "12 Title" (period optional)
        # Tier 2: "\n12. (1)" or "\n12 (1)"
        pattern = re.compile(
            r'(?:\n|\A)(?:Section\s+)?([0-9]{1,4}[A-Z]?)\s*[\.\-\–\s]\s*([A-Z][^\n\(\)\.\—]{1,120})?(?:\n|\s{2,}|\s*(?=\([0-9a-zA-Z]+\)|[A-Z]))',
            re.MULTILINE
        )

        matches = list(pattern.finditer(raw))
        sections_dict = {}

        for i, match in enumerate(matches):
            sec_num = match.group(1).strip()
            
            try:
                num_int = int(re.sub(r'\D', '', sec_num))
                # Ignore random standalone integers (like page numbers or single digit notes)
                if num_int > 900 or num_int == 0:
                    continue
            except ValueError:
                continue

            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
            
            raw_title = match.group(2).strip() if (match.lastindex and match.lastindex >= 2 and match.group(2)) else ""
            raw_body = raw[start_pos:end_pos].strip()

            if not raw_title and "\n" in raw_body:
                lines = [l.strip() for l in raw_body.split("\n") if l.strip()]
                if lines and len(lines[0]) < 80 and not lines[0].startswith("("):
                    raw_title = lines[0]
                    raw_body = "\n".join(lines[1:])

            clean_body = re.sub(r'\s+', ' ', raw_body).strip()
            clean_title = re.sub(r'\s+', ' ', raw_title).strip() or f"Section {sec_num}"

            # Only accept non-empty bodies
            if len(clean_body) > 10 and sec_num not in sections_dict:
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

        return sorted(sections_dict.values(), key=lambda x: sec_sort_key(x.section_number))

    def run(self):
        parsed = self.parse()
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
        status = "COMPLETE" if pct >= 95 else "PARTIAL"
        print(f"[{status}] {self.short_title:<28}: {len(parsed):>4} / {self.expected_sections:<4} ({pct:5.1f}%) -> {self.output_path.name}")

if __name__ == "__main__":
    TARGETS = [
        ("evidence_act_2011", "Evidence Act 2011", "Evidence Act 2011", 2011, 259, "data/raw_pdfs/evidence-act-2011.pdf", "data/json_laws/evidence_act_2011.json"),
        ("cybercrimes_act_2015", "Cybercrimes (Prohibition, Prevention, etc.) Act 2015", "Cybercrimes Act 2015", 2015, 59, "data/raw_pdfs/cybercrimes-act-2015.pdf", "data/json_laws/cybercrimes_act_2015.json"),
        ("fccpa_2018", "Federal Competition and Consumer Protection Act 2018", "FCCPA 2018", 2018, 168, "data/raw_pdfs/fccpa-2018.pdf", "data/json_laws/fccpa_2018.json"),
        ("national_health_act_2014", "National Health Act 2014", "National Health Act 2014", 2014, 65, "data/raw_pdfs/national-health-act-2014.pdf", "data/json_laws/national_health_act_2014.json"),
        ("penal_code_act_1960", "Penal Code (Northern States) Federal Provisions Act", "Penal Code Act", 1960, 74, "data/raw_pdfs/penal-code-northern-states-1960.pdf", "data/json_laws/penal_code_act_1960.json"),
        ("money_laundering_act_2011", "Money Laundering (Prohibition) Act 2011", "Money Laundering Act 2011", 2011, 25, "data/raw_pdfs/money-laundering-act-2011.pdf", "data/json_laws/money_laundering_act_2011.json"),
    ]

    print("================================================================")
    print("RUNNING ADAPTIVE HIGH-RECALL EXTRACTION ON TARGETED STATUTES")
    print("================================================================")
    for cfg in TARGETS:
        if Path(cfg[5]).exists():
            extractor = AdaptiveStatuteExtractor(*cfg)
            extractor.run()
        else:
            print(f"[MISSING] {cfg[2]}: File not found at {cfg[5]}")
