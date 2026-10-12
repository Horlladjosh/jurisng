import json
import re
from pathlib import Path

JSON_PATH = Path("data/json_laws/money_laundering_act_2011.json")
SHORT_TITLE = "Money Laundering (Prohibition) Act, 2011"

MISSING_SECTIONS = [
    {
        "section_number": "15",
        "section_title": "Money laundering offences",
        "part": "PART II - OFFENCES",
        "full_text": (
            "15. (1) A person who—\n"
            "(a) converts or transfers resources or properties derived directly or indirectly from illicit traffic in "
            "narcotic drugs or psychotropic substances or any other crime or illegal act, with the aim of concealing "
            "or disguising the illicit origin of the resources or property or aiding any person involved to evade the "
            "legal consequences of his action;\n"
            "(b) collaborates in concealing or disguising the genuine nature, origin, location, disposition, movement "
            "or ownership of the resources, property or rights thereto derived directly or indirectly from illicit traffic "
            "in narcotic drugs or psychotropic substances or any other crime or illegal act;\n"
            "commits an offence under this section and is liable on conviction to imprisonment for a term of not less "
            "than 5 years but not more than 8 years.\n"
            "(2) A person who commits an offence under subsection (1) of this section shall be liable on conviction—\n"
            "(a) in the case of an individual, to imprisonment for a term of not less than 5 years but not more than 8 years;\n"
            "(b) in the case of a financial institution or designated non-financial institution, to a fine of not less than "
            "N10,000,000 or forfeiture of the assets, or both."
        )
    },
    {
        "section_number": "16",
        "section_title": "Other offences",
        "part": "PART II - OFFENCES",
        "full_text": (
            "16. (1) A person who—\n"
            "(a) being a director, officer or employee of a financial institution or designated non-financial institution "
            "warns or in any other way intimates the owner of the funds or securities involving a transaction under this Act;\n"
            "(b) destroys or removes a register or record required to be kept under this Act;\n"
            "(c) carries out or attempts under a false name to carry out any of the operations specified in sections 1 to 5 of this Act;\n"
            "(d) fails to report an international transfer of funds or securities as required under this Act;\n"
            "commits an offence.\n"
            "(2) A person who commits an offence under subsection (1) of this section shall be liable on conviction—\n"
            "(a) in the case of an offence under subsection (1)(a) or (b), to imprisonment for a term of not less than 2 years but not more than 3 years;\n"
            "(b) in the case of an offence under subsection (1)(c) or (d), to imprisonment for a term of not less than 2 years or a fine of not less than N500,000 or both."
        )
    },
    {
        "section_number": "25",
        "section_title": "Interpretation",
        "part": "PART III - MISCELLANEOUS",
        "full_text": (
            "25. In this Act—\n"
            "'Central Bank' means the Central Bank of Nigeria;\n"
            "'Commission' means the Economic and Financial Crimes Commission;\n"
            "'Designated Non-Financial Institution' means dealers in jewelry, cars and luxury goods, chartered accountants, "
            "audit firms, tax consultants, clearing and settlement companies, legal practitioners, hotels, casinos, "
            "supermarkets, or such other businesses as the Federal Ministry of Commerce or appropriate regulatory authorities may designate;\n"
            "'Financial Institution' means banks, offshore banking corporations, insurance companies, brokerage firms, investment companies, "
            "and other financial institutions defined under the Banks and Other Financial Institutions Act;\n"
            "'Money Laundering' has the meaning assigned to it in section 15 of this Act;\n"
            "'Transactions' means a purchase, sale, loan, pledge, gift, transfer, delivery or other disposition of property or resources."
        )
    },
    {
        "section_number": "26",
        "section_title": "Citation",
        "part": "PART III - MISCELLANEOUS",
        "full_text": "26. This Act may be cited as the Money Laundering (Prohibition) Act, 2011."
    }
]

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

sec_map = {int(s["section_number"]): s for s in data.get("sections", []) if s["section_number"].isdigit()}

for s in MISSING_SECTIONS:
    num = int(s["section_number"])
    s_num = str(num)
    s_title = s["section_title"].strip()
    s_part = s["part"].strip()
    s_body = s["full_text"].strip()
    sec_map[num] = {
        "section_number": s_num,
        "section_title": s_title,
        "part": s_part,
        "full_text": s_body,
        "searchable_chunk": f"{SHORT_TITLE} | {s_part} | {s_num}. {s_title} | {s_body}"
    }
    print(f"[+] Finalized Section {num}: {s_title}")

sorted_secs = [sec_map[k] for k in sorted(sec_map.keys())]
data["sections"] = sorted_secs
data["total_sections"] = len(sorted_secs)

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n[✓] Money Laundering Act successfully integrated: {len(sorted_secs)}/26 sections present.")
