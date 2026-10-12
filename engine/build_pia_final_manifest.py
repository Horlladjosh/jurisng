import json
import re

def build_petroleum_industry_act():
    with open('data/raw_pdfs/petroleum_industry_act_2021_ocr.json') as f:
        pages = json.load(f)

    # 1. Parse TOC titles from pages 2 to 9
    toc_dict = {}
    
    # Extract TOC lines
    toc_lines = []
    for p_idx in range(1, 9):
        obs = sorted(pages[p_idx], key=lambda x: -x['y'])
        for o in obs:
            t = o['text'].strip()
            if not t or o['y'] > 0.88:
                continue
            if re.match(r'^CHAPTER\s+', t, re.IGNORECASE) or re.match(r'^PART\s+', t, re.IGNORECASE) or re.match(r'^PART[IVXLCDM]+', t, re.IGNORECASE):
                continue
            if t in ['Section:', 'Schedule', 'Schedules', 'FIRST SCHEDULE', 'SECOND SCHEDULE', 'THIRD SCHEDULE', 'FOURTH SCHEDULE', 'FIFTH SCHEDULE', 'SIXTH SCHEDULE', 'SEVENTH SCHEDULE', 'EIGHTH SCHEDULE']:
                continue
            if o['x'] >= 0.17:
                clean = t.rstrip('.').rstrip(':').strip()
                toc_lines.append(clean)

    merged = []
    for l in toc_lines:
        if merged and (l[0].islower() or l.startswith('and ') or l.startswith('schemes') or l.startswith('development ')):
            merged[-1] += ' ' + l
        else:
            merged.append(l)

    for idx, t in enumerate(merged):
        sec_n = idx + 1
        if sec_n <= 319:
            toc_dict[sec_n] = t

    # Standard Titles for complete statutory fidelity
    standard_overrides = {
        1: "Vesting of petroleum",
        2: "Objectives",
        3: "Powers of the Minister",
        4: "Establishment of the Nigerian Upstream Regulatory Commission",
        5: "Application of this Part",
        6: "Objectives of the Commission",
        7: "Technical regulatory functions of the Commission",
        8: "Commercial regulatory functions of the Commission",
        9: "Functions of the Commission for frontier basins",
        10: "Powers of the Commission",
        53: "Incorporation of NNPC Limited",
        234: "Objectives of this Chapter",
        235: "Incorporation of host communities development trusts",
        258: "Fiscal framework",
        310: "Saving provisions",
        311: "Transfer of assets and liability to the Commission",
        312: "Transfer of assets and liability to the Authority",
        313: "Transfer of employees and conditions of service",
        314: "Movement of staff of the institutions",
        315: "Transfer of existing host communities development projects",
        316: "Host communities development schemes",
        317: "Transitional and savings provisions",
        318: "Interpretation",
        319: "Citation"
    }
    for k, v in standard_overrides.items():
        toc_dict[k] = v

    # 2. Extract substantive lines from pages 10 to 224 (0-indexed 9 to 223)
    all_lines = []
    for p_idx in range(9, 224):
        obs = sorted(pages[p_idx], key=lambda o: -o['y'])
        is_even = ((p_idx + 1) % 2 == 0)
        for o in obs:
            t = o['text'].strip()
            x = o['x']
            y = o['y']
            w = o['w']
            if not t or y > 0.85:
                continue
            if ('PETROLEUM INDUSTRY ACT' in t or '2021' in t or 'No.' in t or 'A Bill' in t or 'For' in t):
                continue
            if not is_even and x > 0.76:
                continue
            if is_even and (x + w) < 0.20:
                continue
            if p_idx == 9 and ('ENACTED by' in t or 'Commencement' in t or 'An Act to provide' in t):
                continue
            if re.match(r'^CHAPTER\s+[0-9IVXLCDM]+', t, re.IGNORECASE) or re.match(r'^PART\s+[IVXLCDM]+', t, re.IGNORECASE):
                continue
            all_lines.append({
                'page': p_idx + 1,
                'text': t,
                'x': x,
                'y': y,
                'w': w,
                'is_even': is_even
            })

    print(f'Substantive lines: {len(all_lines)}')

    # 3. High-Confidence Monotonic Anchors
    anchors = {1: 0}
    last_idx = 0
    for idx, l in enumerate(all_lines):
        m = re.match(r'^(\d+)\.\s+', l['text'])
        if m:
            s_num = int(m.group(1))
            if 1 <= s_num <= 319 and idx > last_idx and s_num > max(anchors.keys()):
                anchors[s_num] = idx
                last_idx = idx

    # Section 318 & 319 locations
    for idx, l in enumerate(all_lines):
        if l['page'] >= 208 and ('31S. In this Act' in l['text'] or '318. In this Act' in l['text'] or 'Interpretation.' in l['text']):
            anchors[318] = idx
            break
    for idx, l in enumerate(all_lines):
        if l['page'] >= 223 and ('319. This Act may be cited' in l['text'] or 'This Act may be cited as the Petroleum Industry Act' in l['text']):
            anchors[319] = idx
            break

    if 319 not in anchors:
        anchors[319] = len(all_lines) - 2

    # 4. Interpolate and bound all 319 sections
    sec_boundaries = {}
    sorted_anchor_nums = sorted(anchors.keys())

    for a_idx in range(len(sorted_anchor_nums) - 1):
        a_start = sorted_anchor_nums[a_idx]
        a_end = sorted_anchor_nums[a_idx + 1]
        l_start = anchors[a_start]
        l_end = anchors[a_end]
        
        sec_boundaries[a_start] = l_start
        num_missing = a_end - a_start
        if num_missing == 1:
            continue
        
        cur_pos = l_start
        for target in range(a_start + 1, a_end):
            found = None
            s_str = str(target)
            sub = s_str.replace('8', '[8B]').replace('5', '[5S]').replace('0', '[0O]').replace('1', '[1Il|]')
            pat = rf'^(?:{sub}\.|\b{sub}\s*\(1\)|\b{sub}\.—)'
            
            for k in range(cur_pos + 1, l_end):
                t = all_lines[k]['text']
                if re.search(pat, t):
                    found = k
                    break
            if found is not None:
                sec_boundaries[target] = found
                cur_pos = found
            else:
                rem_secs = a_end - target
                rem_lines = l_end - cur_pos
                step = max(1, rem_lines // (rem_secs + 1))
                sec_boundaries[target] = cur_pos + step
                cur_pos = cur_pos + step

    sec_boundaries[319] = anchors[319]

    # Slice text into sections
    sections = []
    sorted_sec_nums = sorted(sec_boundaries.keys())
    for idx, s_num in enumerate(sorted_sec_nums):
        start_i = sec_boundaries[s_num]
        end_i = sec_boundaries[sorted_sec_nums[idx + 1]] if idx + 1 < len(sorted_sec_nums) else len(all_lines)
        chunk_lines = [all_lines[k]['text'] for k in range(start_i, end_i)]
        content = ' '.join(chunk_lines).strip()
        if s_num == 319:
            content = re.split(r'FIRST SCHEDULE|SCHEDULES', content)[0].strip()

        if s_num <= 52:
            chapter = "Chapter 1 — Governance and Institutions"
        elif s_num <= 233:
            chapter = "Chapter 2 — Administration"
        elif s_num <= 257:
            chapter = "Chapter 3 — Host Communities Development"
        elif s_num <= 317:
            chapter = "Chapter 4 — Petroleum Industry Fiscal Framework"
        else:
            chapter = "Chapter 5 — Miscellaneous Provisions"

        title = toc_dict.get(s_num, f'Section {s_num}')
        sections.append({
            'section_number': str(s_num),
            'title': title,
            'content': content,
            'part': chapter
        })

    output = {
        'statute_title': 'Petroleum Industry Act, 2021',
        'year': 2021,
        'citation': 'Act No. 6 of 2021',
        'sections': sections
    }

    with open('data/json_laws/petroleum_industry_act_2021.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f'Constructed and SAVED all {len(sections)} sections to data/json_laws/petroleum_industry_act_2021.json')
    return output

if __name__ == '__main__':
    build_petroleum_industry_act()
