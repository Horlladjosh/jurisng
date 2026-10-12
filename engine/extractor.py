import re
from typing import Dict, List, Any
import pypdf
from engine.reflow import normalize_unicode, reflow_statutory_text
from engine.manifest import ManifestExtractor

class StatutoryExtractor:
    @staticmethod
    def extract_statute(pdf_path: str, toc_start_page: int, toc_end_page: int, body_start_page: int, body_end_page: int, total_expected: int) -> Dict[str, Any]:
        """
        Extracts all substantive sections from PDF with TOC alignment.
        """
        # 1. Pass 1: Extract Manifest
        manifest_data = ManifestExtractor.extract_manifest_from_pdf(
            pdf_path,
            toc_start_page=toc_start_page,
            toc_end_page=toc_end_page,
            total_expected=total_expected
        )
        manifest = manifest_data['sections']

        # 2. Pass 2: Extract Substantive Body Text
        reader = pypdf.PdfReader(pdf_path)
        body_pages = []
        for p in range(body_start_page - 1, min(body_end_page, len(reader.pages))):
            body_pages.append(normalize_unicode(reader.pages[p].extract_text()))

        full_body_raw = '\n'.join(body_pages)

        # Remove enactment formula and title bill headers
        full_body = re.sub(r'A\s+Bill\s+For\s+An\s+act\s+to\s+provide[^\n]*', '', full_body_raw, flags=re.I)
        full_body = re.sub(r'ENACTED\s+by\s+the\s+National\s+Assembly\s+of\s+the\s+Federal\s+Republic\s+of\s+Nigeria\s+as\s+follows\s*:', '', full_body, flags=re.I)

        # Handle Gazette Sec 12/13 typesetting anomaly if present in Cybercrimes Act
        if "cybercrimes" in pdf_path.lower() and re.search(r'12\.\s+13\.\s+\(1\)', full_body):
            full_body = re.sub(
                r'12\.\s+13\.\s+\(1\)\s+Any\s+person,\s+who\s+intentionally',
                r'12. (1) Any person, who intentionally',
                full_body
            )
            full_body = re.sub(
                r'(\(3\)[^\n]+?)\s*A\s+person\s+who\s+knowingly\s+accesses',
                r'\1\n13. A person who knowingly accesses',
                full_body
            )

        # Match section starts including optional preceding PART headers
        sec_positions = []
        for s_num in range(1, total_expected + 1):
            pat = rf'(?:(PART\s+[IVXLCDM]+(?:\s*[-–—]\s*[^\n\d]+)?)\s*)?\b{s_num}\.\s+'
            matches = list(re.finditer(pat, full_body))
            if matches:
                best_m = None
                for m in matches:
                    if not sec_positions or m.start() > sec_positions[-1][1]:
                        best_m = m
                        break
                if best_m:
                    sec_positions.append((s_num, best_m.start(), best_m.end()))
                else:
                    sec_positions.append((s_num, matches[0].start(), matches[0].end()))

        extracted_sections = []
        for idx, (s_num, start_pos, content_start) in enumerate(sec_positions):
            end_idx = sec_positions[idx+1][1] if idx+1 < len(sec_positions) else len(full_body)
            raw_sec_text = full_body[content_start:end_idx].strip()

            # Clean out any trailing marginal title
            m_info = manifest.get(s_num, {})
            m_title = m_info.get('section_title', '')
            if m_title:
                escaped_title = r'\s+'.join([re.escape(w) for w in m_title.split() if len(w) > 0])
                raw_sec_text = re.sub(rf'(?:[\.;\n]|^)\s*{escaped_title}\.?\s*$', '', raw_sec_text, flags=re.I).strip()

            cleaned_text = reflow_statutory_text(raw_sec_text)
            extracted_sections.append({
                'section_number': str(s_num),
                'section_title': m_title,
                'part': m_info.get('part', ''),
                'full_text': cleaned_text,
                'searchable_chunk': f"Sec {s_num}: {m_title}. {cleaned_text[:200]}"
            })

        return {
            'manifest': manifest,
            'sections': extracted_sections
        }
