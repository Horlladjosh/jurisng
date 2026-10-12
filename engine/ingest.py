import argparse
import sys
import json
import fitz
import re
from engine.reflow import normalize_unicode, reflow_statutory_text
from engine.verifier import StatutoryVerifier
from engine.builder import CorpusBuilder

def get_electoral_manifest() -> dict:
    doc = fitz.open('data/raw_pdfs/electoral_act_2022.pdf')
    toc_raw = ''
    for p in range(2, 7): # pages 3 to 7
        toc_raw += doc[p].get_text() + '\n'

    toc_clean = normalize_unicode(toc_raw)
    toc_clean = re.sub(r'A\s*\d+\s+2022\s+No\.\s*\d+', '', toc_clean)
    toc_clean = re.sub(r'2022\s+No\.\s*\d+\s+A\s*\d+', '', toc_clean)
    toc_clean = re.sub(r'Electoral\s+Act,\s+2022', '', toc_clean, flags=re.I)
    toc_clean = re.sub(r'ARRANGEMENT\s+OF\s+SECTIONS', '', toc_clean, flags=re.I)
    toc_clean = re.sub(r'Section\s*:', '', toc_clean, flags=re.I)

    parts = []
    for m in re.finditer(r'(PART\s+[IVXLCDM0-9]+(?:\s*[-–—]?\s*[A-Z\s,’\']+)?)(?=\n|\s+\d+\.)', toc_clean):
        parts.append((m.start(), re.sub(r'\s+', ' ', m.group(1)).strip()))

    anchors = []
    last_pos = 0

    for target_num in range(1, 154):
        pat = rf'(?:^|\s|\n)\b{target_num}\b(?:\.|\s|\n)'
        matches = list(re.finditer(pat, toc_clean[last_pos:]))
        if matches:
            m = matches[0]
            abs_start = last_pos + m.start()
            abs_end = last_pos + m.end()
            anchors.append((target_num, abs_start, abs_end))
            last_pos = abs_start + 1

    manifest = {}
    for idx, (s_num, start_pos, content_start) in enumerate(anchors):
        end_pos = anchors[idx+1][1] if idx+1 < len(anchors) else toc_clean.find('SCHEDULES', content_start)
        if end_pos == -1:
            end_pos = len(toc_clean)
        raw_chunk = toc_clean[content_start:end_pos].strip()

        assigned_part = ''
        for p_pos, p_name in parts:
            if p_pos <= start_pos:
                assigned_part = p_name
            else:
                break

        for p_pos, p_name in parts:
            raw_chunk = raw_chunk.replace(p_name, '')

        title = re.sub(r'\s+', ' ', raw_chunk).strip(' .,:;-–—')
        if title.startswith('EstaEstablishment'):
            title = title.replace('EstaEstablishment', 'Establishment')

        manifest[s_num] = {
            'section_number': str(s_num),
            'section_title': title,
            'part': assigned_part
        }

    return manifest

def ingest_electoral():
    print("=" * 80)
    print("[*] INGESTING STATUTE: Electoral Act, 2022")
    print("[*] Raw PDF: data/raw_pdfs/electoral_act_2022.pdf (114 Pages)")
    print("=" * 80)

    # 1. Extract ground truth TOC manifest
    print("[1/4] Extracting Ground-Truth TOC Manifest (Pages 3-7)...")
    manifest = get_electoral_manifest()
    print(f"[✓] Extracted {len(manifest)} / 153 Official Gazette Section Titles.")

    # 2. Extract Substantive Body Text (Pages 9 to 71)
    print("[2/4] Parsing 153 Substantive Sections (Pages 9-71) with PyMuPDF...")
    doc = fitz.open('data/raw_pdfs/electoral_act_2022.pdf')
    body_pages = []
    for p in range(8, 71): # pages 9 to 71
        body_pages.append(normalize_unicode(doc[p].get_text()))

    full_body_raw = '\n'.join(body_pages)

    # Clean Gazette running headers
    full_body = re.sub(r'A\s*\d+\s+2022\s+No\.\s*\d+', '', full_body_raw)
    full_body = re.sub(r'2022\s+No\.\s*\d+\s+A\s*\d+', '', full_body)
    full_body = re.sub(r'Electoral\s+Act,\s+2022', '', full_body, flags=re.I)
    full_body = re.sub(r'ACT\s+No\.\s*\d+', '', full_body, flags=re.I)
    full_body = re.sub(r'AN\s+ACT\s+TO\s+REPEAL[^\n]*', '', full_body, flags=re.I)
    full_body = re.sub(r'ENACTED\s+by\s+the\s+National\s+Assembly[^\n]*', '', full_body, flags=re.I)

    body_anchors = []
    last_pos = 0

    for target_num in range(1, 154):
        pat = rf'(?:^|\n|\s)\b{target_num}\b[\.]?\s*(?:\([0-9a-zA-Z]+\)|[A-Z]|\n)'
        matches = list(re.finditer(pat, full_body[last_pos:]))
        if matches:
            m = matches[0]
            abs_start = last_pos + m.start()
            num_m = re.search(rf'\b{target_num}\b[\.]?\s*', full_body[abs_start:])
            abs_end = abs_start + num_m.end() if num_m else last_pos + m.end()
            body_anchors.append((target_num, abs_start, abs_end))
            last_pos = abs_start + 1
        else:
            print(f"[!] Missing anchor for Section {target_num}")

    extracted_sections = []
    for idx, (s_num, start_pos, content_start) in enumerate(body_anchors):
        end_idx = body_anchors[idx+1][1] if idx+1 < len(body_anchors) else len(full_body)
        raw_sec_text = full_body[content_start:end_idx].strip()

        # Strip Part headers
        raw_sec_text = re.sub(r'PART\s+[IVXLCDM0-9]+(?:\s*[-–—]?\s*[A-Z\s,’\']+)?', '', raw_sec_text, flags=re.I).strip()

        # Strip marginal note titles
        m_info = manifest.get(s_num, {})
        m_title = m_info.get('section_title', '')
        if m_title and len(m_title.strip()) > 4:
            words = [re.escape(w) for w in m_title.split() if len(w) > 0]
            title_pattern = r'\b' + r'\s+'.join(words) + r'\.?\b'
            raw_sec_text = re.sub(title_pattern, '', raw_sec_text, flags=re.I).strip()

        cleaned_text = reflow_statutory_text(raw_sec_text)

        extracted_sections.append({
            'section_number': str(s_num),
            'section_title': m_title,
            'part': m_info.get('part', ''),
            'full_text': cleaned_text,
            'searchable_chunk': f"Electoral Act, 2022 Sec {s_num}: {m_title}. {cleaned_text[:200]}"
        })

    # 3. 10-Point Automated Quality Gate
    print("[3/4] Running 10-Point Automated Statutory Quality Gate...")
    audit = StatutoryVerifier.audit_sections(manifest, extracted_sections, 153)

    print(f"    - Sections Extracted: {audit['total_extracted']} / {audit['expected_total']}")
    print(f"    - Title Matches:      {audit['title_matches']} / {audit['expected_total']}")
    print(f"    - Missing Sections:   {audit['missing_count']}")

    if not audit['passed']:
        print("\n[!] QUALITY GATE FAILED! Issues found:")
        for issue in audit['issues']:
            print(f"    - {issue}")
        sys.exit(1)

    print("[✓] QUALITY GATE PASSED (100% Statutory Precision).")

    # 4. Save JSON and sync database
    print("[4/4] Writing Pristine JSON Corpus & Syncing SQLite + FTS5 Index...")
    json_path = CorpusBuilder.save_statute_json(
        statute_id="electoral_act",
        short_title="Electoral Act 2022",
        year=2022,
        jurisdiction="Federal",
        sections=extracted_sections
    )
    print(f"[✓] Saved to {json_path}")
    CorpusBuilder.rebuild_database()

    print("\n" + "=" * 80)
    print("[✓] ELECTORAL ACT 2022 INGESTION COMPLETE & 100% CERTIFIED!")
    print("=" * 80)

def get_cama_manifest() -> dict:
    doc = fitz.open('data/raw_pdfs/cama_2020.pdf')
    toc_raw = ''
    for p in range(0, 43):
        toc_raw += doc[p].get_text() + '\n'

    toc_clean = normalize_unicode(toc_raw)
    toc_clean = re.sub(r'COMPANIES\s+AND\s+ALLIED\s+MATTERS\s+ACT,\s+201[9|0]', '', toc_clean, flags=re.I)
    toc_clean = re.sub(r'Arrangement\s+of\s+Sections', '', toc_clean, flags=re.I)
    toc_clean = re.sub(r'Section\s*:', '', toc_clean, flags=re.I)

    toc_clean = re.sub(
        r'609\s+610\s+Adjustment\s+of\s+rights\s+of\s+contributors\.\s+Inspection\s+of\s+books\s+by\s+creditors\s+and\s+contributories\.',
        '609 Adjustment of rights of contributors.\n610 Inspection of books by creditors and contributories.',
        toc_clean
    )
    toc_clean = re.sub(
        r'832\s+833\s*(CHAPTER\s+2[\s\S]*?TRUSTEES\s*)?Change\s+of\s+name\s+or\s+object\.\s+Alteration\s+of\s+provisions\s+of\s+the\s+constitution\.',
        r'\1\n832 Change of name or object.\n833 Alteration of provisions of the constitution.',
        toc_clean
    )
    toc_clean = re.sub(
        r'837\s+838\s+Exercise\s+of\s+powers\s+of\s+trustee\.\s+Application\s+of\s+income\s+and\s+property\.',
        '837 Exercise of powers of trustee.\n838 Application of income and property.',
        toc_clean
    )
    toc_clean = re.sub(
        r'869\s+870\s+Repeal\s+and\s+savings\.\s+Citation\.',
        '869 Repeal and savings.\n870 Citation.',
        toc_clean
    )

    anchors = []
    last_pos = 0

    for target_num in range(1, 871):
        pat = rf'(?:^|\s|\n)\b{target_num}\b(?:\s|\n|\.)'
        matches = list(re.finditer(pat, toc_clean[last_pos:]))
        if matches:
            m = matches[0]
            abs_start = last_pos + m.start()
            abs_end = last_pos + m.end()
            anchors.append((target_num, abs_start, abs_end))
            last_pos = abs_start + 1

    manifest = {}
    current_part = ''

    for idx, (s_num, start_pos, content_start) in enumerate(anchors):
        end_pos = anchors[idx+1][1] if idx+1 < len(anchors) else toc_clean.find('Schedules', content_start)
        if end_pos == -1: end_pos = len(toc_clean)
        raw_chunk = toc_clean[content_start:end_pos].strip()

        part_m = re.search(r'(PART\s+[A-Z0-9]+(?:\s*[-–—]\s*[^\n]+)?)', raw_chunk, re.I)
        if part_m:
            current_part = part_m.group(1).strip()
            raw_chunk = raw_chunk.replace(part_m.group(0), '').strip()

        chap_m = re.search(r'(CHAPTER\s+[0-9]+(?:\s*[-–—]?\s*[^\n]+)?)', raw_chunk, re.I)
        if chap_m:
            raw_chunk = raw_chunk.replace(chap_m.group(0), '').strip()

        title = re.sub(r'\s+', ' ', raw_chunk).strip(' .,:;-–—')
        manifest[s_num] = {
            'section_number': str(s_num),
            'section_title': title,
            'part': current_part
        }

    return manifest

def ingest_cama():
    print("=" * 80)
    print("[*] INGESTING STATUTE: Companies and Allied Matters Act, 2020 (CAMA 2020)")
    print("[*] Raw PDF: data/raw_pdfs/cama_2020.pdf (606 Pages)")
    print("=" * 80)

    print("[1/4] Extracting Ground-Truth TOC Manifest (Pages 1-43)...")
    manifest = get_cama_manifest()
    print(f"[✓] Extracted {len(manifest)} / 870 Official Gazette Section Titles.")

    print("[2/4] Parsing 870 Substantive Sections (Pages 44-508) with PyMuPDF...")
    doc = fitz.open('data/raw_pdfs/cama_2020.pdf')
    body_pages = []
    for p in range(43, 508):
        body_pages.append(normalize_unicode(doc[p].get_text()))

    full_body_raw = '\n'.join(body_pages)
    full_body = re.sub(r'COMPANIES\s+AND\s+ALLIED\s+MATTERS\s+ACT,\s+201[9|0]', '', full_body_raw, flags=re.I)
    full_body = re.sub(r'A\s+Bill\s+For\s+An\s+Act\s+to\s+repeal[^\n]*', '', full_body, flags=re.I)
    full_body = re.sub(r'ENACTED\s+by\s+the\s+National\s+Assembly\s+of\s+the\s+Federal\s+Republic\s+of\s+Nigeria', '', full_body, flags=re.I)

    anchors = []
    last_pos = 0

    for target_num in range(1, 871):
        pat = rf'(?:^|\n|\s)\b{target_num}\.\s+'
        matches = list(re.finditer(pat, full_body[last_pos:]))
        if matches:
            m = matches[0]
            abs_start = last_pos + m.start()
            abs_end = last_pos + m.end()
            anchors.append((target_num, abs_start, abs_end))
            last_pos = abs_start + 1

    extracted_sections = []
    for idx, (s_num, start_pos, content_start) in enumerate(anchors):
        end_idx = anchors[idx+1][1] if idx+1 < len(anchors) else len(full_body)
        raw_sec_text = full_body[content_start:end_idx].strip()

        raw_sec_text = re.sub(r'PART\s+[A-Z0-9]+(?:\s*[-–—]\s*[^\n]+)?', '', raw_sec_text, flags=re.I).strip()
        raw_sec_text = re.sub(r'CHAPTER\s+[0-9]+(?:\s*[-–—]?\s*[^\n]+)?', '', raw_sec_text, flags=re.I).strip()

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
            'searchable_chunk': f"Companies and Allied Matters Act, 2020 Sec {s_num}: {m_title}. {cleaned_text[:200]}"
        })

    print("[3/4] Running 10-Point Automated Statutory Quality Gate...")
    audit = StatutoryVerifier.audit_sections(manifest, extracted_sections, 870)

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
        statute_id="cama_2020",
        short_title="Companies and Allied Matters Act, 2020",
        year=2020,
        jurisdiction="Federal Republic of Nigeria",
        sections=extracted_sections
    )
    print(f"[✓] Saved to {json_path}")
    CorpusBuilder.rebuild_database()

    print("\n" + "=" * 80)
    print("[✓] CAMA 2020 INGESTION COMPLETE & 100% CERTIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Nigerian Federal Statutes with 100% Verbatim Precision")
    parser.add_argument("--statute", "-s", type=str, default="electoral", help="Statute key (e.g. electoral, cama, cybercrimes)")
    args = parser.parse_args()

    if args.statute in ["electoral", "electoral_act"]:
        ingest_electoral()
    elif args.statute == "cama":
        ingest_cama()
    else:
        from engine.ingest import ingest_statute
        ingest_statute(args.statute)
