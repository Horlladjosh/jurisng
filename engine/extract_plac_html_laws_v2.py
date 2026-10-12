import urllib.request
import re
import json
import os
from bs4 import BeautifulSoup

PLAC_HTML_ACTS = [
    {
        "sn": 87,
        "statute_id": "icpc_act_2000",
        "title": "Corrupt Practices and Other Related Offences Act, 2000",
        "short_title": "ICPC Act",
        "year": 2000,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. C31, LFN 2004 / Act No. 5 of 2000",
        "enactment_date": "13th June 2000",
        "description": "An Act to prohibit and prescribe punishment for corrupt practices and other related offences and to establish the Independent Corrupt Practices and Other Related Offences Commission.",
        "out_file": "icpc_act_2000.json",
        "expected_sections": 56
    },
    {
        "sn": 60,
        "statute_id": "cbn_act_2007",
        "title": "Central Bank of Nigeria (Establishment) Act, 2007",
        "short_title": "CBN Act",
        "year": 2007,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 7 of 2007",
        "enactment_date": "25th May 2007",
        "description": "An Act to repeal the Central Bank of Nigeria Act 1991 and enact the Central Bank of Nigeria Act 2007 to provide for the establishment, administration, operations and management of the Central Bank of Nigeria.",
        "out_file": "cbn_act_2007.json",
        "expected_sections": 61
    },
    {
        "sn": 18,
        "statute_id": "advance_fee_fraud_act_2006",
        "title": "Advance Fee Fraud and Other Fraud Related Offences Act, 2006",
        "short_title": "Advance Fee Fraud Act",
        "year": 2006,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 14 of 2006",
        "enactment_date": "5th June 2006",
        "description": "An Act to prohibit and punish certain offences pertaining to advance fee fraud and other fraud related offences and to repeal other Acts related therewith.",
        "out_file": "advance_fee_fraud_act_2006.json",
        "expected_sections": 22
    },
    {
        "sn": 122,
        "statute_id": "dishonoured_cheques_act_1977",
        "title": "Dishonoured Cheques (Offences) Act, 1977",
        "short_title": "Dishonoured Cheques Act",
        "year": 1977,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. D11, LFN 2004 / Act No. 44 of 1977",
        "enactment_date": "20th May 1977",
        "description": "An Act to make it an offence for any person to obtain credit by means of a cheque that is subsequently dishonoured, and for matters connected therewith.",
        "out_file": "dishonoured_cheques_act.json",
        "expected_sections": 4
    },
    {
        "sn": 14,
        "statute_id": "acts_authentication_act_1961",
        "title": "Acts Authentication Act, 1961",
        "short_title": "Acts Authentication Act",
        "year": 1961,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. A2, LFN 2004 / Act No. 50 of 1961",
        "enactment_date": "1st January 1962",
        "description": "An Act to make provision for the authentication and recording of Acts of the National Assembly.",
        "out_file": "acts_authentication_act.json",
        "expected_sections": 6
    },
    {
        "sn": 467,
        "statute_id": "public_holidays_act_1979",
        "title": "Public Holidays Act, 1979",
        "short_title": "Public Holidays Act",
        "year": 1979,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. P40, LFN 2004 / Act No. 31 of 1979",
        "enactment_date": "1st January 1979",
        "description": "An Act to repeal all the State Laws on public holidays and to make provisions for the whole Federation for public holidays and other related matters.",
        "out_file": "public_holidays_act.json",
        "expected_sections": 7
    },
    {
        "sn": 193,
        "statute_id": "foreign_judgments_act_1960",
        "title": "Foreign Judgments (Reciprocal Enforcement) Act, 1960",
        "short_title": "Foreign Judgments Act",
        "year": 1960,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. F35, LFN 2004 / Act No. 31 of 1960",
        "enactment_date": "1st February 1961",
        "description": "An Act to make provision for the enforcement in Nigeria of judgments given in foreign countries which accord reciprocal treatment to judgments given in Nigeria.",
        "out_file": "foreign_judgments_act.json",
        "expected_sections": 15
    }
]

def clean_txt(s):
    s = s.replace("\xa0", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def normalize_title_for_matching(t):
    t = t.lower()
    t = re.sub(r"part\s+[ivxlcdm\d]+", "", t)
    t = re.sub(r"[\-\—\–]", "", t) # Remove hyphens so Mon-days matches Mondays
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return t

def extract_statute(cfg):
    sn = cfg["sn"]
    expected_secs = cfg["expected_sections"]
    print(f"\n[*] Fetching and parsing SN {sn} ({cfg['title']})...")
    
    url = f"https://placng.org/lawsofnigeria/view2.php?sn={sn}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        
    soup = BeautifulSoup(html, "html.parser")
    body_div = soup.find("div", class_="field-name-body")
    text = body_div.get_text()
    raw_lines = [clean_txt(l) for l in text.splitlines() if clean_txt(l)]

    # 1. Locate Preamble / Enactment
    enact_idx = None
    for i, l in enumerate(raw_lines):
        if ("An Act to" in l or "AN ACT TO" in l or "An Act To" in l) and i > 2:
            enact_idx = i
            break
    if enact_idx is None:
        for i, l in enumerate(raw_lines):
            if re.match(r"^\[\d{4}\s+No\.", l) or "[Commencement.]" in l or "[1st" in l or "[ 1st" in l:
                enact_idx = i
                break
    if enact_idx is None:
        enact_idx = 0

    toc_lines = raw_lines[:enact_idx]
    substantive_lines = raw_lines[enact_idx:]

    # 2. Extract TOC
    toc = []
    current_part = "General Provisions"
    for l in toc_lines:
        if "ARRANGEMENT" in l.upper() or l.upper() == "SECTION":
            continue
        part_m = re.match(r"^(PART|CHAPTER)\s+([IVXLCDM\d]+|[A-Z])\b(.*)$", l, re.IGNORECASE)
        if part_m:
            current_part = l
            continue
        if "SCHEDULE" in l.upper() and len(l) < 30:
            break
        m = re.match(r"^(\d{1,3})\.\s*(.*)$", l)
        if m:
            s_t = m.group(2).strip().rstrip(".")
            toc.append((int(m.group(1)), s_t, current_part))
        elif len(l) > 2 and not l.isupper() and not l.startswith("["):
            # If it doesn't look like a Part title, append
            if not l.startswith("Offences") and not l.startswith("Electronic") and not l.startswith("Jurisdiction") and not l.startswith("Miscellaneous"):
                toc.append((len(toc) + 1, l.strip().rstrip("."), current_part))

    # Special adjustments for specific acts if needed
    if cfg["short_title"] == "Advance Fee Fraud Act":
        # Advance Fee Fraud Act has 22 sections:
        # 1. Obtaining property by false pretence, etc.
        # 2. Other fraud related offences
        # 3. Use of premises
        # 4. Fraudulent invitation
        # 5. Receipt of fraudulent document by victim to constitute attempt
        # 6. Possession of fraudulent document to constitute attempt
        # 7. Laundering of fund obtained through unlawful activity, etc.
        # 8. Conspiracy, aiding, etc.
        # 9. Conviction for alternative offences
        # 10. Offences by bodies corporate
        # 11. Restitution
        # 12. Duty to obtain subscriber's name and address
        # 13. Duties of telecommunication internet service providers and internet cafes
        # 14. Jurisdiction to try offences, etc.
        # 15. Possession of pecuniary resources not accounted for
        # 16. Power to control property of an accused person
        # 17. Power to make order of forfeiture without conviction for an offence
        # 18. Power of arrest
        # 19. Power to grant bail
        # 20. Interpretation
        # 21. Repeal
        # 22. Citation
        toc = [
            (1, "Obtaining property by false pretence, etc.", "Part I: Offences"),
            (2, "Other fraud related offences", "Part I: Offences"),
            (3, "Use of premises", "Part I: Offences"),
            (4, "Fraudulent invitation", "Part I: Offences"),
            (5, "Receipt of fraudulent document by victim to constitute attempt", "Part I: Offences"),
            (6, "Possession of fraudulent document to constitute attempt", "Part I: Offences"),
            (7, "Laundering of fund obtained through unlawful activity, etc.", "Part I: Offences"),
            (8, "Conspiracy, aiding, etc.", "Part I: Offences"),
            (9, "Conviction for alternative offences", "Part I: Offences"),
            (10, "Offences by bodies corporate", "Part I: Offences"),
            (11, "Restitution", "Part I: Offences"),
            (12, "Duty to obtain subscriber's name and address", "Part II: Electronic Telecommunication Offences, etc."),
            (13, "Duties of telecommunication internet service providers and internet cafes", "Part II: Electronic Telecommunication Offences, etc."),
            (14, "Jurisdiction to try offences, etc.", "Part III: Jurisdiction"),
            (15, "Possession of pecuniary resources not accounted for", "Part III: Jurisdiction"),
            (16, "Power to control property of an accused person", "Part III: Jurisdiction"),
            (17, "Power to make order of forfeiture without conviction for an offence", "Part III: Jurisdiction"),
            (18, "Power of arrest", "Part III: Jurisdiction"),
            (19, "Power to grant bail", "Part III: Jurisdiction"),
            (20, "Interpretation", "Part IV: Miscellaneous"),
            (21, "Repeal of the Advance Fee Fraud and Other Fraud Related Offences Act", "Part IV: Miscellaneous"),
            (22, "Citation", "Part IV: Miscellaneous")
        ]

    # 3. Locate each section in substantive_lines
    sec_matches = []
    curr_line_idx = 0

    for s_num, s_title, part in toc:
        if s_num > expected_secs:
            break
        matched_idx = None
        s_norm = normalize_title_for_matching(s_title)
        
        for j in range(curr_line_idx, len(substantive_lines)):
            l = substantive_lines[j]
            l_norm = normalize_title_for_matching(l)
            
            # Pattern A: starts with 's_num. ' or 's_num '
            if re.match(rf"^{s_num}[\.\s]", l) and not l.startswith(f"{s_num}. ("):
                matched_idx = j
                break
            if re.match(rf"^{s_num}\.\s+", l):
                matched_idx = j
                break
            # Pattern B: exact or prefix match of title
            if s_norm and len(s_norm) > 3:
                prefix = s_norm[:min(len(s_norm), 12)]
                if prefix in l_norm:
                    matched_idx = j
                    break
            # Special case for citation
            if s_num == expected_secs and ("cited as" in l or "cited as the" in l):
                matched_idx = j
                break

        if matched_idx is not None:
            sec_matches.append((s_num, s_title, part, matched_idx))
            curr_line_idx = matched_idx + 1
        else:
            print(f"   [MISS] Sec {s_num}: \"{s_title}\"")

    print(f"    Matched {len(sec_matches)} / {expected_secs} sections.")

    sections_json = []
    for i, (s_num, s_title, part, line_idx) in enumerate(sec_matches):
        body_start = line_idx + 1
        if i + 1 < len(sec_matches):
            body_end = sec_matches[i+1][3]
        else:
            body_end = len(substantive_lines)
            for k in range(body_start, len(substantive_lines)):
                if "FIRST SCHEDULE" in substantive_lines[k].upper() or "SCHEDULES" in substantive_lines[k].upper():
                    body_end = k
                    break

        sec_body_lines = substantive_lines[body_start:body_end]
        body_text = "\n".join(sec_body_lines).strip()
        if not body_text:
            body_text = s_title

        sections_json.append({
            "section_number": str(s_num),
            "section_title": s_title.strip().rstrip("."),
            "part": part,
            "full_text": body_text,
            "searchable_chunk": f"{cfg['title']} - Section {s_num}: {s_title}\n{part}\n{body_text}"
        })

    manifest = {
        "statute_id": cfg["statute_id"],
        "title": cfg["title"],
        "short_title": cfg["short_title"],
        "year": cfg["year"],
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": cfg["gazette_number"],
        "enactment_date": cfg["enactment_date"],
        "description": cfg["description"],
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = f"data/json_laws/{cfg['out_file']}"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)

if __name__ == "__main__":
    total = 0
    for cfg in PLAC_HTML_ACTS:
        total += extract_statute(cfg)
    print(f"\n=======================================================")
    print(f"COMPLETED PLAC HTML EXTRACTION: Total sections: {total}")
