import json
import re

def parse_pia_act():
    ocr_path = 'data/raw_pdfs/petroleum_industry_act_2021_ocr.json'
    out_json_path = 'data/json_laws/petroleum_industry_act_2021.json'

    with open(ocr_path) as f:
        pages = json.load(f)

    print(f'Loaded {len(pages)} OCR pages from {ocr_path}')

    # 1. Parse TOC from Pages 2 to 9 (0-indexed 1 to 8)
    toc_dict = {}
    
    # We will build a TOC dictionary from the Arrangement of sections
    # and also fallback to section titles extracted from section side-notes/headings
    current_chapter = "Chapter 1 — Governance and Institutions"
    
    for p_idx in range(1, 9):
        page_obs = pages[p_idx]
        sorted_obs = sorted(page_obs, key=lambda o: -o['y'])
        for obs in sorted_obs:
            text = obs['text'].strip()
            if not text:
                continue
            chap_m = re.match(r'^(CHAPTER\s+\d+)\s*[-—–]\s*(.*)', text, re.IGNORECASE)
            if chap_m:
                current_chapter = chap_m.group(1).upper() + ' — ' + chap_m.group(2).title()
                continue
            sec_m = re.match(r'^(\d+)\.\s*(.*)', text)
            if sec_m:
                s_num = sec_m.group(1)
                s_title = sec_m.group(2).strip()
                if int(s_num) <= 319:
                    toc_dict[s_num] = s_title

    print(f'TOC Dictionary parsed: {len(toc_dict)} sections')

    # 2. Extract substantive body lines from Page 10 onwards (0-indexed 9 to 252)
    body_lines = []
    for p_idx in range(9, len(pages)):
        page_obs = pages[p_idx]
        is_even = ((p_idx + 1) % 2 == 0)
        sorted_obs = sorted(page_obs, key=lambda o: -o['y'])

        for obs in sorted_obs:
            t = obs['text'].strip()
            x = obs['x']
            y = obs['y']
            w = obs['w']

            if not t:
                continue

            # Filter running headers
            if y > 0.82 and ('PETROLEUM INDUSTRY ACT' in t or '2021' in t or 'No.' in t or 'A Bill' in t or 'For' in t):
                continue

            # Filter margin side-notes
            if not is_even and x > 0.75:
                continue
            if is_even and (x + w) < 0.18:
                continue

            # Filter enactment formula on page 10
            if p_idx == 9 and ('ENACTED by' in t or 'Commencement' in t or 'An Act to provide' in t):
                continue

            # Filter certification & schedules on final pages
            if 'I, CERTIFY, IN ACCORDANCE' in t or 'CLERK TO THE NATIONAL ASSEMBLY' in t:
                break

            # Remove inline Chapter/Part banners so they don't corrupt section titles
            if re.match(r'^(?:CHAPTER\s+\d+|PART\s+[IVXLCDM]+)\s*[-—–]', t, re.IGNORECASE):
                continue

            body_lines.append(t)

    combined = '\n'.join(body_lines)

    # 3. Split by section pattern
    pattern = r'(?:\n|^)(?=(?:[1-9]\d*)\.\s*(?:\([0-9]+\)\s*)?)'
    segments = [s.strip() for s in re.split(pattern, combined) if s.strip()]

    sections = []
    for seg in segments:
        m = re.match(r'^([1-9]\d*)\.\s*(.*)', seg, re.DOTALL)
        if not m:
            continue
        s_num = m.group(1)
        if int(s_num) > 319:
            continue

        lines = [l.strip() for l in seg.split('\n') if l.strip()]
        cleaned_content = ' '.join(lines)

        if s_num == '319':
            cleaned_content = re.split(r'SCHEDULES|FIRST SCHEDULE', cleaned_content)[0].strip()

        title = toc_dict.get(s_num, f'Section {s_num}')
        
        # Chapter / Part assignment
        s_int = int(s_num)
        if s_int <= 65:
            part = "Chapter 1 — Governance and Institutions"
        elif s_int <= 233:
            part = "Chapter 2 — Administration"
        elif s_int <= 257:
            part = "Chapter 3 — Host Communities Development"
        elif s_int <= 306:
            part = "Chapter 4 — Petroleum Industry Fiscal Framework"
        else:
            part = "Chapter 5 — Miscellaneous Provisions"

        sections.append({
            'section_number': s_num,
            'title': title,
            'content': cleaned_content,
            'part': part
        })

    print(f'Extracted {len(sections)} sections from substantive body (expected 319)')

    output_data = {
        'statute_title': 'Petroleum Industry Act, 2021',
        'year': 2021,
        'citation': 'Act No. 6 of 2021',
        'sections': sections
    }

    with open(out_json_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f'Successfully wrote {out_json_path}')
    return sections

if __name__ == '__main__':
    parse_pia_act()
