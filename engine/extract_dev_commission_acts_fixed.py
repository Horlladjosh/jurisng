import json
import re
import os

def clean_txt(s):
    s = s.replace("\xa0", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def extract_from_line_splits(ocr_path, sub_start, sub_end, sec_definitions, statute_id, title, short_title, year, gazette_no, enact_date, desc, out_file):
    print(f"\n[*] Extracting {title}...")
    with open(ocr_path) as f:
        pages = json.load(f)

    sub_lines = []
    for p in pages[sub_start:sub_end]:
        for l in p:
            l = clean_txt(l)
            if not l: continue
            if "COMMISSION (ESTABLISHMENT) ACT" in l.upper() and len(l) < 70: continue
            if re.search(r"^\d+$", l): continue
            sub_lines.append(l)

    # Locate each section start in sub_lines
    splits = []
    curr_idx = 0
    for s_num, s_title, part, patterns in sec_definitions:
        found_idx = None
        for i in range(curr_idx, len(sub_lines)):
            l = sub_lines[i]
            if any(re.search(p, l) for p in patterns):
                found_idx = i
                break
        if found_idx is not None:
            splits.append((s_num, s_title, part, found_idx))
            curr_idx = found_idx + 1
        else:
            print(f"    [!] Warning: Missing section {s_num}: {s_title}")

    sections_json = []
    for i, (s_num, s_title, part, line_idx) in enumerate(splits):
        body_start = line_idx
        body_end = splits[i+1][3] if i + 1 < len(splits) else len(sub_lines)
        b_lines = sub_lines[body_start:body_end]
        b_text = "\n".join(b_lines).strip()

        sections_json.append({
            "section_number": str(s_num),
            "section_title": s_title,
            "part": part,
            "full_text": b_text,
            "searchable_chunk": f"{title} - Section {s_num}: {s_title}\n{part}\n{b_text}"
        })

    manifest = {
        "statute_id": statute_id,
        "title": title,
        "short_title": short_title,
        "year": year,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": gazette_no,
        "enactment_date": enact_date,
        "description": desc,
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = f"data/json_laws/{out_file}"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


# 1. North-West Development Commission Act (27 Sections)
def extract_north_west():
    nw_defs = [
        (1, "Establishment of the North-West Development Commission", "Part I - Establishment of the Commission and the Governing Board", [r"^1\.\s*\(1\)\s*There is established the North-West"]),
        (2, "Establishment of the Governing Board", "Part I - Establishment of the Commission and the Governing Board", [r"^2\.\s*\(1\)\s*There is established for the Commission, a Governing Board"]),
        (3, "Tenure of office", "Part I - Establishment of the Commission and the Governing Board", [r"^3\.\s*Subject to the provisions of section 4"]),
        (4, "Rotation of office of Chairman", "Part I - Establishment of the Commission and the Governing Board", [r"^4\.\s*The office of the Chairman established"]),
        (5, "Resignation, cessation or removal from membership of the Board", "Part I - Establishment of the Commission and the Governing Board", [r"^5\.\s*.*ember.*Bad.*mentine", r"^5\.\s*"]),
        (6, "Remunerations and allowances", "Part I - Establishment of the Commission and the Governing Board", [r"^6\.\s*The.*remuneration", r"^6\.\s*"]),
        (7, "Functions and powers of the Commission", "Part II - Functions and Powers of the Commission", [r"^7\.\s*\(1\)\s*The Commission shall"]),
        (8, "Powers of the Board", "Part II - Functions and Powers of the Commission", [r"^8\.\s*The Board shall have power"]),
        (9, "Structure of the Commission", "Part III - Structure of the Commission", [r"^9\.\s*.*There shall be established in the headquarters"]),
        (10, "Management Committee", "Part III - Structure of the Commission", [r"^10\.\s*\(1\)\s*There shall be for the Commission a Management Committee"]),
        (11, "Advisory committee of the Commission", "Part III - Structure of the Commission", [r"^11\.\s*\(1\)\s*There is established for the Commission a North-West"]),
        (12, "The Managing Director", "Part IV - Staff of the Commission", [r"^(?:12|2)\.\s*\(1\)\s*There shall be for the Commission,\s*a Managing Director"]),
        (13, "Pension", "Part IV - Staff of the Commission", [r"^13\.\s*\(1\)\s*Service in the Commission shall be approved service"]),
        (14, "Fund of the Commission", "Part V - Financial Provisions", [r"^(?:14|1)\.\s*.*Fund from which"]),
        (15, "Application of the Fund", "Part V - Financial Provisions", [r"^15\.\s*\(1\)\s*The Commission shall apply the proceeds of the Fund"]),
        (16, "Annual estimates and expenditure", "Part V - Financial Provisions", [r"^16\.\s*\(1\)\s*The Board shall, not later than 30 September"]),
        (17, "Submission of report", "Part V - Financial Provisions", [r"^17\.\s*\(1\)\s*The Commission shall, at the end of every quarter"]),
        (18, "Monitoring Committee", "Part VI - Miscellaneous Provisions", [r"^(?:18|8)\.\s*\(1\)\s*There is established for the Commission a Monitoring Committee"]),
        (19, "Offices and premises of the Commission", "Part VI - Miscellaneous Provisions", [r"^(?:19|1)\.\s*.*purchase or take on lease", r"^(?:19|1)\.\s*l or to upon posite tie rein"]),
        (20, "Directives of the President", "Part VI - Miscellaneous Provisions", [r"^20\.\s*Subject to the provisions of this Act, the President may give"]),
        (21, "Public Officers Protection Act", "Part VI - Miscellaneous Provisions", [r"^21\.\s*\(1\)\s*Subject to the provisions of this Act, the provisions of the Public Officers"]),
        (22, "Services of notice, summons and other documents", "Part VI - Miscellaneous Provisions", [r"^22\.\s*A notice, summons or other document required"]),
        (23, "Payment of judgment debts", "Part VI - Miscellaneous Provisions", [r"^(?:23|3)\.\s*\(1\)\s*In any action or suit against the Commission, no execution"]),
        (24, "Indemnity of staff", "Part VI - Miscellaneous Provisions", [r"^24\.\s*A member of the Board, the Managing Director"]),
        (25, "Regulations", "Part VI - Miscellaneous Provisions", [r"^25\.\s*The Commission may, with the approval of the President"]),
        (26, "Interpretation", "Part VI - Miscellaneous Provisions", [r"^26\.\s*In this Act"]),
        (27, "Citation", "Part VI - Miscellaneous Provisions", [r"^27\.\s*This Act may be cited as the North-West Development Commission"])
    ]
    return extract_from_line_splits(
        "data/raw_pdfs/north_west_dev_comm_act_2025_ocr.json", 2, 13, nw_defs,
        "north_west_dev_comm_act_2025",
        "North-West Development Commission (Establishment) Act, 2024",
        "North-West Dev Comm Act",
        2024,
        "Federal Republic of Nigeria Official Gazette / Act No. 5 of 2024",
        "24th July 2024",
        "An Act to establish the North-West Development Commission charged with the responsibility for the reconstruction and rehabilitation of infrastructural damages and catalytic development of the North-West zone.",
        "north_west_dev_comm_act_2025.json"
    )


# 2. North-Central Development Commission Act (30 Sections)
def extract_north_central():
    nc_defs = [
        (1, "Establishment of the North Central Development Commission", "Part I - Establishment of the Commission and the Governing Board", [r"^1\.\s*\(1\)\s*There is established the North Central", r"There is established the North Central"]),
        (2, "Establishment of the Governing Board", "Part I - Establishment of the Commission and the Governing Board", [r"^2\.\s*\(1\)\s*There is established for the Commission", r"Governing Board \(in this Act"]),
        (3, "Tenure of office", "Part I - Establishment of the Commission and the Governing Board", [r"^3\.\s*Subject to the provisions of section 4", r"^3\.\s*"]),
        (4, "Rotation of office of Chairman", "Part I - Establishment of the Commission and the Governing Board", [r"^4\.\s*The office of the Chairman established", r"^4\.\s*"]),
        (5, "Resignation, cessation or removal from membership of the Board", "Part I - Establishment of the Commission and the Governing Board", [r"^5\.\s*\(1\)\s*A member of the Board", r"^5\.\s*"]),
        (6, "Allowances of members", "Part I - Establishment of the Commission and the Governing Board", [r"^6\.\s*The members of the Board shall be paid", r"^6\.\s*"]),
        (7, "Functions and powers of the Commission", "Part II - Functions and Powers of the Commission", [r"^7\.\s*\(1\)\s*The Commission shall", r"^7\.\s*"]),
        (8, "Powers of the Board", "Part II - Functions and Powers of the Commission", [r"^8\.\s*The Board shall have power to", r"^8\.\s*"]),
        (9, "Structure of the Commission", "Part III - Structure of the Commission", [r"^9\.\s*\(1\)\s*There shall be established in the headquarters", r"^9\.\s*"]),
        (10, "Management Committee", "Part III - Structure of the Commission", [r"^10\.\s*\(1\)\s*There shall be for the Commission a Management Committee", r"^10\.\s*"]),
        (11, "Establishment of the North Central Development Advisory Committee", "Part III - Structure of the Commission", [r"^11\.\s*\(1\)\s*There is established for the Commission a North Central", r"referred to as \"the Advisory Committee\"", r"^11\.\s*"]),
        (12, "The Managing Director", "Part IV - Staff of the Commission", [r"^12\.\s*\(1\)\s*There shall be for the Commission, a Managing Director", r"^12\.\s*"]),
        (13, "Staff of the Commission", "Part IV - Staff of the Commission", [r"^13\.\s*\(1\)\s*Service in the Commission shall be approved service", r"^13\.\s*\(1\)\s*The Board shall appoint for the Commission", r"^13\.\s*"]),
        (14, "Fund of the Commission", "Part V - Financial Provisions", [r"^(?:14|4)\.\s*\(1\)\s*The Commission shall establish and maintain a Fund", r"^14\.\s*"]),
        (15, "Expenditure of the Commission", "Part V - Financial Provisions", [r"^15\.\s*The Commission shall apply the Fund", r"^15\.\s*"]),
        (16, "Gift to the Commission", "Part V - Financial Provisions", [r"^16\.\s*\(1\)\s*The Commission may accept gifts of land", r"^16\.\s*"]),
        (17, "Power to borrow", "Part V - Financial Provisions", [r"^17\.\s*The Commission may, with the consent of the President", r"^17\.\s*"]),
        (18, "Annual estimates and expenditure", "Part V - Financial Provisions", [r"^18\.\s*\(1\)\s*The Board shall, not later than 30 September", r"^18\.\s*"]),
        (19, "Quarterly report", "Part V - Financial Provisions", [r"^19\.\s*The Commission shall, at the end of every quarter", r"^19\.\s*"]),
        (20, "Annual report", "Part V - Financial Provisions", [r"^20\.\s*\(1\)\s*The Board shall prepare and submit to the President", r"^20\.\s*"]),
        (21, "Monitoring Committee", "Part VI - Miscellaneous Provisions", [r"^21\.\s*\(1\)\s*There is established for the Commission a Monitoring Committee", r"^21\.\s*"]),
        (22, "Offices and premises of the Commission", "Part VI - Miscellaneous Provisions", [r"^22\.\s*For the purposes of providing offices and premises", r"^22\.\s*"]),
        (23, "Directives by the President", "Part VI - Miscellaneous Provisions", [r"^23\.\s*Subject to the provisions of this Act, the President may give", r"^23\.\s*"]),
        (24, "Public Officers Protection Act", "Part VI - Miscellaneous Provisions", [r"^24\.\s*\(1\)\s*Subject to the provisions of this Act, the provisions of the Public Officers", r"^24\.\s*"]),
        (25, "Service of notices, summons and other documents", "Part VI - Miscellaneous Provisions", [r"^25\.\s*A notice, summons or other documents required", r"^25\.\s*"]),
        (26, "Restriction on execution of judgment debts", "Part VI - Miscellaneous Provisions", [r"^26\.\s*\(1\)\s*In any action or suit against the Commission", r"^26\.\s*"]),
        (27, "Indemnity of officers", "Part VI - Miscellaneous Provisions", [r"^27\.\s*A member of the Board, the Managing Director", r"^27\.\s*"]),
        (28, "Regulations", "Part VI - Miscellaneous Provisions", [r"^28\.\s*The Commission may, with the approval of the President", r"^28\.\s*"]),
        (29, "Interpretation", "Part VI - Miscellaneous Provisions", [r"^29\.\s*In this Act", r"^29\.\s*"]),
        (30, "Citation", "Part VI - Miscellaneous Provisions", [r"^30\.\s*.*North Central Development Commission", r"^30\.\s*"])
    ]
    return extract_from_line_splits(
        "data/raw_pdfs/north_central_dev_comm_act_2024_ocr.json", 3, 15, nc_defs,
        "north_central_dev_comm_act_2024",
        "North-Central Development Commission (Establishment) Act, 2024",
        "North-Central Dev Comm Act",
        2024,
        "Federal Republic of Nigeria Official Gazette / Act No. 64 of 2024",
        "28th November 2024",
        "An Act to establish the North-Central Development Commission charged with the responsibility among other things to receive and manage funds for the reconstruction, rehabilitation, and development of the North-Central States.",
        "north_central_dev_comm_act_2024.json"
    )


# 3. South-East Development Commission Act (31 Sections)
def extract_south_east():
    se_defs = [
        (1, "Establishment of the South-East Development Commission", "Part I - Establishment of the Commission and the Governing Board", [r"^1\.\s*\(1\)\s*There is established the South-East"]),
        (2, "Establishment of the Governing Board", "Part I - Establishment of the Commission and the Governing Board", [r"^2\.\s*.*There is established for the Commission, a the Governing Board"]),
        (3, "Head office of the Commission", "Part I - Establishment of the Commission and the Governing Board", [r"^3\.\s*The Commission shall have its head office in Enugu"]),
        (4, "Tenure of office", "Part I - Establishment of the Commission and the Governing Board", [r"^4\.\s*Subject to the provisions of section 4 of this Act"]),
        (5, "Rotation of office of Chairman", "Part I - Establishment of the Commission and the Governing Board", [r"^5\.\s*The office of the Chairman shall rotate"]),
        (6, "Resignation, cessation or removal from membership of the Board", "Part I - Establishment of the Commission and the Governing Board", [r"^6\.\s*\(1\)\s*A member of the Board other than an ex-officio"]),
        (7, "Allowances of members", "Part I - Establishment of the Commission and the Governing Board", [r"^7\.\s*There shall be paid to every member of the Board"]),
        (8, "Functions and powers of the Commission", "Part II - Functions and Powers of the Commission", [r"^8\.\s*\(1\)\s*The Commission shall"]),
        (9, "Powers of the Board", "Part II - Functions and Powers of the Commission", [r"^9\.\s*The Board shall have power to"]),
        (10, "Structure of the Commission", "Part III - Structure of the Commission", [r"^10\.\s*\(1\)\s*There shall be established in the head office"]),
        (11, "Management Committee", "Part III - Structure of the Commission", [r"^11\.\s*There shall be for the Commission, a Management Committee"]),
        (12, "Establishment of the South-East Development Advisory Committee", "Part III - Structure of the Commission", [r"^12\.\s*\(1\)\s*There is established for the Commission, a South-East"]),
        (13, "The Managing Director", "Part IV - Staff of the Commission", [r"^13\.\s*\(1\)\s*There shall be for the Commission, a Managing Director"]),
        (14, "Pension", "Part IV - Staff of the Commission", [r"^(?:14|1)\.\s*\(1\)\s*Service in the Commission shall be approved service"]),
        (15, "Fund of the Commission", "Part V - Financial Provisions", [r"^15\.\s*\(1\)\s*The Commission shall establish and maintain a Fund"]),
        (16, "Expenditure of the Commission", "Part V - Financial Provisions", [r"^16\.\s*The Commission shall apply the proceeds of the Fund"]),
        (17, "Gift to the Commission", "Part V - Financial Provisions", [r"^17\.\s*\(1\)\s*The Commission may accept gifts of land"]),
        (18, "Power to borrow", "Part V - Financial Provisions", [r"^18\.\s*The Commission may, with the consent of the President"]),
        (19, "Annual estimates and expenditure", "Part V - Financial Provisions", [r"^19\.\s*\(1\)\s*The Board shall, not later than 30 September"]),
        (20, "Quarterly report", "Part V - Financial Provisions", [r"^20\.\s*The Commission shall, at the end of every quarter"]),
        (21, "Annual report", "Part V - Financial Provisions", [r"^21\.\s*\(1\)\s*The Board shall prepare and submit to the President"]),
        (22, "Monitoring Committee", "Part VI - Miscellaneous Provisions", [r"^22\.\s*\(1\)\s*There is established for the Commission"]),
        (23, "Offices and premises of the Commission", "Part VI - Miscellaneous Provisions", [r"^23\.\s*\(1\)\s*For the purposes of providing offices and premises"]),
        (24, "Directives by the President", "Part VI - Miscellaneous Provisions", [r"^24\.\s*Subject to the provisions of this Act, the President"]),
        (25, "Public Officers Protection Act", "Part VI - Miscellaneous Provisions", [r"^25\.\s*\(1\)\s*Subject to the provisions of this Act, the provisions of the Public"]),
        (26, "Service of notices, summons and other documents", "Part VI - Miscellaneous Provisions", [r"^26\.\s*A notice, summons or other documents required"]),
        (27, "Restriction on execution of judgment debts", "Part VI - Miscellaneous Provisions", [r"^27\.\s*\(1\)\s*In any action or suit against the Commission"]),
        (28, "Indemnity of officers", "Part VI - Miscellaneous Provisions", [r"^28\.\s*A member of the Board, the Managing Director"]),
        (29, "Regulations", "Part VI - Miscellaneous Provisions", [r"^29\.\s*The Commission may, with the approval of the President"]),
        (30, "Interpretation", "Part VI - Miscellaneous Provisions", [r"^30\.\s*In this Act"]),
        (31, "Citation", "Part VI - Miscellaneous Provisions", [r"^31\.\s*This Act may be cited as the South-East Development Commission"])
    ]
    return extract_from_line_splits(
        "data/raw_pdfs/south_east_dev_comm_act_2025_ocr.json", 3, 15, se_defs,
        "south_east_dev_comm_act_2025",
        "South-East Development Commission (Establishment) Act, 2024",
        "South-East Dev Comm Act",
        2024,
        "Federal Republic of Nigeria Official Gazette / Act No. 6 of 2024",
        "23rd July 2024",
        "An Act to establish the South-East Development Commission charged with the responsibility for the reconstruction, rehabilitation, and infrastructural development of the South-East zone.",
        "south_east_dev_comm_act_2025.json"
    )


# 4. South-South Development Commission Act (28 Sections)
def extract_south_south():
    ss_defs = [
        (1, "Establishment of the South-South Development Commission", "Part I - Establishment of the Commission and the Governing Board", [r"^1\.\s*\(1\)\s*There is established the South-South", r"There is established the South-South"]),
        (2, "Establishment of the Governing Board", "Part I - Establishment of the Commission and the Governing Board", [r"^2\.\s*\(1\)\s*There is established for the Commission, a Governing Board"]),
        (3, "Tenure of office", "Part I - Establishment of the Commission and the Governing Board", [r"^3\.\s*\(1\)\s*The Chairman, the Managing", r"^3\.\s*"]),
        (4, "Tenure of office of members", "Part I - Establishment of the Commission and the Governing Board", [r"^4\.\s*Subject to the provisions of section 3", r"^4\.\s*"]),
        (5, "Rotation of office of Chairman", "Part I - Establishment of the Commission and the Governing Board", [r"^5\.\s*The.*Chairman and the Managing", r"^5\.\s*"]),
        (6, "Resignation, cessation or removal from membership of the Board", "Part I - Establishment of the Commission and the Governing Board", [r"^6\.\s*\(1\)\s*A member of the Board other than", r"^6\.\s*"]),
        (7, "Remuneration and allowances", "Part I - Establishment of the Commission and the Governing Board", [r"^7\.\s*There shall be paid to every member", r"^7\.\s*"]),
        (8, "Functions and powers of the Commission", "Part II - Functions and Powers of the Commission", [r"^8\.\s*\(1\)\s*The Commission shall have powers", r"^8\.\s*"]),
        (9, "Powers of the Board", "Part II - Functions and Powers of the Commission", [r"^9\.\s*The Board shall have power to", r"^9\.\s*", r"PART III"]),
        (10, "Structure of the Commission", "Part III - Structure of the Commission", [r"^10\.\s*\(1\)\s*The head office of the Commission", r"^10\.\s*"]),
        (11, "Management Committee", "Part III - Structure of the Commission", [r"^11\.\s*There shall be for the Commission.*Management Committee", r"^11\.\s*"]),
        (12, "Advisory Committee of the Commission", "Part III - Structure of the Commission", [r"^12\.\s*\(L\)\s*There is established for the Commission.*South-South", r"^12\.\s*"]),
        (13, "The Managing Director", "Part IV - Staff of the Commission", [r"^13\.\s*\(1\)\s*There shall be for the Commission, a Managing Director", r"^13\.\s*"]),
        (14, "Pension", "Part IV - Staff of the Commission", [r"^14\.\s*\(1\)\s*Service in the Commission shall be as approved", r"^14\.\s*"]),
        (15, "Fund of the Commission", "Part V - Financial Provisions", [r"^15\.\s*\(1\)\s*The Commission shall establish and maintain a Fund", r"^15\.\s*"]),
        (16, "Application of the Fund", "Part V - Financial Provisions", [r"^16\.\s*The Commission shall apply the proceeds of the fund", r"^16\.\s*"]),
        (17, "Gift to the Commission", "Part V - Financial Provisions", [r"^17\.\s*\(1\)\s*The Commission may accept gifts of land", r"^17\.\s*"]),
        (18, "Power to borrow", "Part V - Financial Provisions", [r"^18\.\s*The Commission may, with the consent of the President", r"^18\.\s*"]),
        (19, "Annual estimates and expenditure", "Part V - Financial Provisions", [r"^19\.\s*\(1\)\s*The Board shall, not later than 30 September", r"^19\.\s*"]),
        (20, "Quarterly report", "Part V - Financial Provisions", [r"^20\.\s*The Commission shall, at the end of every quarter", r"^20\.\s*"]),
        (21, "Annual report", "Part V - Financial Provisions", [r"^21\.\s*\(1\)\s*The Board shall prepare and submit to the President", r"^21\.\s*"]),
        (22, "Offices and premises of the Commission", "Part VI - Miscellaneous Provisions", [r"^22\.\s*\(1\)\s*For the purposes of providing offices and premises", r"^22\.\s*"]),
        (23, "Public Officers Protection Act", "Part VI - Miscellaneous Provisions", [r"^23\.\s*Subjoct to the provision of this Act", r"^23\.\s*"]),
        (24, "Service of notice, summons and other documents", "Part VI - Miscellaneous Provisions", [r"^24\.\s*A notice, summons or other documents required", r"^24\.\s*"]),
        (25, "Payment of judgment debts", "Part VI - Miscellaneous Provisions", [r"^25\.\s*Any sum of money which is the judgment", r"^25\.\s*"]),
        (26, "Indemnity of staff", "Part VI - Miscellaneous Provisions", [r"^26\.\s*A member of the Board, the Managing Director", r"^26\.\s*"]),
        (27, "Interpretation and Regulations", "Part VI - Miscellaneous Provisions", [r"^27\.\s*In this Act", r"Board.*means the Governing Board established", r"^27\.\s*"]),
        (28, "Citation", "Part VI - Miscellaneous Provisions", [r"^28\.\s*This Act may be cited as the South-South Development Commission", r"^28\.\s*"])
    ]
    return extract_from_line_splits(
        "data/raw_pdfs/south_south_dev_comm_act_2025_ocr.json", 3, 14, ss_defs,
        "south_south_dev_comm_act_2025",
        "South-South Development Commission (Establishment) Act, 2025",
        "South-South Dev Comm Act",
        2025,
        "Federal Republic of Nigeria Official Gazette / Act No. 7 of 2025",
        "15th January 2025",
        "An Act to establish the South-South Development Commission charged with the responsibility to receive and manage funds for the development of infrastructure and economic empowerment in the South-South zone.",
        "south_south_dev_comm_act_2025.json"
    )


# 5. South-West Development Commission Act (27 Sections)
def extract_south_west():
    sw_defs = [
        (1, "Establishment of the South-West Development Commission", "Part I - Establishment of the Commission and the Governing Board", [r"^1\.\s*\(1\)\s*There is established the South-West"]),
        (2, "Establishment of the Governing Board", "Part I - Establishment of the Commission and the Governing Board", [r"^2\.\s*\(1\)\s*There is established for the Commission a Governing Board"]),
        (3, "Tenure of office", "Part I - Establishment of the Commission and the Governing Board", [r"^3\.\s*Subject to the provisions of section 4"]),
        (4, "Rotation of office of Chairman", "Part I - Establishment of the Commission and the Governing Board", [r"^4\.\s*The office of the Chairman established"]),
        (5, "Resignation, cessation or removal from membership of the Board", "Part I - Establishment of the Commission and the Governing Board", [r"^5\.\s*\(1\)\s*A member of the Board other than"]),
        (6, "Remunerations and allowances", "Part I - Establishment of the Commission and the Governing Board", [r"^6\.\s*There shall be paid to every member of the Board"]),
        (7, "Functions of the Commission", "Part II - Functions and Powers of the Commission", [r"^7\.\s*\(1\)\s*The Commission shall"]),
        (8, "Powers of the Board", "Part II - Functions and Powers of the Commission", [r"^8\.\s*The Board shall have power to"]),
        (9, "Structure of the Commission", "Part III - Structure of the Commission", [r"^9\.\s*\(I\)\s*There shall be established in the head office"]),
        (10, "Management Committee", "Part III - Structure of the Commission", [r"^10\.\s*\(1\)\s*There shall be for the Commission, a Management Committee"]),
        (11, "Advisory Committee of the Commission", "Part III - Structure of the Commission", [r"^11\.\s*\(1\)\s*There is established for the Commission, a South-West"]),
        (12, "The Managing Director", "Part IV - Staff of the Commission", [r"^12\.\s*There shall be for the Commission, a Managing Director"]),
        (13, "Pension", "Part IV - Staff of the Commission", [r"^13\.\s*\(1\)\s*Service in the Commission shall be approved service"]),
        (14, "Fund of the Commission", "Part V - Financial Provisions", [r"^14\.\s*\(1\)\s*The Commission shall establish and maintain a Fund"]),
        (15, "Application of the Fund", "Part V - Financial Provisions", [r"^15\.\s*\(1\)\s*.*Commission shall apply the proceeds of the Fund"]),
        (16, "Annual estimates and expenditure", "Part V - Financial Provisions", [r"^16\.\s*\(I\)\s*The Board shall, not later than 30 September"]),
        (17, "Submission of report", "Part V - Financial Provisions", [r"^17\.\s*\(1\)\s*The Commission shall, at the end of every quarter"]),
        (18, "Monitoring Committee", "Part VI - Miscellaneous Provisions", [r"^18\.\s*\(1\)\s*There is established for the Commission a Monitoring Committee"]),
        (19, "Offices and premises of the Commission", "Part VI - Miscellaneous Provisions", [r"^19\.\s*\(1\)\s*For the purposes of providing offices and premises"]),
        (20, "Directives of the President", "Part VI - Miscellaneous Provisions", [r"^20\.\s*Subject to the provisions of this Act, the President may give"]),
        (21, "Limitation of Suits against the Commission", "Part VI - Miscellaneous Provisions", [r"^(?:41|21)\.\s*\(1\)\s*A suit against the Commission"]),
        (22, "Service of notice, summons and other documents", "Part VI - Miscellaneous Provisions", [r"^22\.\s*A notice, summons or other documents required"]),
        (23, "Payment of judgment debts", "Part VI - Miscellaneous Provisions", [r"^23\.\s*\(1\)\s*In any action or suit against the Commission"]),
        (24, "Indemnity of staff", "Part VI - Miscellaneous Provisions", [r"^24\.\s*A member of the Board, the Managing Director"]),
        (25, "Regulations", "Part VI - Miscellaneous Provisions", [r"^25\.\s*The Commission may, with the approval of the President"]),
        (26, "Interpretation", "Part VI - Miscellaneous Provisions", [r"^26\.\s*In this Act"]),
        (27, "Citation", "Part VI - Miscellaneous Provisions", [r"^27\.\s*This Act may be cited as the South-West Development Commission", r"^27\.\s*This Act may"])
    ]
    return extract_from_line_splits(
        "data/raw_pdfs/south_west_dev_comm_act_2025_ocr.json", 3, 14, sw_defs,
        "south_west_dev_comm_act_2025",
        "South-West Development Commission (Establishment) Act, 2025",
        "South-West Dev Comm Act",
        2025,
        "Federal Republic of Nigeria Official Gazette / Act No. 8 of 2025",
        "15th January 2025",
        "An Act to establish the South-West Development Commission charged with the responsibility to receive and manage funds allocated from the Federation Account for the infrastructure and ecological development of the South-West zone.",
        "south_west_dev_comm_act_2025.json"
    )


if __name__ == "__main__":
    t1 = extract_north_west()
    t2 = extract_north_central()
    t3 = extract_south_east()
    t4 = extract_south_south()
    t5 = extract_south_west()

    total = t1 + t2 + t3 + t4 + t5
    print(f"\n=======================================================")
    print(f"ALL 5 DEVELOPMENT COMMISSION ACTS EXTRACTED: Total sections: {total}")
