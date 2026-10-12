import json
import re

def build_manifest():
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

    # 2. Extract Substantive Page text
    # Clean text page by page
    clean_pages_text = []
    for p_idx in range(8, 141):
        obs = sorted(pages[p_idx], key=lambda o: -o['y'])
        is_even = ((p_idx + 1) % 2 == 0)
        lines = []
        for o in obs:
            t = o['text'].strip()
            x = o['x']
            y = o['y']
            w = o['w']

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

            # Fix specific known OCR anomalies on section numbers
            if p_idx == 11 and t.startswith('• (1)'):
                t = '4. (1)' + t[5:]
            elif p_idx == 54 and t.startswith('32. (1) There is established: the Nation'): # N-HYPPADEC section 82
                t = '82. (1)' + t[7:]
            elif p_idx == 65 and t.startswith('10. In giving effect'): # Section 110
                t = '110. In giving effect'
            elif p_idx == 80 and t.startswith('6. (1) The Board shall'): # Section 136
                t = '136. (1) The Board shall'
            elif p_idx == 81 and t.startswith('8. (1) The Agency shall'): # Section 138
                t = '138. (1) The Agency shall'
            elif p_idx == 82 and t.startswith('1. ( academic'): # Section 141
                t = '141. (1) Functions of Executive Directors'
            elif p_idx == 88 and t.startswith('15. (" This With hal have'): # Section 151
                t = '151. (1) Supervisory powers'
            elif p_idx == 91 and t.startswith('8. The Agency shall, not later'): # Section 158
                t = '158. The Agency shall, not later'
            elif p_idx == 92 and t.startswith('16. 0) The provision'): # Section 161
                t = '161. (1) The provision'
            elif p_idx == 97 and t.startswith('70. Feed-in-tariff'): # Section 170
                t = '170. Feed-in-tariff'
            elif p_idx == 102 and t.startswith('17. (1) There is appointed'): # Section 177
                t = '177. (1) There is appointed'
            elif p_idx == 104 and t.startswith('79. (1) The NEMSA'): # Section 179
                t = '179. (1) The NEMSA'
            elif p_idx == 105 and t.startswith('80. The chief executive'): # Section 180
                t = '180. The chief executive'
            elif p_idx == 110 and t.startswith('19. Now insanding'): # Section 190
                t = '190. Cessation of membership'
            elif p_idx == 111 and t.startswith('12. To tie hal vie'): # Section 192
                t = '192. Filling of vacancies'
            elif p_idx == 115 and t.startswith('15. The Minister shall'): # Section 205
                t = '205. The Minister shall'
            elif p_idx == 115 and t.startswith('208. (1) A person who'): # Section 208
                t = '208. (1) A person who'
            elif p_idx == 119 and t.startswith('1. Ine Attorney-General'): # Section 221
                t = '221. The Attorney-General'
            elif p_idx == 119 and t.startswith('22. (1) Notwithstanding'): # Section 222
                t = '222. (1) Notwithstanding'
            elif p_idx == 122 and t.startswith('28. Without prejudice'): # Section 228
                t = '228. Without prejudice'

            lines.append(t)
        clean_pages_text.append('\n'.join(lines))

    full_body = '\n'.join(clean_pages_text)

    # 3. Step through all 233 sections
    sections = []
    current_sec = 1
    current_lines = []

    lines = full_body.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        next_sec = current_sec + 1
        is_next = False
        if next_sec <= 233:
            if re.match(rf'^{next_sec}\.\s+', line):
                is_next = True

        if is_next:
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
        else:
            current_lines.append(line)

    # Final section 233
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

    print(f'Total Segmented Sections: {len(sections)} (target: 233)')
    missing = [i for i in range(1, 234) if str(i) not in [s['section_number'] for s in sections]]
    if missing:
        print(f'Missing section numbers: {missing}')

    output_data = {
        'statute_title': 'Electricity Act, 2023',
        'year': 2023,
        'citation': 'Act No. 24 of 2023',
        'sections': sections
    }

    with open('data/json_laws/electricity_act_2023.json', 'w') as f:
        json.dump(output_data, f, indent=2)

    return sections

if __name__ == '__main__':
    build_manifest()
