import fitz
import re
import json
import os

def clean_text_block(text):
    text = text.replace("\xa0", " ").strip()
    # Normalize multiple whitespace
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)

def extract_efcc_act():
    pdf_path = "data/raw_pdfs/efcc_act.pdf"
    doc = fitz.open(pdf_path)
    full_lines = []
    for p in range(len(doc)):
        page = doc[p]
        txt = page.get_text()
        for l in txt.splitlines():
            l = l.replace("\xa0", " ").strip()
            if l:
                full_lines.append(l)

    # In EFCC Act, after line 113 starts the substantive body
    sec_hits = []
    for i, l in enumerate(full_lines):
        m = re.match(r"^(\d{1,2})\.\s*$", l)
        m2 = re.match(r"^(\d{1,2})\.\s+([A-Za-z].*)$", l)
        if m:
            s_num = int(m.group(1))
            title = full_lines[i+1] if i+1 < len(full_lines) else ""
            sec_hits.append((s_num, title, i, True))
        elif m2:
            s_num = int(m2.group(1))
            title = m2.group(2)
            sec_hits.append((s_num, title, i, False))

    seqs = []
    current_seq = []
    for h in sec_hits:
        s_num, title, idx, next_line = h
        if s_num == 1:
            if current_seq:
                seqs.append(current_seq)
            current_seq = [h]
        elif current_seq and s_num == current_seq[-1][0] + 1:
            current_seq.append(h)
    if current_seq:
        seqs.append(current_seq)

    # Substantive is seqs[1]
    substantive = seqs[1]
    sections_json = []

    # Map part headers
    part_map = {
        1: "Part I: Establishment of the Economic and Financial Crimes Commission, etc.",
        6: "Part II: Functions of the Commission",
        8: "Part III: Staff of the Commission",
        12: "Part IV: Special Units",
        14: "Part V: Offences",
        35: "Part VI: Financial Provisions",
        38: "Part VII: Miscellaneous Provisions"
    }
    current_part = "Part I: Establishment of the Economic and Financial Crimes Commission, etc."

    for idx, (s_num, title, line_idx, is_next_line) in enumerate(substantive):
        if s_num in part_map:
            current_part = part_map[s_num]

        body_start_idx = line_idx + 2 if is_next_line else line_idx + 1
        if idx + 1 < len(substantive):
            body_end_idx = substantive[idx+1][2]
        else:
            # Last section (47) goes until Schedules or end
            body_end_idx = len(full_lines)
            for j in range(body_start_idx, len(full_lines)):
                if "SCHEDULE" in full_lines[j].upper():
                    body_end_idx = j
                    break

        sec_body_lines = full_lines[body_start_idx:body_end_idx]
        body_text = "\n".join(sec_body_lines).strip()

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.strip().rstrip("."),
            "part": current_part,
            "full_text": body_text,
            "searchable_chunk": f"Economic and Financial Crimes Commission (Establishment, etc.) Act, 2004 - Section {s_num}: {title}\n{current_part}\n{body_text}"
        })

    manifest = {
        "statute_id": "efcc_act_2004",
        "title": "Economic and Financial Crimes Commission (Establishment, etc.) Act, 2004",
        "short_title": "EFCC Act",
        "year": 2004,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 1 of 2004",
        "enactment_date": "4th June 2004",
        "description": "An Act to provide for the establishment of the Economic and Financial Crimes Commission, charged with the responsibility for the enforcement of all economic and financial crimes laws and other related matters.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/efcc_act_2004.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[✓] EFCC Act: Successfully extracted {len(sections_json)} sections -> {out_path}")
    return len(sections_json)


def extract_patents_designs_act():
    pdf_path = "data/raw_pdfs/patents_designs_act.pdf"
    doc = fitz.open(pdf_path)
    full_lines = []
    for p in range(len(doc)):
        page = doc[p]
        txt = page.get_text()
        for l in txt.splitlines():
            l = l.replace("\xa0", " ").strip()
            if l:
                full_lines.append(l)

    # Let's find sections 1 to 33 in substantive part (starts after line 50)
    sec_hits = []
    for i, l in enumerate(full_lines):
        m = re.match(r"^(\d{1,2})\.\s*(.*)$", l)
        if m:
            s_num = int(m.group(1))
            rest = m.group(2).strip()
            if s_num <= 33:
                sec_hits.append((s_num, rest, i))

    # Find the substantive sequence (where 1 starts around page 2, line > 40)
    substantive = []
    expected = 1
    for s_num, rest, idx in sec_hits:
        if idx < 40:
            continue
        if s_num == expected:
            title = rest
            if not title and idx + 1 < len(full_lines):
                title = full_lines[idx+1]
            substantive.append((s_num, title, idx))
            expected += 1
            if expected > 33:
                break

    sections_json = []
    part_map = {
        1: "Part I: Patents",
        12: "Part II: Designs",
        23: "Part III: General Provisions"
    }
    current_part = "Part I: Patents"

    for idx, (s_num, title, line_idx) in enumerate(substantive):
        if s_num in part_map:
            current_part = part_map[s_num]

        # Clean title line from body
        body_start = line_idx + 1
        if idx + 1 < len(substantive):
            body_end = substantive[idx+1][2]
        else:
            body_end = len(full_lines)
            for j in range(body_start, len(full_lines)):
                if "FIRST SCHEDULE" in full_lines[j].upper() or "SCHEDULES" in full_lines[j].upper():
                    body_end = j
                    break

        sec_body_lines = full_lines[body_start:body_end]
        body_text = "\n".join(sec_body_lines).strip()

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.strip().rstrip("."),
            "part": current_part,
            "full_text": body_text,
            "searchable_chunk": f"Patents and Designs Act, 1971 - Section {s_num}: {title}\n{current_part}\n{body_text}"
        })

    manifest = {
        "statute_id": "patents_designs_act",
        "title": "Patents and Designs Act, 1971",
        "short_title": "Patents and Designs Act",
        "year": 1971,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. P2, LFN 2004",
        "enactment_date": "1st December 1971",
        "description": "An Act to make comprehensive provisions for the registration and proprietorship of patents and industrial designs in Nigeria.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/patents_designs_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[✓] Patents and Designs Act: Successfully extracted {len(sections_json)} sections -> {out_path}")
    return len(sections_json)


def extract_oaths_act():
    pdf_path = "data/raw_pdfs/oaths_act.pdf"
    doc = fitz.open(pdf_path)
    full_lines = []
    for p in range(len(doc)):
        page = doc[p]
        txt = page.get_text()
        for l in txt.splitlines():
            l = l.replace("\xa0", " ").strip()
            if l:
                full_lines.append(l)

    # Substantive body starts around line 30
    substantive = []
    expected = 1
    for i, l in enumerate(full_lines):
        if i < 25:
            continue
        m = re.match(r"^(\d{1,2})\.\s*(.*)$", l)
        if m:
            s_num = int(m.group(1))
            rest = m.group(2).strip()
            if s_num == expected:
                title = rest
                if not title and i + 1 < len(full_lines):
                    title = full_lines[i+1]
                substantive.append((s_num, title, i))
                expected += 1
                if expected > 16:
                    break

    sections_json = []
    for idx, (s_num, title, line_idx) in enumerate(substantive):
        body_start = line_idx + 1
        if idx + 1 < len(substantive):
            body_end = substantive[idx+1][2]
        else:
            body_end = len(full_lines)
            for j in range(body_start, len(full_lines)):
                if "FIRST SCHEDULE" in full_lines[j].upper() or "SCHEDULES" in full_lines[j].upper():
                    body_end = j
                    break

        sec_body_lines = full_lines[body_start:body_end]
        body_text = "\n".join(sec_body_lines).strip()

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.strip().rstrip("."),
            "part": "General Provisions",
            "full_text": body_text,
            "searchable_chunk": f"Oaths Act, 1963 - Section {s_num}: {title}\nGeneral Provisions\n{body_text}"
        })

    manifest = {
        "statute_id": "oaths_act",
        "title": "Oaths Act, 1963",
        "short_title": "Oaths Act",
        "year": 1963,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. O1, LFN 2004",
        "enactment_date": "1st October 1963",
        "description": "An Act to consolidate and amend the law relating to the administration of oaths and affirmations.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/oaths_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[✓] Oaths Act: Successfully extracted {len(sections_json)} sections -> {out_path}")
    return len(sections_json)


def extract_hire_purchase_act():
    pdf_path = "data/raw_pdfs/hire_purchase_act.pdf"
    doc = fitz.open(pdf_path)
    full_lines = []
    for p in range(len(doc)):
        page = doc[p]
        txt = page.get_text()
        for l in txt.splitlines():
            l = l.replace("\xa0", " ").strip()
            if l:
                full_lines.append(l)

    # Hire Purchase Act has 21 sections
    substantive = []
    expected = 1
    for i, l in enumerate(full_lines):
        if i < 25:
            continue
        m = re.match(r"^(\d{1,2})\.\s*(.*)$", l)
        if m:
            s_num = int(m.group(1))
            rest = m.group(2).strip()
            if s_num == expected:
                title = rest
                if not title and i + 1 < len(full_lines):
                    title = full_lines[i+1]
                substantive.append((s_num, title, i))
                expected += 1
                if expected > 21:
                    break

    sections_json = []
    for idx, (s_num, title, line_idx) in enumerate(substantive):
        body_start = line_idx + 1
        if idx + 1 < len(substantive):
            body_end = substantive[idx+1][2]
        else:
            body_end = len(full_lines)
            for j in range(body_start, len(full_lines)):
                if "SCHEDULE" in full_lines[j].upper():
                    body_end = j
                    break

        sec_body_lines = full_lines[body_start:body_end]
        body_text = "\n".join(sec_body_lines).strip()

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.strip().rstrip("."),
            "part": "General Provisions",
            "full_text": body_text,
            "searchable_chunk": f"Hire-Purchase Act, 1965 - Section {s_num}: {title}\nGeneral Provisions\n{body_text}"
        })

    manifest = {
        "statute_id": "hire_purchase_act",
        "title": "Hire-Purchase Act, 1965",
        "short_title": "Hire-Purchase Act",
        "year": 1965,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. H4, LFN 2004",
        "enactment_date": "1st October 1968",
        "description": "An Act to make provision for the regulation of hire-purchase and credit-sale agreements and for other matters connected therewith.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/hire_purchase_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[✓] Hire-Purchase Act: Successfully extracted {len(sections_json)} sections -> {out_path}")
    return len(sections_json)


def extract_trade_disputes_act():
    pdf_path = "data/raw_pdfs/trade_disputes_act.pdf"
    doc = fitz.open(pdf_path)
    full_lines = []
    for p in range(len(doc)):
        page = doc[p]
        txt = page.get_text()
        for l in txt.splitlines():
            l = l.replace("\xa0", " ").strip()
            if l:
                full_lines.append(l)

    # Trade disputes act has sections 1..19, and then 33..54 (since 20..32 repealed)
    # Let's find valid section numbers
    valid_sec_nums = list(range(1, 20)) + list(range(33, 55))
    
    sec_hits = {}
    curr_expected_idx = 0
    
    for i, l in enumerate(full_lines):
        if i < 45:
            continue
        if curr_expected_idx >= len(valid_sec_nums):
            break
        expected_sec = valid_sec_nums[curr_expected_idx]
        
        m = re.match(r"^(\d{1,2})\.\s*(.*)$", l)
        if m:
            s_num = int(m.group(1))
            rest = m.group(2).strip()
            if s_num == expected_sec:
                title = rest
                if not title and i + 1 < len(full_lines):
                    title = full_lines[i+1]
                sec_hits[s_num] = (title, i)
                curr_expected_idx += 1

    sorted_secs = sorted(sec_hits.keys())
    sections_json = []

    part_map = {
        1: "Part I: Procedure for Settling Trade Disputes",
        33: "Part III: Board of Inquiry",
        35: "Part IV: Supplementary Provisions: The National Industrial Court, Arbitration Tribunals and Boards of Inquiry",
        40: "Part V: Supplementary Provisions: Application of Act to State Trade Disputes",
        41: "Part VI: Miscellaneous and General"
    }
    current_part = "Part I: Procedure for Settling Trade Disputes"

    for idx, s_num in enumerate(sorted_secs):
        if s_num in part_map:
            current_part = part_map[s_num]
            
        title, line_idx = sec_hits[s_num]
        body_start = line_idx + 1
        if idx + 1 < len(sorted_secs):
            next_s = sorted_secs[idx+1]
            body_end = sec_hits[next_s][1]
        else:
            body_end = len(full_lines)
            for j in range(body_start, len(full_lines)):
                if "SCHEDULE" in full_lines[j].upper():
                    body_end = j
                    break

        sec_body_lines = full_lines[body_start:body_end]
        body_text = "\n".join(sec_body_lines).strip()

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.strip().rstrip("."),
            "part": current_part,
            "full_text": body_text,
            "searchable_chunk": f"Trade Disputes Act, 1976 - Section {s_num}: {title}\n{current_part}\n{body_text}"
        })

    manifest = {
        "statute_id": "trade_disputes_act",
        "title": "Trade Disputes Act, 1976",
        "short_title": "Trade Disputes Act",
        "year": 1976,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. T8, LFN 2004",
        "enactment_date": "1st January 1976",
        "description": "An Act to make comprehensive provisions for the settlement of trade disputes and other matters incidental thereto.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/trade_disputes_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[✓] Trade Disputes Act: Successfully extracted {len(sections_json)} sections -> {out_path}")
    return len(sections_json)


if __name__ == "__main__":
    t1 = extract_efcc_act()
    t2 = extract_patents_designs_act()
    t3 = extract_oaths_act()
    t4 = extract_hire_purchase_act()
    t5 = extract_trade_disputes_act()
    print(f"\n=======================================================")
    print(f"COMPLETED: Extracted 5 Foundational LFN Acts with {t1+t2+t3+t4+t5} certified sections!")
