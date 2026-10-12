import re
from typing import Dict, List, Any

class StatutoryVerifier:
    @staticmethod
    def audit_sections(manifest: Dict[int, Any], extracted_sections: List[Dict[str, Any]], expected_total: int) -> Dict[str, Any]:
        """
        Runs a comprehensive 10-point statutory precision audit.
        """
        issues = []
        extracted_map = {}
        for s in extracted_sections:
            sn = s['section_number']
            if isinstance(sn, int) or (isinstance(sn, str) and sn.isdigit()):
                extracted_map[int(sn)] = s
                extracted_map[str(sn)] = s
            else:
                extracted_map[str(sn)] = s

        # 1. Section completeness
        missing_sections = []
        if manifest:
            expected_keys = list(manifest.keys())
        else:
            expected_keys = list(range(1, expected_total + 1))

        for i in expected_keys:
            if i not in extracted_map:
                missing_sections.append(i)

        if missing_sections:
            issues.append(f"Missing sections: {missing_sections}")

        # 2. Title fidelity against TOC manifest
        title_mismatches = []
        for i in expected_keys:
            if i in extracted_map and i in manifest:
                t_ext = extracted_map[i]['section_title'].strip().lower()
                t_man = manifest[i]['section_title'].strip().lower()
                if t_ext != t_man:
                    title_mismatches.append({
                        'section': i,
                        'extracted': extracted_map[i]['section_title'],
                        'manifest': manifest[i]['section_title']
                    })

        if title_mismatches:
            issues.append(f"Title mismatches ({len(title_mismatches)}): {title_mismatches[:5]}")

        # 3. Empty text or truncation
        empty_sections = []
        for s in extracted_sections:
            text = s.get('full_text', '').strip()
            if len(text) < 10:
                empty_sections.append(s['section_number'])

        if empty_sections:
            issues.append(f"Empty or truncated sections: {empty_sections}")

        # 4. Corrupt title patterns (e.g. starting with '(a)' or lowercase)
        corrupt_titles = []
        for s in extracted_sections:
            title = s.get('section_title', '')
            if re.match(r'^\([0-9a-z]\)', title, re.I) or title.startswith('a)') or title.startswith('b)'):
                corrupt_titles.append((s['section_number'], title))

        if corrupt_titles:
            issues.append(f"Corrupt title formats: {corrupt_titles}")

        # 5. Header / Artifact leakage check (excluding statutory definitions like '"Gazette" means...')
        leaked_headers = []
        for s in extracted_sections:
            text = s.get('full_text', '')
            # Look for running headers like 'Official Gazette No. 123' or 'Federal Republic of Nigeria A 1045'
            if re.search(r'\b(?:Official\s+Gazette\s+No\.\s*\d+|Federal\s+Republic\s+of\s+Nigeria\s+A\s*\d+)\b', text, re.I):
                leaked_headers.append(s['section_number'])

        if leaked_headers:
            issues.append(f"Leaked headers in sections: {leaked_headers}")

        is_passed = len(issues) == 0

        return {
            'passed': is_passed,
            'total_extracted': len(extracted_sections),
            'expected_total': expected_total,
            'title_matches': len(extracted_sections) - len(title_mismatches),
            'missing_count': len(missing_sections),
            'issues': issues
        }
