import json
import re

def build_pia_act_certified():
    with open('data/raw_pdfs/petroleum_industry_act_2021_ocr.json') as f:
        pages = json.load(f)

    # 1. Parse TOC titles from pages 2 to 9
    toc_dict = {}
    
    # Collect titles
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

    # Merge continuation lines
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

    # Fallback overrides for standard titles
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

    print(f'Total substantive lines: {len(all_lines)}')

    # 3. Custom start regexes
    custom_starts = {
        1: r'^(?:1\.|1\.\s*\(1\)\s*The\s+entire\s+property|The\s+entire\s+property\s+and\s+control\s+of\s+all\s+petroleum)',
        2: r'^(?:2\.|The\s+primary\s+objective\s+of\s+this\s+Act\s+is\s+to|Objectives\.)',
        3: r'^(?:3\.|3\.\s*\(1\)\s*The\s+Minister\s+shall|Powers\s+of\s+the\s+Minister)',
        4: r'^(?:4\.|4\.\s*\(1\)\s*There\s+is\s+established\s+the\s+Nigerian\s+Upstream)',
        5: r'^(?:5\.|5\.\s*The\s+objects\s+and\s+functions\s+of\s+the\s+Commission)',
        6: r'^(?:6\.|6\.\s*The\s+objectives\s+of\s+the\s+Commission)',
        7: r'^(?:7\.|7\.\s*The\s+technical\s+regulatory\s+functions)',
        8: r'^(?:8\.|B\.\s*The\s+commercial\s+regulatory|8\.\s*The\s+commercial\s+regulatory|Commercial\s+regulatory\s+functions)',
        21: r'^(?:21\.|(?:\(1\)\s*)?The\s+Commission\s+shall\s+pay\s+its\s+employees|Remuneration\s+and\s+allowances)',
        53: r'^(?:53\.|53\.\s*\(1\)\s*The\s+Minister\s+shall\s+within\s+six\s+months|The\s+Minister\s+shall\s+cause\s+to\s+be\s+incorporated)',
        234: r'^(?:234\.|234\.\s*\(1\)\s*The\s+objectives\s+of\s+this\s+Chapter|Objectives\s+of\s+this\s+Chapter)',
        258: r'^(?:258\.|258\.\s*\(1\)\s*The\s+objectives\s+of\s+this\s+Chapter|Fiscal\s+framework)',
        318: r'^(?:318\.|318\.\s*In\s+this\s+Act|Interpretation)',
        319: r'^(?:319\.|319\.\s*This\s+Act\s+may\s+be\s+cited|This\s+Act\s+may\s+be\s+cited\s+as\s+the\s+Petroleum\s+Industry\s+Act)'
    }

    def matches_section(s, text):
        if s in custom_starts:
            if re.search(custom_starts[s], text, re.IGNORECASE):
                return True
        s_str = str(s)
        sub = s_str.replace('8', '[8B]').replace('5', '[5S]').replace('0', '[0O]')
        return bool(re.search(rf'^(?:{sub}\.|\b{sub}\s*\(1\)|\b{sub}\.—)', text))

    # Sequential search with local window
    sec_starts = {1: 0}
    last_idx = 0

    for s in range(2, 320):
        found = None
        lookahead = len(all_lines) if s == 319 else min(len(all_lines), last_idx + 180)
        for i in range(last_idx + 1, lookahead):
            t = all_lines[i]['text']
            if matches_section(s, t):
                found = i
                break
        if found is not None:
            sec_starts[s] = found
            last_idx = found
        else:
            # Fallback search
            for i in range(last_idx + 1, min(len(all_lines), last_idx + 60)):
                t = all_lines[i]['text']
                if re.search(rf'\b{s}\b', t):
                    found = i
                    break
            if found is not None:
                sec_starts[s] = found
                last_idx = found
            else:
                sec_starts[s] = last_idx + 1
                last_idx = last_idx + 1

    # Slice text into sections
    sections = []
    sorted_sec_nums = sorted(sec_starts.keys())
    for idx, s_num in enumerate(sorted_sec_nums):
        start_i = sec_starts[s_num]
        end_i = sec_starts[sorted_sec_nums[idx + 1]] if idx + 1 < len(sorted_sec_nums) else len(all_lines)
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
    build_pia_act_certified()
