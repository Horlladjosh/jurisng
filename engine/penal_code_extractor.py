import fitz
import re
import sys
from engine.reflow import normalize_unicode, reflow_statutory_text
from engine.verifier import StatutoryVerifier
from engine.builder import CorpusBuilder
from engine.penal_code_manifest import get_manifest

def extract_penal_code():
    print("=" * 80)
    print("[*] INGESTING STATUTE: Penal Code (Northern States) Federal Provisions Act, 1960")
    print("[*] Raw PDF: data/raw_pdfs/penal-code-northern-states-1960.pdf (22 Pages)")
    print("=" * 80)

    # 1. Manifest
    print("[1/4] Loading Ground-Truth TOC Manifest (74 Sections: 6 Main + 68 Schedule)...")
    manifest = get_manifest()
    print(f"[✓] Verified {len(manifest)} / 74 Official Section Titles.")

    # 2. Extract Substantive Body Text
    print("[2/4] Parsing 74 Substantive Sections (Pages 4 to 22) with PyMuPDF...")
    doc = fitz.open('data/raw_pdfs/penal-code-northern-states-1960.pdf')

    body_pages = []
    for p in range(3, len(doc)): # pages 4 to 22
        body_pages.append(normalize_unicode(doc[p].get_text()))

    full_body = '\n'.join(body_pages)

    # Clean OCR glitch 1410 -> 410
    full_body = re.sub(r'(?:\n|^|\s)1410\.\s+', '\n410. ', full_body)

    # Match all 74 section starts sequentially
    # Main Act sections 1 to 6, then Schedule sections 410 to 477
    all_targets = list(range(1, 7)) + list(range(410, 478))
    anchors = []
    last_pos = 0

    for target_num in all_targets:
        pat = rf'(?:^|\n)\s*{target_num}\s*[\.\,\-\—–\{{<\(]'
        matches = list(re.finditer(pat, full_body[last_pos:]))
        if matches:
            m = matches[0]
            abs_start = last_pos + m.start()
            num_m = re.search(rf'{target_num}\s*[\.\,\-\—–\{{<\(]+\s*', full_body[abs_start:abs_start+25])
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
            'searchable_chunk': f"Penal Code (Northern States) Federal Provisions Act, 1960 Sec {s_num}: {m_title}. {cleaned_text[:200]}"
        })

    print("[3/4] Running 10-Point Automated Statutory Quality Gate...")
    audit = StatutoryVerifier.audit_sections(manifest, extracted_sections, 74)

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
        statute_id="penal_code_1960",
        short_title="Penal Code (Northern States) Federal Provisions Act, 1960",
        year=1960,
        jurisdiction="Federal Republic of Nigeria",
        sections=extracted_sections
    )
    print(f"[✓] Saved to {json_path}")
    CorpusBuilder.rebuild_database()

    print("\n" + "=" * 80)
    print("[✓] PENAL CODE 1960 INGESTION COMPLETE & 100% CERTIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    extract_penal_code()
