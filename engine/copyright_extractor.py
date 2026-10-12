import fitz
import re
import sys
from engine.copyright_manifest import get_copyright_manifest
from engine.reflow import reflow_statutory_text
from engine.verifier import StatutoryVerifier
from engine.builder import CorpusBuilder

def extract_copyright():
    print("=" * 80)
    print("[*] INGESTING STATUTE: Copyright Act, 2022 (Act No. 8)")
    print("[*] Raw PDF: data/raw_pdfs/copyright_act_2022.pdf (Official Gazette No. 56)")
    print("=" * 80)

    # 1. Manifest
    print("[1/4] Loading Ground-Truth TOC Manifest (109 Sections across 12 Parts)...")
    manifest = get_copyright_manifest()
    print(f"[✓] Loaded {len(manifest)} / 109 Official Gazette Section Titles.")

    # 2. Extract Body Pages (Pages 7-64) with layout filtering
    print("[2/4] Parsing 109 Substantive Sections (Pages 7-64) with PyMuPDF...")
    doc = fitz.open('data/raw_pdfs/copyright_act_2022.pdf')
    pages_blocks = []

    for pno in range(6, 64): # Pages 7 to 64
        page = doc[pno]
        is_even = ((pno + 1) % 2 == 0)
        blocks = sorted(page.get_text('blocks'), key=lambda b: (b[1], b[0]))
        for b in blocks:
            x0, y0, x1, y1, text, bno, btype = b
            if y0 < 145: # running header
                continue
            if is_even and x1 < 155: # marginal note
                continue
            if not is_even and x0 > 440: # marginal note
                continue
            t_clean = text.strip()
            if pno == 6 and any(w in t_clean for w in ['AN ACT TO REPEAL', 'ACT No. 8', 'ENACTED by the National Assembly', '[17th Day of March, 2023]']):
                continue
            if re.match(r'^PART\s+[IVXLCDM0-9]+', t_clean, re.I):
                if re.search(r'\b\d+[\.\-—–]', t_clean):
                    t_clean = re.sub(r'^PART\s+[IVXLCDM0-9]+[^\n]*\n?', '', t_clean, flags=re.I).strip()
                else:
                    continue
            if t_clean:
                pages_blocks.append(t_clean)

    full_body = '\n\n'.join(pages_blocks)

    # Find Section Anchors
    anchors = []
    last_pos = 0
    for s in range(1, 110):
        pat = rf'(?:^|\n|\s)\b{s}\s*[\.\-—–]\s*(?:\([0-9a-zA-Z]+\)|[A-Z0-9\(\—\–\-])'
        matches = list(re.finditer(pat, full_body[last_pos:]))
        if matches:
            m = matches[0]
            abs_start = last_pos + m.start()
            num_m = re.search(rf'\b{s}\s*[\.\-—–]+\s*', full_body[abs_start:abs_start+25])
            content_start = abs_start + num_m.end() if num_m else last_pos + m.end()
            anchors.append((s, abs_start, content_start))
            last_pos = abs_start + 1
        else:
            print(f"[!] Warning: Missed anchor for section {s}")

    extracted_sections = []
    for idx, (s_num, start_pos, content_start) in enumerate(anchors):
        end_idx = anchors[idx+1][1] if idx+1 < len(anchors) else len(full_body)
        raw_text = full_body[content_start:end_idx].strip()
        if s_num == 109:
            raw_text = re.sub(r'\n?Citation\.?\s*$', '', raw_text, flags=re.I).strip()
        cleaned = reflow_statutory_text(raw_text)
        m_info = manifest[s_num]
        extracted_sections.append({
            'section_number': str(s_num),
            'section_title': m_info['section_title'],
            'part': m_info['part'],
            'full_text': cleaned,
            'searchable_chunk': f"Copyright Act, 2022 Sec {s_num}: {m_info['section_title']}. {cleaned[:200]}"
        })

    print("[3/4] Running 10-Point Automated Statutory Quality Gate...")
    audit = StatutoryVerifier.audit_sections(manifest, extracted_sections, 109)

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
        statute_id="copyright_act_2022",
        short_title="Copyright Act, 2022",
        year=2022,
        jurisdiction="Federal Republic of Nigeria",
        sections=extracted_sections
    )
    print(f"[✓] Saved to {json_path}")
    CorpusBuilder.rebuild_database()

    print("\n" + "=" * 80)
    print("[✓] COPYRIGHT ACT 2022 INGESTION COMPLETE & 100% CERTIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    extract_copyright()
