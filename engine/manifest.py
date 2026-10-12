import re
from typing import Dict, List, Any
import pypdf
from engine.reflow import normalize_unicode

class ManifestExtractor:
    @staticmethod
    def extract_manifest_from_pdf(pdf_path: str, toc_start_page: int, toc_end_page: int, total_expected: int = None) -> Dict[str, Any]:
        """
        Extracts the official Table of Contents (Arrangement of Sections)
        from the specified page range of the PDF.
        """
        reader = pypdf.PdfReader(pdf_path)
        toc_raw = ''
        for p in range(toc_start_page - 1, toc_end_page):
            if p < len(reader.pages):
                toc_raw += reader.pages[p].extract_text() + '\n'

        toc_clean = normalize_unicode(toc_raw)
        # Remove common TOC running headers
        toc_clean = re.sub(r'Arrangement\s+of\s+Sections', '', toc_clean, flags=re.I)
        toc_clean = re.sub(r'Section\s*:', '', toc_clean, flags=re.I)
        toc_clean = re.sub(r'\s+', ' ', toc_clean).strip()

        pattern = r'(PART\s+[IVXLCDM]+(?:\s*[-–—]\s*[^0-9]+?)?|\b\d{1,4}\s*[\.|\s])'
        splits = list(re.finditer(pattern, toc_clean))

        sections = {}
        current_part = ''

        for idx, match in enumerate(splits):
            token = match.group(0).strip()
            start_pos = match.end()
            end_pos = splits[idx+1].start() if idx+1 < len(splits) else toc_clean.find('SCHEDULE')
            if end_pos == -1:
                end_pos = len(toc_clean)

            content = toc_clean[start_pos:end_pos].strip()

            if token.upper().startswith('PART'):
                current_part = re.sub(r'\s+', ' ', token).strip(' .,:;-–—')
            else:
                sec_num_match = re.search(r'\d+', token)
                if sec_num_match:
                    s_num = int(sec_num_match.group(0))
                    s_title = re.sub(r'\s+', ' ', content).strip(' .,:;-–—')
                    # Ignore false matches like page numbers or year
                    if total_expected and s_num > total_expected:
                        continue
                    if s_num > 0 and len(s_title) > 0:
                        sections[s_num] = {
                            'section_number': str(s_num),
                            'section_title': s_title,
                            'part': current_part
                        }

        return {
            'pdf_path': pdf_path,
            'total_sections_extracted': len(sections),
            'sections': sections
        }
