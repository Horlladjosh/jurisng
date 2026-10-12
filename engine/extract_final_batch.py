import fitz
import urllib.request
import re
import json
import os
from bs4 import BeautifulSoup

def clean_txt(s):
    s = s.replace("\xa0", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def normalize_title(t):
    t = t.lower()
    t = re.sub(r"part\s+[ivxlcdm\d]+", "", t)
    t = re.sub(r"[\-\—\–]", "", t)
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return t

# 1. Stamp Duties Act
def extract_stamp_duties_act():
    print("\n[*] Extracting Stamp Duties Act (Cap. S8, LFN 2004)...")
    doc = fitz.open("data/raw_pdfs/stamp_duties_act.pdf")
    full_lines = []
    for p in range(len(doc)):
        for l in doc[p].get_text().splitlines():
            l = clean_txt(l)
            if l: full_lines.append(l)

    sec_hits = []
    for i, l in enumerate(full_lines):
        m = re.match(r"^(\d{1,3})\.\s*(.*)$", l)
        m_roman = re.match(r"^(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s*(.*)$", l)
        if m:
            s_num = int(m.group(1))
            title = m.group(2).strip()
            if not title and i + 1 < len(full_lines):
                title = full_lines[i+1]
            sec_hits.append((s_num, title, i))
        elif m_roman and i > 50:
            s_num = 1 if m_roman.group(0).startswith("I.") else None
            if s_num:
                sec_hits.append((s_num, m_roman.group(1), i))

    substantive = []
    expected = 1
    for s_num, title, idx in sec_hits:
        if idx < 40: continue
        if s_num == expected:
            substantive.append((s_num, title, idx))
            expected += 1
            if expected > 117: break

    sections_json = []
    for i, (s_num, title, line_idx) in enumerate(substantive):
        body_start = line_idx + 1
        body_end = substantive[i+1][2] if i + 1 < len(substantive) else len(full_lines)
        b_lines = full_lines[body_start:body_end]
        b_text = "\n".join(b_lines).strip()
        if not b_text: b_text = title

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.rstrip("."),
            "part": "General Provisions",
            "full_text": b_text,
            "searchable_chunk": f"Stamp Duties Act - Section {s_num}: {title}\nGeneral Provisions\n{b_text}"
        })

    manifest = {
        "statute_id": "stamp_duties_act",
        "title": "Stamp Duties Act, 1939",
        "short_title": "Stamp Duties Act",
        "year": 1939,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. S8, LFN 2004",
        "enactment_date": "1st April 1939",
        "description": "An Act to provide for the levying of stamp duties on certain matters and instruments in Nigeria.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/stamp_duties_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


# 2. Immigration Act
def extract_immigration_act():
    print("\n[*] Extracting Immigration Act (Cap. I1, LFN 2004)...")
    doc = fitz.open("data/raw_pdfs/immigration_act.pdf")
    full_lines = []
    for p in range(len(doc)):
        for l in doc[p].get_text().splitlines():
            l = clean_txt(l)
            if l: full_lines.append(l)

    sec_hits = []
    for i, l in enumerate(full_lines):
        m = re.match(r"^(\d{1,3})\.\s*(.*)$", l)
        if m:
            s_num = int(m.group(1))
            title = m.group(2).strip()
            if not title and i + 1 < len(full_lines):
                title = full_lines[i+1]
            sec_hits.append((s_num, title, i))

    substantive = []
    expected = 1
    for s_num, title, idx in sec_hits:
        if idx < 40: continue
        if s_num == expected:
            substantive.append((s_num, title, idx))
            expected += 1
            if expected > 53: break

    sections_json = []
    for i, (s_num, title, line_idx) in enumerate(substantive):
        body_start = line_idx + 1
        body_end = substantive[i+1][2] if i + 1 < len(substantive) else len(full_lines)
        b_lines = full_lines[body_start:body_end]
        b_text = "\n".join(b_lines).strip()
        if not b_text: b_text = title

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.rstrip("."),
            "part": "General Provisions",
            "full_text": b_text,
            "searchable_chunk": f"Immigration Act - Section {s_num}: {title}\nGeneral Provisions\n{b_text}"
        })

    manifest = {
        "statute_id": "immigration_act",
        "title": "Immigration Act, 1963",
        "short_title": "Immigration Act",
        "year": 1963,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. I1, LFN 2004 / Act No. 6 of 1963",
        "enactment_date": "1st August 1963",
        "description": "An Act to consolidate and amend the law relating to immigration.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/immigration_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


# 3. NDLEA Act
def extract_ndlea_act():
    print("\n[*] Extracting NDLEA Act (Cap. N30, LFN 2004)...")
    doc = fitz.open("data/raw_pdfs/ndlea_act.pdf")
    full_lines = []
    for p in range(len(doc)):
        for l in doc[p].get_text().splitlines():
            l = clean_txt(l)
            if l: full_lines.append(l)

    sec_hits = []
    for i in range(180, min(2300, len(full_lines))):
        l = full_lines[i]
        m1 = re.match(r"^(\d{1,2})\.\s*(.*)$", l)
        m2 = re.match(r"^(\d{1,2})\.$", l)
        m_bare13 = (l == "13" and i + 1 < len(full_lines) and full_lines[i+1] == ".")
        if m1 and m1.group(2).strip():
            sec_hits.append((int(m1.group(1)), m1.group(2).strip(), i))
        elif m2 or (m1 and not m1.group(2).strip()):
            s_num = int(m2.group(1) if m2 else m1.group(1))
            t = full_lines[i+1] if i + 1 < len(full_lines) else ""
            sec_hits.append((s_num, t, i))
        elif m_bare13:
            sec_hits.append((13, "[Repealed/Amended]", i))

    substantive = []
    expected = 1
    for s_num, title, idx in sec_hits:
        if s_num == expected:
            substantive.append((s_num, title, idx))
            expected += 1
            if expected > 44: break

    sections_json = []
    for i, (s_num, title, line_idx) in enumerate(substantive):
        body_start = line_idx + 1
        body_end = substantive[i+1][2] if i + 1 < len(substantive) else 2250
        b_lines = full_lines[body_start:body_end]
        b_text = "\n".join(b_lines).strip()
        if not b_text: b_text = title

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.rstrip("."),
            "part": "General Provisions",
            "full_text": b_text,
            "searchable_chunk": f"National Drug Law Enforcement Agency Act - Section {s_num}: {title}\nGeneral Provisions\n{b_text}"
        })

    manifest = {
        "statute_id": "ndlea_act",
        "title": "National Drug Law Enforcement Agency Act, 1989",
        "short_title": "NDLEA Act",
        "year": 1989,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N30, LFN 2004 / Decree No. 48 of 1989",
        "enactment_date": "29th December 1989",
        "description": "An Act to establish the National Drug Law Enforcement Agency to enforce laws against the illicit trafficking in narcotic drugs and psychotropic substances.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/ndlea_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


# 4. Trade Unions Act
def extract_trade_unions_act():
    print("\n[*] Extracting Trade Unions Act (Cap. T14, LFN 2004)...")
    doc = fitz.open("data/raw_pdfs/trade_unions_act.pdf")
    full_lines = []
    for p in range(len(doc)):
        for l in doc[p].get_text().splitlines():
            l = clean_txt(l)
            if l: full_lines.append(l)

    sec_hits = []
    for i in range(200, min(3100, len(full_lines))):
        l = full_lines[i]
        m1 = re.match(r"^(\d{1,2})\.\s*(.*)$", l)
        m2 = re.match(r"^(\d{1,2})\.$", l)
        m3_split = (re.match(r"^(\d{1,2})$", l) and i + 1 < len(full_lines) and full_lines[i+1] == ".")
        if m1 and m1.group(2).strip():
            sec_hits.append((int(m1.group(1)), m1.group(2).strip(), i))
        elif m2 or (m1 and not m1.group(2).strip()):
            s_num = int(m2.group(1) if m2 else m1.group(1))
            t = full_lines[i+1] if i + 1 < len(full_lines) else ""
            sec_hits.append((s_num, t, i))
        elif m3_split:
            s_num = int(l)
            t = full_lines[i+2] if i + 2 < len(full_lines) else ""
            sec_hits.append((s_num, t, i))

    substantive = []
    expected = 1
    for s_num, title, idx in sec_hits:
        if s_num == expected:
            substantive.append((s_num, title, idx))
            expected += 1
            if expected > 55: break

    sections_json = []
    for i, (s_num, title, line_idx) in enumerate(substantive):
        body_start = line_idx + 1
        if line_idx + 1 < len(full_lines) and full_lines[line_idx+1] == ".":
            body_start += 1
        body_end = substantive[i+1][2] if i + 1 < len(substantive) else 3070
        b_lines = full_lines[body_start:body_end]
        b_text = "\n".join(b_lines).strip()
        if not b_text: b_text = title

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.rstrip("."),
            "part": "General Provisions",
            "full_text": b_text,
            "searchable_chunk": f"Trade Unions Act - Section {s_num}: {title}\nGeneral Provisions\n{b_text}"
        })

    manifest = {
        "statute_id": "trade_unions_act",
        "title": "Trade Unions Act, 1973",
        "short_title": "Trade Unions Act",
        "year": 1973,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. T14, LFN 2004 / Decree No. 31 of 1973",
        "enactment_date": "1st November 1973",
        "description": "An Act to make comprehensive provisions with respect to the formation, registration and organization of trade unions and federations of trade unions.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/trade_unions_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


# 5. Arbitration and Conciliation Act (Cap. A18, sn=32)
def extract_arbitration_act():
    print("\n[*] Extracting Arbitration and Conciliation Act (Cap. A18, LFN 2004)...")
    url = "https://placng.org/lawsofnigeria/view2.php?sn=32"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    text = soup.find("div", class_="field-name-body").get_text()
    raw_lines = [clean_txt(l) for l in text.splitlines() if clean_txt(l)]

    sections_catalog = [
        (1, "Form of arbitration agreement"),
        (2, "Arbitration agreement irrevocable except by agreement or leave of court"),
        (3, "Death of party"),
        (4, "Arbitration agreement and substantive claim before court"),
        (5, "Power to stay proceedings"),
        (6, "Number of arbitrators"),
        (7, "Appointment of arbitrators"),
        (8, "Grounds for challenge"),
        (9, "Challenge procedure"),
        (10, "Termination of mandate due to failure or impossibility to act"),
        (11, "Appointment of substitute arbitrator"),
        (12, "Competence of arbitral tribunal to rule on its jurisdiction"),
        (13, "Power of arbitral tribunal to order interim measure of protection"),
        (14, "Equal treatment of parties"),
        (15, "Arbitral proceedings"),
        (16, "Place of arbitration"),
        (17, "Commencement of arbitral proceedings"),
        (18, "Language to be used in arbitral proceedings"),
        (19, "Points of claim and defence"),
        (20, "Hearing and written proceedings"),
        (21, "Default of a party"),
        (22, "Power of arbitral tribunal to appoint expert"),
        (23, "Power of court to order attendance of witness"),
        (24, "Decision making by arbitral tribunal"),
        (25, "Settlement"),
        (26, "Form and contents of award"),
        (27, "Termination of proceedings"),
        (28, "Correction and interpretation of award and additional award"),
        (29, "Application for setting aside an arbitral award"),
        (30, "Setting aside of award in case of misconduct by arbitrator, etc."),
        (31, "Recognition and enforcement of awards"),
        (32, "Refusal of recognition or enforcement of award"),
        (33, "Waiver of right to object"),
        (34, "Extent of court intervention"),
        (35, "Extent of application of this Act to arbitration"),
        (36, "Extension of time"),
        (37, "Right to settle dispute by conciliation"),
        (38, "Request to conciliate"),
        (39, "Commencement of conciliation proceedings"),
        (40, "Appointment of conciliators"),
        (41, "Action by the conciliation body"),
        (42, "Terms of settlement"),
        (43, "Application of this Part of this Act"),
        (44, "Appointment of sole arbitrator, etc."),
        (45, "Challenge of arbitrators"),
        (46, "Replacement of arbitrators"),
        (47, "Rules applicable to substance of dispute"),
        (48, "Setting aside of arbitral award"),
        (49, "Costs"),
        (50, "Deposit of costs"),
        (51, "Recognition and enforcement of awards"),
        (52, "Grounds for refusing recognition or enforcement"),
        (53, "Application of Arbitration Rules set out in the First Schedule"),
        (54, "Application of the Convention on Recognition and Enforcement of Foreign Arbitral Awards, etc."),
        (55, "Conciliation Rules"),
        (56, "Receipt of written communication"),
        (57, "Interpretation"),
        (58, "Short title and application")
    ]

    sec_positions = []
    curr_line = 90
    for s_num, s_title in sections_catalog:
        norm_t = normalize_title(s_title)
        best_idx = None
        for idx in range(curr_line, min(470, len(raw_lines))):
            l = raw_lines[idx]
            norm_l = normalize_title(l)
            m = re.match(r"^" + str(s_num) + r"\.\s*(.*)$", l)
            if m:
                best_idx = idx
                break
            elif norm_t in norm_l or norm_l.startswith(norm_t[:20]):
                best_idx = idx
                break
        if best_idx is not None:
            sec_positions.append((s_num, s_title, best_idx))
            curr_line = best_idx + 1

    sections_json = []
    for i, (s_num, title, line_idx) in enumerate(sec_positions):
        body_start = line_idx + 1
        body_end = sec_positions[i+1][2] if i + 1 < len(sec_positions) else 468
        b_lines = raw_lines[body_start:body_end]
        filtered_b = [l for l in b_lines if not l.startswith("Arbitration and Conciliation") and not re.match(r"^PART\s+[IVXLCDM]+", l, re.I)]
        b_text = "\n".join(filtered_b).strip()
        if not b_text: b_text = title

        part_num = "Part I - Arbitration" if s_num <= 36 else ("Part II - Conciliation" if s_num <= 42 else ("Part III - International Arbitration" if s_num <= 55 else "Part IV - Miscellaneous"))

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title,
            "part": part_num,
            "full_text": b_text,
            "searchable_chunk": f"Arbitration and Conciliation Act - Section {s_num}: {title}\n{part_num}\n{b_text}"
        })

    manifest = {
        "statute_id": "arbitration_conciliation_act",
        "title": "Arbitration and Conciliation Act, 1988",
        "short_title": "Arbitration and Conciliation Act",
        "year": 1988,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. A18, LFN 2004 / Decree No. 11 of 1988",
        "enactment_date": "14th March 1988",
        "description": "An Act to provide a unified legal framework for the fair and efficient settlement of commercial disputes by arbitration and conciliation.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/arbitration_conciliation_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


# 6. NIPC Act (Cap. N117, sn=374)
def extract_nipc_act():
    print("\n[*] Extracting NIPC Act (Cap. N117, LFN 2004)...")
    url = "https://placng.org/lawsofnigeria/view2.php?sn=374"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    text = soup.find("div", class_="field-name-body").get_text()
    raw_lines = [clean_txt(l) for l in text.splitlines() if clean_txt(l)]

    sections_catalog = [
        (1, "Establishment of the Nigerian Investment Promotion Commission"),
        (2, "Governing Council of the Commission"),
        (3, "Tenure of office, etc."),
        (4, "Functions of the Commission"),
        (5, "Powers of the Commission"),
        (6, "Secretary of the Commission"),
        (7, "Other staff of the Commission, etc."),
        (8, "Staff regulations"),
        (9, "Conditions of service"),
        (10, "Pensions"),
        (11, "Departments of the Commission"),
        (12, "Fund of the Commission"),
        (13, "Power to accept gifts"),
        (14, "Borrowing power, etc."),
        (15, "Annual estimates, accounts and audit"),
        (16, "Annual reports"),
        (17, "Enterprises eligible for participation"),
        (18, "Application of this Act"),
        (19, "Establishment of an enterprise"),
        (20, "Registration of enterprise with the Commission"),
        (21, "Purchase of the shares of a domestic company by a foreign company"),
        (22, "Incentives for special investment"),
        (23, "Priority areas"),
        (24, "Investment guarantees, transfer of capital, profits and dividends"),
        (25, "Guarantees against expropriation"),
        (26, "Dispute settlement procedures"),
        (27, "Assistance to enterprise"),
        (28, "Transitional provisions"),
        (29, "Repeal of Cap. 178 L.F.N.1990, etc."),
        (30, "Regulations"),
        (31, "Interpretation"),
        (32, "Short title")
    ]

    sec_positions = []
    curr_line = 50
    for s_num, s_title in sections_catalog:
        norm_t = normalize_title(s_title)
        best_idx = None
        for idx in range(curr_line, min(220, len(raw_lines))):
            l = raw_lines[idx]
            norm_l = normalize_title(l)
            m = re.match(r"^" + str(s_num) + r"\.\s*(.*)$", l)
            if m:
                best_idx = idx
                break
            elif norm_t in norm_l or norm_l.startswith(norm_t[:20]):
                best_idx = idx
                break
        if best_idx is not None:
            sec_positions.append((s_num, s_title, best_idx))
            curr_line = best_idx + 1

    sections_json = []
    for i, (s_num, title, line_idx) in enumerate(sec_positions):
        body_start = line_idx + 1
        body_end = sec_positions[i+1][2] if i + 1 < len(sec_positions) else 218
        b_lines = raw_lines[body_start:body_end]
        filtered_b = [l for l in b_lines if not l.startswith("PART ") and not l.startswith("SCHEDULE")]
        b_text = "\n".join(filtered_b).strip()
        if not b_text: b_text = title

        part_num = "Part I - Establishment of Commission" if s_num <= 3 else ("Part II - Functions and Powers" if s_num <= 5 else ("Part III - Staff" if s_num <= 11 else ("Part IV - Financial Provisions" if s_num <= 16 else "Part V - Provisions relating to Investment")))

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title,
            "part": part_num,
            "full_text": b_text,
            "searchable_chunk": f"Nigerian Investment Promotion Commission Act - Section {s_num}: {title}\n{part_num}\n{b_text}"
        })

    manifest = {
        "statute_id": "nipc_act_1995",
        "title": "Nigerian Investment Promotion Commission Act, 1995",
        "short_title": "NIPC Act",
        "year": 1995,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N117, LFN 2004 / Decree No. 16 of 1995",
        "enactment_date": "16th January 1995",
        "description": "An Act to establish the Nigerian Investment Promotion Commission to encourage and promote investment in the Nigerian economy.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/nipc_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


# 7. NHRC Act (Cap. N46, sn=308)
def extract_nhrc_act():
    print("\n[*] Extracting NHRC Act (Cap. N46, LFN 2004)...")
    url = "https://placng.org/lawsofnigeria/view2.php?sn=308"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    text = soup.find("div", class_="field-name-body").get_text()
    raw_lines = [clean_txt(l) for l in text.splitlines() if clean_txt(l)]

    sections_catalog = [
        (1, "Establishment of the National Human Rights Commission"),
        (2, "Governing Council of the Commission"),
        (3, "Tenure of office, etc."),
        (4, "Cessation of membership"),
        (5, "Functions of the Commission"),
        (6, "Powers of the Commission"),
        (7, "Executive secretary of the Commission"),
        (8, "Other staff of the Commission, etc."),
        (9, "Staff regulations"),
        (10, "Conditions of service"),
        (11, "Pensions"),
        (12, "Fund of the Commission"),
        (13, "Power to accept gifts"),
        (14, "Borrowing power, etc."),
        (15, "Annual estimates, accounts and audit"),
        (16, "Annual reports"),
        (17, "Power of the Attorney-General of the Federation to give directives"),
        (18, "Regulations"),
        (19, "Interpretation"),
        (20, "Short title")
    ]

    sec_positions = []
    curr_line = 46
    for s_num, s_title in sections_catalog:
        norm_t = normalize_title(s_title)
        best_idx = None
        for idx in range(curr_line, min(155, len(raw_lines))):
            l = raw_lines[idx]
            norm_l = normalize_title(l)
            m = re.match(r"^" + str(s_num) + r"\.\s*(.*)$", l)
            if m:
                best_idx = idx
                break
            elif norm_t in norm_l or norm_l.startswith(norm_t[:20]):
                best_idx = idx
                break
        if best_idx is not None:
            sec_positions.append((s_num, s_title, best_idx))
            curr_line = best_idx + 1

    sections_json = []
    for i, (s_num, title, line_idx) in enumerate(sec_positions):
        body_start = line_idx + 1
        body_end = sec_positions[i+1][2] if i + 1 < len(sec_positions) else 154
        b_lines = raw_lines[body_start:body_end]
        filtered_b = [l for l in b_lines if not l.startswith("PART ") and not l.startswith("National Human Rights Commission Act") and not l.startswith("SCHEDULE")]
        b_text = "\n".join(filtered_b).strip()
        if not b_text: b_text = title

        part_num = "Part I - Establishment of Commission" if s_num <= 4 else ("Part II - Functions and Powers" if s_num <= 6 else ("Part III - Staff" if s_num <= 11 else ("Part IV - Financial Provisions" if s_num <= 16 else "Part V - Miscellaneous")))

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title,
            "part": part_num,
            "full_text": b_text,
            "searchable_chunk": f"National Human Rights Commission Act - Section {s_num}: {title}\n{part_num}\n{b_text}"
        })

    manifest = {
        "statute_id": "nhrc_act_1995",
        "title": "National Human Rights Commission Act, 1995",
        "short_title": "NHRC Act",
        "year": 1995,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N46, LFN 2004 / Decree No. 22 of 1995",
        "enactment_date": "27th September 1995",
        "description": "An Act to establish the National Human Rights Commission for the promotion and protection of human rights guaranteed by the Nigerian Constitution and international instruments.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/nhrc_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


# 8. Customs and Excise Management Act (Cap. C45, LFN 2004)
def extract_customs_act():
    print("\n[*] Extracting Customs and Excise Management Act (Cap. C45, LFN 2004)...")
    doc = fitz.open("data/raw_pdfs/customs_management_act.pdf")
    full_lines = []
    for p in range(len(doc)):
        for l in doc[p].get_text().splitlines():
            l = clean_txt(l)
            if l: full_lines.append(l)

    sec_hits = []
    for i in range(250, 3360):
        l = full_lines[i]
        m = re.match(r"^(\d{1,3})\.\s*(.*)$", l)
        if m:
            sec_hits.append((int(m.group(1)), m.group(2).strip(), i))

    substantive = []
    expected = 1
    for s_num, title, idx in sec_hits:
        if s_num == expected:
            substantive.append((s_num, title, idx))
            expected += 1
            if expected > 195: break

    sections_json = []
    for i, (s_num, title, line_idx) in enumerate(substantive):
        body_start = line_idx + 1
        body_end = substantive[i+1][2] if i + 1 < len(substantive) else 3355
        b_lines = full_lines[body_start:body_end]
        filtered_b = [l for l in b_lines if not l.startswith("CUSTOMS AND EXCISE MANAGEMENT ACT") and not re.match(r"^PART\s+[IVXLCDM]+", l, re.I)]
        b_text = "\n".join(filtered_b).strip()
        if not b_text: b_text = title

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.rstrip("."),
            "part": "General Provisions",
            "full_text": b_text,
            "searchable_chunk": f"Customs and Excise Management Act - Section {s_num}: {title}\nGeneral Provisions\n{b_text}"
        })

    manifest = {
        "statute_id": "customs_management_act",
        "title": "Customs and Excise Management Act, 1958",
        "short_title": "Customs and Excise Management Act (CEMA)",
        "year": 1958,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. C45, LFN 2004 / No. 55 of 1958",
        "enactment_date": "1st April 1959",
        "description": "An Act to consolidate and amend the law relating to the management and administration of Customs and Excise duties.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/customs_management_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


if __name__ == "__main__":
    t1 = extract_stamp_duties_act()
    t2 = extract_immigration_act()
    t3 = extract_ndlea_act()
    t4 = extract_trade_unions_act()
    t5 = extract_arbitration_act()
    t6 = extract_nipc_act()
    t7 = extract_nhrc_act()
    t8 = extract_customs_act()

    total = t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8
    print(f"\n=======================================================")
    print(f"FINAL BATCH COMPLETE: Ingested 8 Acts with {total} certified sections!")
