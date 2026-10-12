import json
import re

def parse_electricity_act():
    ocr_path = 'data/raw_pdfs/electricity_act_2023_ocr.json'
    out_json_path = 'data/json_laws/electricity_act_2023.json'

    with open(ocr_path) as f:
        pages = json.load(f)

    print(f'Loaded {len(pages)} OCR pages from {ocr_path}')

    # 1. Parse TOC from Pages 2 to 8 (0-indexed 1 to 7)
    toc_dict = {}
    part_map = {}
    current_part = "Part I — Preliminary Provisions"

    for p_idx in range(1, 8):
        page_obs = pages[p_idx]
        sorted_obs = sorted(page_obs, key=lambda o: -o['y'])
        for obs in sorted_obs:
            text = obs['text'].strip()
            if not text:
                continue
            part_m = re.match(r'^(PART\s+[IVXLCDM]+)\s*[-—–]\s*(.*)', text, re.IGNORECASE)
            if part_m:
                current_part = part_m.group(1).upper() + ' — ' + part_m.group(2).title()
                continue
            sec_m = re.match(r'^(\d+)\.\s*(.*)', text)
            if sec_m:
                s_num = sec_m.group(1)
                s_title = sec_m.group(2).strip()
                if int(s_num) <= 231:
                    toc_dict[s_num] = s_title
                    part_map[s_num] = current_part

    print(f'TOC Dictionary parsed: {len(toc_dict)} sections (expected 231)')

    # 2. Extract substantive lines from Page 9 onwards (0-indexed 8 to 151)
    body_lines = []
    for p_idx in range(8, len(pages)):
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
            if y > 0.82 and ('ELECTRICITY ACT' in t or '2023' in t or 'No.' in t or 'A Bill' in t or 'For' in t):
                continue

            # Filter margin side-notes
            # In standard Federal Gazette layout:
            # Odd pages: side-notes are on the right margin (x > 0.74)
            # Even pages: side-notes are on the left margin (x < 0.16)
            if not is_even and x > 0.74:
                continue
            if is_even and (x + w) < 0.20:
                continue

            # Filter enactment formula on page 9 (0-indexed 8)
            if p_idx == 8 and ('ENACTED by' in t or 'Commencement' in t or 'An Act to repeal' in t):
                continue

            # Filter certification & schedules on final pages (if after sec 231)
            if 'I, CERTIFY, IN ACCORDANCE' in t or 'CLERK TO THE NATIONAL ASSEMBLY' in t:
                break

            # Remove inline Part banners so they don't corrupt section titles
            if re.match(r'^PART\s+[IVXLCDM]+\s*[-—–]', t, re.IGNORECASE):
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
        if int(s_num) > 231:
            continue

        lines = [l.strip() for l in seg.split('\n') if l.strip()]
        cleaned_content = ' '.join(lines)

        # Trim trailing schedules on Section 231 if any
        if s_num == '231':
            cleaned_content = re.split(r'SCHEDULES|FIRST SCHEDULE', cleaned_content)[0].strip()

        title = toc_dict.get(s_num, f'Section {s_num}')
        part = part_map.get(s_num, 'Part I')

        sections.append({
            'section_number': s_num,
            'title': title,
            'content': cleaned_content,
            'part': part
        })

    print(f'Extracted {len(sections)} sections from substantive body (expected 231)')
    
    # Save output
    output_data = {
        'statute_title': 'Electricity Act, 2023',
        'year': 2023,
        'citation': 'Act No. 24 of 2023',
        'sections': sections
    }

    with open(out_json_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f'Successfully wrote {out_json_path}')
    return sections

if __name__ == '__main__':
    parse_electricity_act()
