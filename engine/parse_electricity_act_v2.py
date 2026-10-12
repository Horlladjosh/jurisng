import json
import re

def build_electricity_act_manifest():
    with open('data/raw_pdfs/electricity_act_2023_ocr.json') as f:
        pages = json.load(f)

    # 1. Complete TOC Mapping for all 233 sections
    # Extract TOC from pages 2 to 8
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

    # Fallback / missing TOC entries cleanup
    known_titles = {
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
        211: "Interference with meters or works of licensees"
    }
    for num, title in known_titles.items():
        if num not in toc_dict or len(toc_dict[num]) < 3:
            toc_dict[num] = title

    print(f'Total TOC Titles Ready: {len(toc_dict)}')

    # 2. Extract substantive pages 9 to 151
    # Line by line extraction
    page_lines_list = []
    for p_idx in range(8, len(pages)):
        page_obs = pages[p_idx]
        is_even = ((p_idx + 1) % 2 == 0)
        sorted_obs = sorted(page_obs, key=lambda o: -o['y'])
        
        lines = []
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
            # Certification stop
            if 'I, CERTIFY, IN ACCORDANCE' in t or 'CLERK TO THE NATIONAL ASSEMBLY' in t:
                break
            # Skip Part banner
            if re.match(r'^PART\s+[IVXLCDM]+\s*[-—–]', t, re.IGNORECASE):
                continue
            lines.append(t)
        page_lines_list.append('\n'.join(lines))

    full_text = '\n'.join(page_lines_list)

    # 3. Sequential State-Machine Segmentation for Sections 1 to 233
    sections = []
    current_sec_num = 1
    current_sec_lines = []

    lines = full_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        next_sec = current_sec_num + 1
        
        # Check if this line starts current_sec_num (for sec 1) or next_sec
        # Regex for section start: e.g. "2. (1) Subject to..." or "2. Subject to..." or "2.—(1)"
        start_m = None
        if current_sec_num == 1 and not sections:
            start_m = re.match(r'^1\.\s+(.*)', line)
            if start_m:
                current_sec_lines.append(line)
                i += 1
                continue
                
        if next_sec <= 233:
            next_m = re.match(rf'^{next_sec}\.\s+(.*)', line)
            if next_m:
                # Save previous section
                sec_content = ' '.join([l.strip() for l in current_sec_lines if l.strip()])
                title = toc_dict.get(current_sec_num, f'Section {current_sec_num}')
                part = part_map.get(current_sec_num, 'Part I — Preliminary Provisions')
                sections.append({
                    'section_number': str(current_sec_num),
                    'title': title,
                    'content': sec_content,
                    'part': part
                })
                # Advance to next section
                current_sec_num = next_sec
                current_sec_lines = [line]
                i += 1
                continue

        current_sec_lines.append(line)
        i += 1

    # Save final section 233
    if current_sec_lines:
        sec_content = ' '.join([l.strip() for l in current_sec_lines if l.strip()])
        # Trim schedules if present
        sec_content = re.split(r'SCHEDULES|FIRST SCHEDULE', sec_content)[0].strip()
        title = toc_dict.get(current_sec_num, f'Section {current_sec_num}')
        part = part_map.get(current_sec_num, 'Part XXII — Final Provisions')
        sections.append({
            'section_number': str(current_sec_num),
            'title': title,
            'content': sec_content,
            'part': part
        })

    print(f'Successfully segmented {len(sections)} sections (target: 233)')

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
    build_electricity_act_manifest()
