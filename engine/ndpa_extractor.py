import fitz
import re
import sys
from engine.ndpa_manifest import get_ndpa_manifest
from engine.reflow import reflow_statutory_text
from engine.verifier import StatutoryVerifier
from engine.builder import CorpusBuilder

PART_BLOCK_PATTERNS = [
    r'^PART\s+[IVXLCDM0-9]+',
    r'^COMMISSION,\s+AND\s+ITS\s+GOVERNING\s+COUNCIL',
    r'^STAFF\s+OF\s+THE\s+COMMISSION',
    r'^PROCESSING\s+OF\s+PERSONAL\s+DATA',
]

def is_part_block(text: str) -> bool:
    t = text.strip()
    return any(re.search(pat, t, re.I) for pat in PART_BLOCK_PATTERNS)

def extract_ndpa():
    print("=" * 80)
    print("[*] INGESTING STATUTE: Nigeria Data Protection Act, 2023 (NDPA 2023)")
    print("[*] Raw PDF: data/raw_pdfs/ndpa_2023.pdf (Official Gazette No. 119)")
    print("=" * 80)

    # 1. Manifest
    print("[1/4] Loading Ground-Truth TOC Manifest from Official Gazette...")
    manifest = get_ndpa_manifest()
    print(f"[✓] Loaded {len(manifest)} / 66 Official Gazette Section Titles.")

    # 2. Extract Body Pages (Pages 7-39) using layout coordinates
    print("[2/4] Parsing 66 Substantive Sections (Pages 7-39) with PyMuPDF layout analysis...")
    doc = fitz.open('data/raw_pdfs/ndpa_2023.pdf')
    pages_blocks = []

    for pno in range(6, 39): # Pages 7 to 39
        page = doc[pno]
        is_even = ((pno + 1) % 2 == 0)
        blocks = sorted(page.get_text('blocks'), key=lambda b: (b[1], b[0]))
        for b in blocks:
            x0, y0, x1, y1, text, bno, btype = b
            # Skip running headers
            if y0 < 145:
                continue
            # Skip marginal notes
            if is_even and x1 < 155:
                continue
            if not is_even and x0 > 440:
                continue
            t_clean = text.strip()
            # Skip preamble on page 7
            if pno == 6 and any(w in t_clean for w in ['AN ACT TO PROVIDE', 'ACT No. 37', 'ENACTED by the National Assembly', '[12th Day of June, 2023]']):
                continue
            if is_part_block(t_clean):
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
    for s in range(1, 67):
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
        if s_num == 66:
            raw_text = re.sub(r'\nCitation\s*$', '', raw_text, flags=re.I).strip()
        cleaned = reflow_statutory_text(raw_text)
        m_info = manifest[s_num]
        extracted_sections.append({
            'section_number': str(s_num),
            'section_title': m_info['section_title'],
            'part': m_info['part'],
            'full_text': cleaned,
            'searchable_chunk': f"Nigeria Data Protection Act, 2023 Sec {s_num}: {m_info['section_title']}. {cleaned[:200]}"
        })

    print("[3/4] Running 10-Point Automated Statutory Quality Gate...")
    audit = StatutoryVerifier.audit_sections(manifest, extracted_sections, 66)

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
        statute_id="ndpa_2023",
        short_title="Nigeria Data Protection Act, 2023",
        year=2023,
        jurisdiction="Federal Republic of Nigeria",
        sections=extracted_sections
    )
    print(f"[✓] Saved to {json_path}")
    CorpusBuilder.rebuild_database()

    print("\n" + "=" * 80)
    print("[✓] NDPA 2023 INGESTION COMPLETE & 100% CERTIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    extract_ndpa()
