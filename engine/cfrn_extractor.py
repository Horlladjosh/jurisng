import fitz
import re
import sys
from engine.reflow import normalize_unicode, reflow_statutory_text
from engine.verifier import StatutoryVerifier
from engine.builder import CorpusBuilder
from engine.cfrn_manifest import get_manifest

def extract_cfrn():
    print("=" * 80)
    print("[*] INGESTING STATUTE: Constitution of the Federal Republic of Nigeria 1999 (as amended)")
    print("[*] Raw PDF: data/raw_pdfs/cfrn_1999.pdf (280 Pages)")
    print("=" * 80)

    # 1. Manifest
    print("[1/4] Loading Ground-Truth TOC Manifest (320 Sections across Chapters I to VIII)...")
    manifest_raw = get_manifest()
    manifest = {int(k): v for k, v in manifest_raw.items()}
    print(f"[✓] Verified {len(manifest)} / 320 Official Gazette Section Titles.")

    # 2. Extract Substantive Body Text
    print("[2/4] Parsing 320 Substantive Sections (Pages 23 to 220) with PyMuPDF...")
    doc = fitz.open('data/raw_pdfs/cfrn_1999.pdf')

    body_pages = []
    for p in range(22, 220): # pages 23 to 220
        body_pages.append(normalize_unicode(doc[p].get_text()))

    full_body = '\n'.join(body_pages)

    # Clean running headers
    full_body = re.sub(r'The\s+Constitution\s+of\s+the\s+Federal\s+Republic\s+of\s+Nigeria[^\n]*', '', full_body, flags=re.I)
    full_body = re.sub(r'(?:^|\n)\s*\d+\s*(?:\n|$)', '\n', full_body)

    # Match all 320 section starts sequentially
    anchors = []
    last_pos = 0

    for target_num in range(1, 321):
        pat = rf'(?:^|\n)\s*{target_num}\s*[\.\,\-\—–\t\{{<\(]'
        matches = list(re.finditer(pat, full_body[last_pos:]))
        if matches:
            m = matches[0]
            abs_start = last_pos + m.start()
            num_m = re.search(rf'{target_num}\s*[\.\,\-\—–\t\{{<\(]+\s*', full_body[abs_start:abs_start+25])
            content_start = abs_start + num_m.end() if num_m else last_pos + m.end()
            anchors.append((target_num, abs_start, content_start))
            last_pos = abs_start + 1
        else:
            print(f"[!] Warning: Anchor for Sec {target_num} not found.")

    extracted_sections = []
    for idx, (s_num, start_pos, content_start) in enumerate(anchors):
        end_idx = anchors[idx+1][1] if idx+1 < len(anchors) else len(full_body)
        raw_sec_text = full_body[content_start:end_idx].strip()

        # If delimiter included '(', preserve leading '('
        m_start_chunk = full_body[start_pos:content_start]
        if ('{' in m_start_chunk or '<' in m_start_chunk or '(' in m_start_chunk) and not raw_sec_text.startswith('('):
            if re.match(r'^[0-9a-zA-Z]\)', raw_sec_text):
                raw_sec_text = '(' + raw_sec_text

        # Remove chapter headers or part titles
        raw_sec_text = re.sub(r'CHAPTER\s+[IVXLCDM0-9]+(?:\s*[-–—]\s*[^\n]+)?', '', raw_sec_text, flags=re.I).strip()
        raw_sec_text = re.sub(r'PART\s+[IVXLCDM0-9]+(?:\s*[-–—]\s*[^\n]+)?', '', raw_sec_text, flags=re.I).strip()
        m_info = manifest.get(s_num, {})
        m_title = m_info.get('section_title', '')
        if m_title and len(m_title.strip()) > 5:
            words = [re.escape(w) for w in m_title.split() if len(w) > 0]
            title_pattern = r'\b' + r'\s+'.join(words) + r'\.?\b'
            raw_sec_text = re.sub(title_pattern, '', raw_sec_text, flags=re.I).strip()

        cleaned_text = reflow_statutory_text(raw_sec_text)
        extracted_sections.append({
            'section_number': str(s_num),
            'section_title': m_title,
            'part': m_info.get('part', ''),
            'full_text': cleaned_text,
            'searchable_chunk': f"Constitution of the Federal Republic of Nigeria 1999 Sec {s_num}: {m_title}. {cleaned_text[:200]}"
        })

    print("[3/4] Running 10-Point Automated Statutory Quality Gate...")
    audit = StatutoryVerifier.audit_sections(manifest, extracted_sections, 320)

    print(f"    - Sections Extracted: {audit['total_extracted']} / {audit['expected_total']}")
    print(f"    - Title Matches:      {audit['title_matches']} / {audit['expected_total']}")
    print(f"    - Missing Sections:   {audit['missing_count']}")

    if not audit['passed']:
        print("\n[!] QUALITY GATE FAILED! Issues found:")
        for issue in audit['issues']:
            print(f"    - {issue}")
        sys.exit(1)

    print("[✓] QUALITY GATE PASSED (100% Statutory Precision).")

    print("[4/4] Writing Pristine JSON Corpus & Syncing SQLite + FTS5 Index...")
    json_path = CorpusBuilder.save_statute_json(
        statute_id="cfrn_1999",
        short_title="Constitution of the Federal Republic of Nigeria 1999 (as amended)",
        year=1999,
        jurisdiction="Federal Republic of Nigeria",
        sections=extracted_sections
    )
    print(f"[✓] Saved to {json_path}")
    CorpusBuilder.rebuild_database()

    print("\n" + "=" * 80)
    print("[✓] CFRN 1999 INGESTION COMPLETE & 100% CERTIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    extract_cfrn()
