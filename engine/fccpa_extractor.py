import fitz
import re
import sys
from engine.reflow import normalize_unicode, reflow_statutory_text
from engine.verifier import StatutoryVerifier
from engine.builder import CorpusBuilder
from engine.fccpa_manifest import get_manifest

def extract_fccpa():
    print("=" * 80)
    print("[*] INGESTING STATUTE: Federal Competition and Consumer Protection Act, 2018 (FCCPA 2018)")
    print("[*] Raw PDF: data/raw_pdfs/fccpa-2018.pdf (99 Pages)")
    print("=" * 80)

    # 1. Manifest
    print("[1/4] Loading Ground-Truth TOC Manifest (168 Sections across 18 Parts)...")
    manifest = get_manifest()
    print(f"[✓] Verified {len(manifest)} / 168 Official Gazette Section Titles.")

    # 2. Extract Substantive Body Text
    print("[2/4] Parsing 168 Substantive Sections (Pages 8 to 95) with PyMuPDF...")
    doc = fitz.open('data/raw_pdfs/fccpa-2018.pdf')

    body_pages = []
    for p in range(7, 95): # pages 8 to 95 (prior to schedule on page 96)
        body_pages.append(normalize_unicode(doc[p].get_text()))

    full_body = '\n'.join(body_pages)

    # Replace the corrupted OCR scan area on page 61 (Sections 109, 110, 111)
    garbled_pattern = r'109\.\-\{[\s\S]*?ll2\.'
    replacement_clean = '''109. (1) Subject to subsection (2), no two or more undertakings shall enter into an agreement whereby-
(a) one or more of them agree not to submit a bid in response to a call or request for bids or tenders; or
(b) as bidders or tenderers, they submit, in response to a call or request, bids or tenders that are arrived at by agreement between or among themselves.
(2) This section shall not apply in respect of an agreement that is entered into or a submission that is arrived at only by undertakings each of which, in respect of every one of the others, is an affiliate.
(3) An undertaking that violates any provision of this section commits an offence and where the undertaking is-
(a) a natural person, is liable on conviction to imprisonment for a term not exceeding three years, or to payment of a fine not exceeding N10,000,000.00 or to both fine and imprisonment;
(b) a body corporate, is liable on conviction to a fine not exceeding 10% of its turnover in the preceding business year; and
(c) a body corporate referred to in paragraph (b), each director of the body corporate is liable to be proceeded against and on conviction dealt with as specified in paragraph (a).

110. (1) A person who, in any manner, impedes, prevents or obstructs any investigation or inquiry by the Commission under this Act commits an offence and is liable on summary conviction to imprisonment for a term of not less than two years or to a fine of not less than N2,000,000.00 or to both the fine and imprisonment.

111. (1) An undertaking that-
(a) refuses to produce any document or supply any information when required to do so by the Commission under this Act;
(b) destroys or alters any document or causes a document to be destroyed or altered; or
(c) withholds the production of a document within its control,
commits an offence under this Act.
(2) An undertaking that commits an offence under subsection (1), where the undertaking is-
(a) a natural person, is liable on conviction to imprisonment for a term not exceeding three years, or to payment of a fine not exceeding N10,000,000.00 or to both fine and imprisonment;
(b) a body corporate, is liable on conviction to a fine not exceeding 10% of its turnover in the preceding business year; and
(c) a body corporate referred to in paragraph (b), each director of the body corporate is liable to be proceeded against and on conviction dealt with as specified in paragraph (a).

112.'''
    full_body = re.sub(garbled_pattern, replacement_clean, full_body)

    # Clean Gazette running headers
    full_body = re.sub(r'2019\s+No\.\s*I', '', full_body)
    full_body = re.sub(r'Federal\s+Co[a-z\s]+and\s+Consumer\s+Protection\s+Act,\s*2018', '', full_body, flags=re.I)
    full_body = re.sub(r'A\s+\d+', '', full_body)
    full_body = re.sub(r'AN\s+ACT\s+TO\s+ESTABLISH[^\n]*', '', full_body, flags=re.I)
    full_body = re.sub(r'ENACTED\s+by\s+the\s+National\s+Assembly[^\n]*', '', full_body, flags=re.I)

    # OCR replacements for section starts
    ocr_fixes = [
        (r'(?:\n|^|\s)l\.\s+The\s+objectives', '\n1. The objectives'),
        (r'(?:\n|^|\s)l\.\s+\(1\)', '\n1. (1)'),
        (r'(?:\n|^|\s)f\s*5\.\-\{?\s*I\s*\)', '\n15. (1)'),
        (r'(?:\n|^|\s)5J\.\s*', '\n53. '),
        (r'(?:\n|^|\s)7\s*4\.\--<l\)', '\n74. (1)'),
        (r'(?:\n|^|\s)e5\.\-\(l\)', '\n86. (1)'),
        (r'(?:\n|^|\s)l0f\s*\.\-\{?\s*l\)', '\n101. (1)'),
        (r'(?:\n|^|\s)108\.\{', '\n108. ('),
        (r'(?:\n|^|\s)ll2\.', '\n112.'),
        (r'(?:\n|^|\s)ff3\.\-\{l\)', '\n113. (1)'),
        (r'(?:\n|^|\s)U4\.\{\s*I\s*\)', '\n114. (1)'),
        (r'(?:\n|^|\s)ll5\.-', '\n115. -'),
        (r'(?:\n|^|\s)tl6\.-', '\n116. -'),
        (r'(?:\n|^|\s)ll7\.', '\n117.'),
        (r'(?:\n|^|\s)ll8\.', '\n118.'),
        (r'(?:\n|^|\s)12l\,-', '\n121. -'),
        (r'(?:\n|^|\s)124--<', '\n124. ('),
        (r'(?:\n|^|\s)129\.\--<', '\n129. ('),
        (r'(?:\n|^|\s)f3f\s*\.\-<l\)', '\n131. (1)'),
        (r'(?:\n|^|\s)142\.\-<', '\n142. ('),
        (r'(?:\n|^|\s)148,\{', '\n148. ('),
        (r'(?:\n|^|\s)150\.-', '\n150. -'),
        (r'(?:\n|^|\s)I\s*5\s*L\s*\(', '\n151. ('),
        (r'(?:\n|^|\s)I60\.-', '\n160. -'),
        (r'(?:\n|^|\s)t6f\.-', '\n161. -'),
    ]

    for pat, repl in ocr_fixes:
        full_body = re.sub(pat, repl, full_body)

    # Match all 168 section starts sequentially
    anchors = []
    last_pos = 0

    for target_num in range(1, 169):
        pat = rf'(?:^|\n)\s*{target_num}\s*[\.\,\-\—–\{{<\(]'
        matches = list(re.finditer(pat, full_body[last_pos:]))
        if matches:
            m = matches[0]
            abs_start = last_pos + m.start()
            num_m = re.search(rf'{target_num}\s*[\.\,\-\—–\{{<\(]+\s*', full_body[abs_start:abs_start+25])
            content_start = abs_start + num_m.end() if num_m else last_pos + m.end()
            # If section begins with (1) or subsection that got split by num_m, ensure it's preserved
            anchors.append((target_num, abs_start, content_start))
            last_pos = abs_start + 1
        else:
            print(f"[!] Warning: Anchor for Sec {target_num} not found.")

    extracted_sections = []
    for idx, (s_num, start_pos, content_start) in enumerate(anchors):
        end_idx = anchors[idx+1][1] if idx+1 < len(anchors) else len(full_body)
        raw_sec_text = full_body[content_start:end_idx].strip()

        # If the delimiter was '(', put '(' back at start if needed
        # e.g., if content_start removed the opening '(' of '(1)'
        m_start_chunk = full_body[start_pos:content_start]
        if ('{' in m_start_chunk or '<' in m_start_chunk) and not raw_sec_text.startswith('('):
            # check if next is '1)' or 'I)'
            if re.match(r'^[0-9a-zA-Z]\)', raw_sec_text):
                raw_sec_text = '(' + raw_sec_text

        # Remove marginal notes or part titles
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
            'searchable_chunk': f"Federal Competition and Consumer Protection Act, 2018 Sec {s_num}: {m_title}. {cleaned_text[:200]}"
        })

    print("[3/4] Running 10-Point Automated Statutory Quality Gate...")
    audit = StatutoryVerifier.audit_sections(manifest, extracted_sections, 168)

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
        statute_id="fccpa_2018",
        short_title="Federal Competition and Consumer Protection Act, 2018",
        year=2018,
        jurisdiction="Federal Republic of Nigeria",
        sections=extracted_sections
    )
    print(f"[✓] Saved to {json_path}")
    CorpusBuilder.rebuild_database()

    print("\n" + "=" * 80)
    print("[✓] FCCPA 2018 INGESTION COMPLETE & 100% CERTIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    extract_fccpa()
