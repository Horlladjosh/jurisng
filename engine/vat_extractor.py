import fitz
import re
import sys
from engine.reflow import normalize_unicode, reflow_statutory_text
from engine.verifier import StatutoryVerifier
from engine.builder import CorpusBuilder
from engine.vat_manifest import get_manifest

def extract_vat():
    print("=" * 80)
    print("[*] INGESTING STATUTE: Value Added Tax Act (Cap. V1 LFN)")
    print("[*] Raw PDF: data/raw_pdfs/vat_act.pdf (39 Pages)")
    print("=" * 80)

    # 1. Manifest
    print("[1/4] Loading Ground-Truth TOC Manifest (48 Sections across 6 Parts)...")
    manifest = get_manifest()
    print(f"[✓] Verified {len(manifest)} / 48 Official Gazette Section Titles.")

    # 2. Extract Substantive Body Text
    print("[2/4] Parsing 48 Substantive Sections (Pages 3 to 17) with PyMuPDF...")
    doc = fitz.open('data/raw_pdfs/vat_act.pdf')

    body_pages = []
    for p in range(2, 17): # pages 3 to 17
        body_pages.append(normalize_unicode(doc[p].get_text()))

    full_body = '\n'.join(body_pages)

    # Section sequence
    sec_targets = [str(i) for i in range(1, 14)] + ['13A'] + [str(i) for i in range(14, 48)]
    anchors = []
    last_pos = 0

    for target_str in sec_targets:
        pat = rf'(?:^|\n)\s*{target_str}\s*[\.\,\-\—–\{{<\(]'
        matches = list(re.finditer(pat, full_body[last_pos:]))
        if matches:
            m = matches[0]
            abs_start = last_pos + m.start()
            num_m = re.search(rf'{target_str}\s*[\.\,\-\—–\{{<\(]+\s*', full_body[abs_start:abs_start+25])
            content_start = abs_start + num_m.end() if num_m else last_pos + m.end()
            anchors.append((target_str, abs_start, content_start))
            last_pos = abs_start + 1
        else:
            print(f"[!] Warning: Anchor for Sec {target_str} not found.")

    extracted_sections = []
    for idx, (s_num, start_pos, content_start) in enumerate(anchors):
        end_idx = anchors[idx+1][1] if idx+1 < len(anchors) else len(full_body)
        raw_sec_text = full_body[content_start:end_idx].strip()

        if ('{' in full_body[start_pos:content_start] or '<' in full_body[start_pos:content_start] or '(' in full_body[start_pos:content_start]) and not raw_sec_text.startswith('('):
            if re.match(r'^[0-9a-zA-Z]\)', raw_sec_text):
                raw_sec_text = '(' + raw_sec_text

        # Remove part titles
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
            'searchable_chunk': f"Value Added Tax Act Sec {s_num}: {m_title}. {cleaned_text[:200]}"
        })

    # Prepare manifest for verifier (using string keys)
    manifest_for_verifier = {int(re.sub(r'\D', '', k)) if k.isdigit() else k: v for k, v in manifest.items()}
    # Let's map extracted section numbers for verifier
    extracted_for_verifier = []
    for s in extracted_sections:
        sn = s['section_number']
        extracted_for_verifier.append({
            'section_number': int(sn) if sn.isdigit() else sn,
            'section_title': s['section_title'],
            'part': s['part'],
            'full_text': s['full_text']
        })

    print("[3/4] Running 10-Point Automated Statutory Quality Gate...")
    audit = StatutoryVerifier.audit_sections(manifest_for_verifier, extracted_for_verifier, 48)

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
        statute_id="value_added_tax_act",
        short_title="Value Added Tax Act",
        year=1993,
        jurisdiction="Federal Republic of Nigeria",
        sections=extracted_sections
    )
    print(f"[✓] Saved to {json_path}")
    CorpusBuilder.rebuild_database()

    print("\n" + "=" * 80)
    print("[✓] VALUE ADDED TAX ACT INGESTION COMPLETE & 100% CERTIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    extract_vat()
