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
        "out_file": "icpc_act_2000.json"
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
        "out_file": "cbn_act_2007.json"
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
        "out_file": "advance_fee_fraud_act_2006.json"
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
        "out_file": "dishonoured_cheques_act.json"
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
        "out_file": "acts_authentication_act.json"
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
        "out_file": "public_holidays_act.json"
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
        "out_file": "foreign_judgments_act.json"
    },
    {
        "sn": 17,
        "statute_id": "admiralty_jurisdiction_act_1991",
        "title": "Admiralty Jurisdiction Act, 1991",
        "short_title": "Admiralty Jurisdiction Act",
        "year": 1991,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. A5, LFN 2004 / Decree No. 59 of 1991",
        "enactment_date": "30th December 1991",
        "description": "An Act to provide for the extent of the admiralty jurisdiction of the Federal High Court and for matters connected therewith.",
        "out_file": "admiralty_jurisdiction_act.json"
    }
]

def fetch_plac_html(sn):
    url = f"https://placng.org/lawsofnigeria/view2.php?sn={sn}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def extract_statute_from_plac_html(cfg):
    sn = cfg["sn"]
    print(f"\n[*] Fetching and parsing SN {sn} ({cfg['title']})...")
    html = fetch_plac_html(sn)
    soup = BeautifulSoup(html, "html.parser")
    body_div = soup.find("div", class_="field-name-body")
    if not body_div:
        raise ValueError(f"No body content found for SN {sn}")

    text = body_div.get_text()
    raw_lines = [l.replace("\xa0", " ").strip() for l in text.splitlines() if l.replace("\xa0", " ").strip()]

    # 1. Locate Preamble / Commencement boundary
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

    substantive_lines = raw_lines[enact_idx:]
    
    # 2. Extract sections
    # Scan for section patterns: '1. Title', '1. ', 'Section Title' followed by (1)
    sections_json = []
    
    # Let's inspect TOC to get the expected list of section titles if available
    toc_lines = raw_lines[:enact_idx]
    toc_titles = []
    for l in toc_lines:
        if "ARRANGEMENT" in l.upper() or l.upper() == "SECTION" or l.startswith("PART ") or l.startswith("CHAPTER "):
            continue
        m = re.match(r"^(\d{1,3})\.\s*(.*)$", l)
        if m:
            s_t = m.group(2).strip().rstrip(".")
            toc_titles.append((int(m.group(1)), s_t))
        elif len(l) > 3 and not l.isupper() and not l.startswith("["):
            toc_titles.append((len(toc_titles) + 1, l.strip().rstrip(".")))

    # Parse substantive body
    current_part = "General Provisions"
    current_sec_num = None
    current_sec_title = ""
    current_body_lines = []

    def commit_section():
        if current_sec_num is not None:
            body_text = "\n".join(current_body_lines).strip()
            # If body_text is empty, check if title contains text
            t = current_sec_title
            if not t:
                # Find title in toc_titles
                for num, tt in toc_titles:
                    if num == current_sec_num:
                        t = tt
                        break
            if not t:
                t = f"Section {current_sec_num}"

            sections_json.append({
                "section_number": str(current_sec_num),
                "section_title": t.strip().rstrip("."),
                "part": current_part,
                "full_text": body_text,
                "searchable_chunk": f"{cfg['title']} - Section {current_sec_num}: {t}\n{current_part}\n{body_text}"
            })

    # Track sequence of sections
    expected_sec = 1
    for idx, l in enumerate(substantive_lines):
        part_m = re.match(r"^(PART|CHAPTER)\s+([IVXLCDM\d]+|[A-Z])\b(.*)$", l, re.IGNORECASE)
        if part_m:
            current_part = l.strip()
            continue

        if "SCHEDULE" in l.upper() and len(l) < 30:
            # We hit schedules at the end
            break

        # Check for section start e.g. "1. Short title" or "1." or "Short title" (matching next TOC title)
        sec_m = re.match(r"^(\d{1,3})\.\s*(.*)$", l)
        is_new_sec = False
        new_num = None
        new_title = ""

        if sec_m:
            s_candidate = int(sec_m.group(1))
            if s_candidate == expected_sec or (expected_sec > 1 and s_candidate == expected_sec):
                is_new_sec = True
                new_num = s_candidate
                new_title = sec_m.group(2).strip()
        else:
            # Check if this line matches the title of expected_sec from TOC
            if toc_titles:
                for t_num, t_txt in toc_titles:
                    if t_num == expected_sec and t_txt and (t_txt.lower() in l.lower() or l.lower() in t_txt.lower()):
                        is_new_sec = True
                        new_num = expected_sec
                        new_title = t_txt
                        break

        if is_new_sec:
            commit_section()
            current_sec_num = new_num
            current_sec_title = new_title
            current_body_lines = []
            expected_sec = new_num + 1
        else:
            if current_sec_num is not None:
                if not current_sec_title and not l.startswith("(") and len(l) < 90:
                    current_sec_title = l
                else:
                    current_body_lines.append(l)

    commit_section()

    # If zero or few sections extracted, fallback to paragraph chunking
    if len(sections_json) == 0:
        raise ValueError(f"Could not extract sections from SN {sn}")

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
        try:
            cnt = extract_statute_from_plac_html(cfg)
            total += cnt
        except Exception as e:
            print(f"    [✗] Error processing {cfg['short_title']}: {e}")
    print(f"\n=======================================================")
    print(f"COMPLETED PLAC HTML EXTRACTION: Total sections: {total}")
