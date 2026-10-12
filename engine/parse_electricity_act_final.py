import json
import re

def build_electricity_act():
    with open('data/raw_pdfs/electricity_act_2023_ocr.json') as f:
        pages = json.load(f)

    # 1. Complete TOC Mapping (1 to 233)
    toc_dict = {}
    part_map = {}
    current_part = "Part I — Preliminary Provisions"

    for p_idx in range(1, 8):
        for o in sorted(pages[p_idx], key=lambda x: -x['y']):
            t = o['text'].strip()
            pm = re.match(r'^(PART\s+[IVXLCDM]+)\s*[-—–]\s*(.*)', t, re.IGNORECASE)
            if pm:
                current_part = pm.group(1).upper() + ' — ' + pm.group(2).strip().title()
                continue
            sm = re.match(r'^(\d+)\.?\s+(.*)', t)
            if sm:
                num = int(sm.group(1))
                if 1 <= num <= 233:
                    toc_dict[num] = sm.group(2).strip()
                    part_map[num] = current_part

    overrides = {
        20: "Conclusive evidence of transfer",
        29: "Exemption from stamp duty",
        30: "Corporate governance",
        31: "Incorporation documents of the ISO",
        55: "The financial year of the Commission",
        115: "Power to make regulations",
        126: "Fine for non-payment of money owed",
        129: "Functions and powers of the Agency",
        130: "Establishment and composition of the Governing Board of the Agency",
        155: "Monitoring of rural electrification projects",
        167: "Considerations for renewable purchase obligation",
        170: "Publication of feed-in tariff rates",
        211: "Interference with meters or works of licensees"
    }
    for k, v in overrides.items():
        toc_dict[k] = v

    # 2. Collect substantive lines
    all_lines = []
    for p_idx in range(8, 141):
        obs = sorted(pages[p_idx], key=lambda o: -o['y'])
        is_even = ((p_idx + 1) % 2 == 0)
        for o in obs:
            t = o['text'].strip()
            x = o['x']
            y = o['y']
            w = o['w']
            if not t:
                continue
            if y > 0.82 and ('ELECTRICITY ACT' in t or '2023' in t or 'No.' in t or 'A Bill' in t or 'For' in t):
                continue
            if not is_even and x > 0.74:
                continue
            if is_even and (x + w) < 0.19:
                continue
            if p_idx == 8 and ('ENACTED by' in t or 'Commencement' in t or 'An Act to repeal' in t):
                continue
            if re.match(r'^PART\s+[IVXLCDM]+\s*[-—–]', t, re.IGNORECASE):
                continue
            all_lines.append({
                'page': p_idx + 1,
                'text': t,
                'x': x,
                'y': y,
                'w': w,
                'is_even': is_even
            })

    # 3. Known start patterns / prefixes for all sections
    custom_starts = {
        4: r'^(?:4\.|•\s*\(1\)\s*The\s+National\s+Integrated)',
        5: r'^(?:5\.|5\.\s*\(1\)\s*The\s+Minister)',
        6: r'^(?:6\.|•\s*Without\s+prejudice)',
        19: r'^(?:19\.|•\s*\(1\)\s*The\s+order\s+issued)',
        20: r'^(?:20\.|20\.\s*1\)\s*A\s+stat)',
        21: r'^(?:21\.|(?:\(1\)\s*)?The\s+ISO\s+shall\s+be\s+entitled)',
        40: r'^(?:40\.|[oO0]\.\s*Subject\s+to)',
        42: r'^(?:42\.|(?:\(1\)\s*)?The\s+Commission\s+may\s+make\s+rules\s+for\s+its\s+meetings|meetings\s+and\s+procedure\s+as\s+it\s+deems)',
        48: r'^(?:48\.|8\.\s*\(1\)\s*The\s+Commission\s+shal)',
        49: r'^(?:49\.|(?:\.\s*)?When\s+any\s+matter\s+arises\s+which\s+entails)',
        55: r'^(?:55\.|55,\s*The\s+financial|55,\s*The\s+inneid)',
        56: r'^(?:56\.|56\.\s*\(\s*accounts)',
        57: r'^(?:57\.|37,\s*\(\s*are\s+Comisin|accounts\s+kept\s+by\s+the\s+Commission\s+under\s+section\s+56)',
        64: r'^(?:64\.|1\.\s*\(1\)\s*A\s+licensee\s+shall\s+comply|General\s+duties\s+of\s+licensee)',
        67: r'^(?:67\.|(?:\(1\)\s*)?The\s+system\s+operator\s+shall\s+be\s+licensed|system\s+operation\s+license)',
        69: r'^(?:69\.|(?:\(1\)\s*)?A\s+trading\s+license\s+shall\s+authorise|Trading\s+licenses)',
        72: r'^(?:72\.|2\.\s*\(1\)\s*A\s+license\s+shall\s+be\s+issued\s+subject\s+to\s+such\s+terns)',
        76: r'^(?:76\.|(?:\(1\)\s*)?Where\s+the\s+Commission\s+is\s+satisfied\s+that\s+a\s+licensee|Enforcement\s+of\s+license)',
        79: r'^(?:79\.|(?:\(1\)\s*)?Where\s+no\s+purchase|Provision\s+where\s+no\s+purchase)',
        82: r'^(?:82\.|32\.\s*\(1\)\s*There\s+is\s+established)',
        87: r'^(?:87\.|87\s*\(1\))',
        106: r'^(?:106\.|\.\s*A\s+notice,\s+summons)',
        107: r'^(?:107\.|(?:\(1\)\s*)?Any\s+sum\s+of\s+money|Indemnity)',
        108: r'^(?:108\.|(?:\(1\)\s*)?The\s+Managing\s+Director\s+shall\s+be\s+the\s+accounting|Demarcation\s+of\s+transmission)',
        110: r'^(?:110\.|10\.\s*In\s+giving\s+effect\s+to\s+the\s+provisions\s+of\s+section\s+109)',
        111: r'^(?:111\.|(?:\(1\)\s*)?The\s+Commission\s+may,\s+in\s+consultation|Commission\s+to\s+issue\s+directives)',
        120: r'^(?:120\.|(?:\(1\)\s*)?The\s+Commission\s+shall\s+determine|Performance\s+standards)',
        121: r'^(?:121\.|(?:\(1\)\s*)?A\s+licensee\s+shall\s+not\s+discriminate|Competition\s+and\s+market)',
        122: r'^(?:122\.|(?:\(1\)\s*)?Where\s+a\s+licensee\s+contravenes|Establishment\s+of\s+the\s+Power\s+Consumer)',
        127: r'^(?:127\.|(?:\(1\)\s*)?The\s+Commission\s+shall\s+prescribe|Establishment\s+of\s+the\s+Rural\s+Electrification\s+Agency)',
        136: r'^(?:136\.|6\.\s*\(1\)\s*The\s+Board\s+shall,\s+on\s+the\s+recommendation)',
        137: r'^(?:137\.|(?:\(1\)\s*)?There\s+shall\s+be\s+for\s+the\s+Agency|Managing\s+Director\s+and\s+chief\s+executive)',
        138: r'^(?:138\.|8\.\s*\(1\)\s*The\s+Agency\s+shall\s+have\s+powers)',
        141: r'^(?:141\.|1\.\s*\( academic\s+and\s+Directors)',
        144: r'^(?:144\.|(?:\(1\)\s*)?There\s+is\s+established\s+the\s+Rural\s+Electrification\s+Fund|Management\s+of\s+the\s+REF)',
        151: r'^(?:151\.|15\.\s*\("\s*This\s+With\s+hal\s+have\s+the\s+perisary\s+pote|Supervisory\s+powers\s+of\s+the\s+Minister)',
        157: r'^(?:157\.|(?:\(1\)\s*)?The\s+Agency\s+may\s+accept\s+gifts|Power\s+to\s+borrow)',
        158: r'^(?:158\.|8\.\s*The\s+Agency\s+shall,\s*not\s+later\s+than\s+30\s+September)',
        159: r'^(?:159\.|(?:\(1\)\s*)?The\s+Agency\s+shall\s+keep\s+proper\s+accounts|\bthe\s+Board\s+shall\s+cause\s+the\s+accounts)',
        160: r'^(?:160\.|160\.\s*The\s+Agency\s+shall\s+submit\s+to\s+the\s+Minister)',
        161: r'^(?:161|16|61)\.\s*(?:\([0-9]+\)\s*)?(?:The\s+provision|\(1\)|0\)\s*The\s+provision\s+of\s+te\s+Pubie)',
        166: r'^(?:166\.|(?:\(1\)\s*)?The\s+Commission\s+shall\s+promote\s+renewable|Renewable\s+Energ)',
        170: r'^(?:170|70)\.\s*(?:Feed-in-tariff|\(1\))',
        173: r'^(?:173\.|(?:\(1\)\s*)?There\s+is\s+established\s+for\s+the\s+(?:Agency|NEMSA)\s+a\s+Governing\s+Board|"the\s+Governing\s+Board"\))',
        174: r'^(?:174\.|174\.\s*\(1\)\s*A\s+member\s+of\s+the\s+Governing\s+Board)',
        175: r'^(?:175\.|175\.\s*The\s+Governing\s+Board\s+has\s+the\s+power)',
        176: r'^(?:176\.|176\.\s*Subject\s+to\s+this\s+Act,\s*the\s+NEMSA)',
        177: r'^(?:177\.|17\.\s*\(1\)\s*There\s+is\s+appointed\s+for\s+the\s+NEMSA)',
        179: r'^(?:179|79)\.\s*(?:\([0-9]+\)\s*)?The\s+NEMSA',
        180: r'^(?:180|80)\.\s*The\s+chief\s+executive',
        185: r'^(?:185|18|85)\.\s*(?:There\s+is|\(1\)|Establishment\s+of\s+the\s+National\s+Power\s+Training)',
        187: r'^(?:187\.|187\.\s*\(1\)\s*There\s+is\s+established\s+the\s+Governing\s+Council)',
        189: r'^(?:189\.|189\.\s*The\s+Chairman\s+and\s+other\s+members)',
        190: r'^(?:190|19|90)\.\s*(?:Notwithstanding|\(1\)|19\.\s*Now\s+insanding)',
        192: r'^(?:192|12|92)\.\s*(?:To\s+the|Where|\(1\)|12\.\s*To\s+tie\s+hal\s+vie\s+son)',
        197: r'^(?:197|19|97)\.\s*(?:The\s+Academic|\(1\))',
        199: r'^(?:199|19|99)\.\s*(?:The\s+Institute|\(1\))',
        202: r'^(?:202|20|02)\.\s*(?:There\s+is|\(1\))',
        205: r'^(?:205|15|05)\.\s*(?:The\s+Minister|15\.\s*The\s+Minister\s+shall\s+exercise)',
        207: r'^(?:207|20|07)\.\s*(?:The\s+Minister|\(1\)|Power\s+to\s+make\s+regulations)',
        213: r'^(?:213|21|13)\.\s*(?:A\s+person|\(1\)|Intentionally\s+disrupting)',
        214: r'^(?:214|21|14)\.\s*(?:A\s+person|\(1\)|Offence\s+relating\s+to\s+damage)',
        221: r'^(?:221|1|21)\.\s*(?:The\s+Attorney-General|Ine\s+Attorney)',
        222: r'^(?:222|22|2)\.\s*(?:\([0-9]+\)\s*)?Notwithstanding',
        228: r'^(?:228|28|8)\.\s*Without\s+prejudice',
        231: r'^(?:231\.|231\.\s*\(1\)\s*Except\s+as\s+otherwise)',
        232: r'^(?:232\.|232\.\s*In\s+this\s+ACT|232\.\s*In\s+this\s+Act)',
        233: r'^(?:233\.|233\.\s*This\s+Act\s+may\s+be\s+cited|This\s+Act\s+may\s+be\s+cited\s+as\s+the\s+Electricity\s+Act)'
    }

    def matches_section(s, text):
        if s in custom_starts:
            if re.search(custom_starts[s], text, re.IGNORECASE):
                return True
        return bool(re.search(rf'^(?:{s}\.|\b{s}\s*\(1\)|\b{s}\.—)', text))

    # Sequential Search with local window
    sec_starts = {1: 0}
    last_idx = 0

    for s in range(2, 234):
        found = None
        # Sec 233 is at the very end (page 141) after 232 which is long
        lookahead = len(all_lines) if s == 233 else min(len(all_lines), last_idx + 180)
        for i in range(last_idx + 1, lookahead):
            t = all_lines[i]['text']
            if matches_section(s, t):
                found = i
                break
        if found is not None:
            sec_starts[s] = found
            last_idx = found
        else:
            # Fallback: find closest match in next 100 lines
            for i in range(last_idx + 1, min(len(all_lines), last_idx + 100)):
                t = all_lines[i]['text']
                if str(s) in t:
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
        # Clean schedule mentions at the end of section 233
        if s_num == 233:
            content = re.split(r'FIRST SCHEDULE|SCHEDULES', content)[0].strip()

        title = toc_dict.get(s_num, f'Section {s_num}')
        part = part_map.get(s_num, 'Part I — Preliminary Provisions')
        sections.append({
            'section_number': str(s_num),
            'title': title,
            'content': content,
            'part': part
        })

    print(f'Constructed all {len(sections)} sections for Electricity Act, 2023')

    output = {
        'statute_title': 'Electricity Act, 2023',
        'year': 2023,
        'citation': 'Act No. 24 of 2023',
        'sections': sections
    }

    with open('data/json_laws/electricity_act_2023.json', 'w') as f:
        json.dump(output, f, indent=2)

    print('SAVED data/json_laws/electricity_act_2023.json')
    return output

if __name__ == '__main__':
    build_electricity_act()
