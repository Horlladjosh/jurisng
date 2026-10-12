import json
import re

def extract_all_electricity_sections():
    with open('data/raw_pdfs/electricity_act_2023_ocr.json') as f:
        pages = json.load(f)

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
            sec_m = re.match(r'^(\d+)\.?\s+(.*)', text)
            if sec_m:
                s_num = int(sec_m.group(1))
                s_title = sec_m.group(2).strip()
                if 1 <= s_num <= 233:
                    toc_dict[s_num] = s_title
                    part_map[s_num] = current_part

    # Fallbacks for OCR anomalies in TOC
    toc_overrides = {
        20: "Conclusive evidence of transfer",
        29: "Exemption from stamp duty",
        30: "Corporate governance",
        31: "Incorporation documents of the ISO",
        55: "The financial year of the Commission",
        126: "Fine for non-payment of money owed",
        129: "Functions and powers of the Agency",
        130: "Establishment and composition of the Governing Board of the Agency",
        155: "Monitoring of rural electrification projects",
        167: "Considerations for renewable purchase obligation",
        170: "Publication of feed-in tariff rates",
        211: "Interference with meters or works of licensees"
    }
    for k, v in toc_overrides.items():
        toc_dict[k] = v

    print(f'TOC Dictionary Ready: {len(toc_dict)} titles')

    # 2. Extract Substantive Content across Pages 9 to 141 (0-indexed 8 to 140)
    # Build clean line list
    all_lines = []
    for p_idx in range(8, 141):
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

            # Header filter
            if y > 0.82 and ('ELECTRICITY ACT' in t or '2023' in t or 'No.' in t or 'A Bill' in t or 'For' in t):
                continue

            # Side-note filter
            if not is_even and x > 0.74:
                continue
            if is_even and (x + w) < 0.19:
                continue

            # Enactment formula filter
            if p_idx == 8 and ('ENACTED by' in t or 'Commencement' in t or 'An Act to repeal' in t):
                continue

            # Skip Part banner
            if re.match(r'^PART\s+[IVXLCDM]+\s*[-—–]', t, re.IGNORECASE):
                continue

            all_lines.append(t)

    # 3. Robust Sequence Matcher
    # We step through target section 1 to 233
    sections = []
    current_sec = 1
    current_lines = []

    # Map of known OCR clipped prefixes for sections where gutter clipped the hundreds digit
    gutter_clipped = {
        161: r'^(?:161|16|61)\.\s*(?:\([0-9]+\)\s*)?(?:The\s+provision|\(1\))',
        170: r'^(?:170|70)\.\s*(?:Feed-in-tariff|\(1\))',
        173: r'^(?:173|17|73)\.\s*(?:There\s+is|\(1\))',
        179: r'^(?:179|79)\.\s*(?:\([0-9]+\)\s*)?The\s+NEMSA',
        180: r'^(?:180|80)\.\s*The\s+chief\s+executive',
        185: r'^(?:185|18|85)\.\s*(?:There\s+is|\(1\))',
        190: r'^(?:190|19|90)\.\s*(?:Notwithstanding|\(1\))',
        192: r'^(?:192|12|92)\.\s*(?:To\s+the|Where|\(1\))',
        197: r'^(?:197|19|97)\.\s*(?:The\s+Academic|\(1\))',
        199: r'^(?:199|19|99)\.\s*(?:The\s+Institute|\(1\))',
        202: r'^(?:202|20|02)\.\s*(?:There\s+is|\(1\))',
        205: r'^(?:205|15|05)\.\s*The\s+Minister',
        207: r'^(?:207|20|07)\.\s*(?:The\s+Minister|\(1\))',
        213: r'^(?:213|21|13)\.\s*(?:A\s+person|\(1\))',
        214: r'^(?:214|21|14)\.\s*(?:A\s+person|\(1\))',
        221: r'^(?:221|1|21)\.\s*(?:The\s+Attorney-General|Ine\s+Attorney)',
        222: r'^(?:222|22|2)\.\s*(?:\([0-9]+\)\s*)?Notwithstanding',
        228: r'^(?:228|28|8)\.\s*Without\s+prejudice'
    }

    line_idx = 0
    while line_idx < len(all_lines):
        line = all_lines[line_idx].strip()
        next_sec = current_sec + 1

        is_next = False
        if next_sec <= 233:
            # Check standard regex
            m = re.match(rf'^{next_sec}\.\s*(.*)', line)
            if m:
                is_next = True
            elif next_sec in gutter_clipped:
                if re.match(gutter_clipped[next_sec], line, re.IGNORECASE):
                    is_next = True
                    # Normalize line start
                    line = re.sub(r'^\d+\.\s*', f'{next_sec}. ', line)

        if is_next:
            # Save current_sec
            sec_content = ' '.join([l.strip() for l in current_lines if l.strip()])
            title = toc_dict.get(current_sec, f'Section {current_sec}')
            part = part_map.get(current_sec, 'Part I — Preliminary Provisions')
            sections.append({
                'section_number': str(current_sec),
                'title': title,
                'content': sec_content,
                'part': part
            })
            current_sec = next_sec
            current_lines = [line]
            line_idx += 1
            continue

        current_lines.append(line)
        line_idx += 1

    # Save final section 233
    if current_lines:
        sec_content = ' '.join([l.strip() for l in current_lines if l.strip()])
        sec_content = re.split(r'SCHEDULES|FIRST SCHEDULE', sec_content)[0].strip()
        title = toc_dict.get(current_sec, f'Section {current_sec}')
        part = part_map.get(current_sec, 'Part XXII — Final Provisions')
        sections.append({
            'section_number': str(current_sec),
            'title': title,
            'content': sec_content,
            'part': part
        })

    print(f'Successfully segmented {len(sections)} sections (target: 233)')
    for s in sections[:10]:
        print(f"  Sec {s['section_number']}: {s['title']} ({len(s['content'])} chars)")
    for s in sections[-10:]:
        print(f"  Sec {s['section_number']}: {s['title']} ({len(s['content'])} chars)")

    output_data = {
        'statute_title': 'Electricity Act, 2023',
        'year': 2023,
        'citation': 'Act No. 24 of 2023',
        'sections': sections
    }

    with open('data/json_laws/electricity_act_2023.json', 'w') as f:
        json.dump(output_data, f, indent=2)

    print('SAVED data/json_laws/electricity_act_2023.json!')
    return sections

if __name__ == '__main__':
    extract_all_electricity_sections()
