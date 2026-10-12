import json
import re
from pathlib import Path

STATUTE_CHECKS = {
    "cfrn_1999": {
        "file": "cfrn_1999.json",
        "name": "Constitution of the Federal Republic of Nigeria 1999",
        "expected": 320,
        "landmarks": {
            1: ("Supremacy of Constitution", ["supreme", "constitution", "binding"]),
            33: ("Right to Life", ["life", "deprived"]),
            35: ("Right to Personal Liberty", ["liberty", "unlawful arrest", "detention"]),
            36: ("Right to Fair Hearing", ["fair hearing", "court", "tribunal"]),
            42: ("Right to Freedom from Discrimination", ["discrimination", "ethnic", "sex"]),
            214: ("Establishment of Nigeria Police Force", ["police force", "federation"]),
            230: ("Establishment of Supreme Court", ["supreme court", "chief justice"]),
            287: ("Enforcement of Decisions", ["decisions", "supreme court", "enforced"])
        }
    },
    "acja_2015": {
        "file": "acja_2015.json",
        "name": "Administration of Criminal Justice Act 2015",
        "expected": 495,
        "landmarks": {
            1: ("Purpose of the Act", ["purpose", "administration", "criminal justice"]),
            15: ("Recording of Arrest / Electronic Confession", ["electronic", "recording", "video", "confession"]),
            17: ("Recording of Confessional Statement", ["statement", "legal practitioner"]),
            158: ("General Entitlement to Bail", ["bail", "recognizance", "applicant"]),
            165: ("Conditions for Bail", ["bail", "security", "court"]),
            221: ("Stay of Proceedings", ["stay of proceedings", "interlocutory", "objection", "stay"]),
            306: ("Stay of Proceedings Prohibited", ["stay of proceedings", "application"])
        }
    },
    "child_rights_act_2003": {
        "file": "child_rights_act_2003.json",
        "name": "Child's Rights Act 2003",
        "expected": 278,
        "landmarks": {
            1: ("Best Interests of the Child", ["best interest", "primary consideration", "child"]),
            3: ("Application of Chapter IV CFRN", ["chapter iv", "constitution", "child"]),
            11: ("Right to Dignity of the Child", ["dignity", "physical", "mental", "abuse"]),
            21: ("Prohibition of Child Marriage", ["marriage", "child", "betrothal", "void"]),
            28: ("Prohibition of Exploitative Child Labour", ["labour", "employment", "child"]),
            149: ("Establishment of Family Court", ["family court", "jurisdiction"])
        }
    },
    "evidence_act_2011": {
        "file": "evidence_act_2011.json",
        "name": "Evidence Act 2011",
        "expected": 259,
        "landmarks": {
            1: ("Evidence of Facts in Issue", ["evidence", "facts in issue", "relevant"]),
            20: ("Admission Defined", ["admission", "statement", "oral", "documentary"]),
            27: ("Confession Defined", ["confession", "admission made at any time"]),
            84: ("Admissibility of Computer/Electronic Evidence", ["computer", "document produced by a computer", "device"]),
            102: ("Public Documents", ["public documents", "sovereign authority", "official acts"]),
            135: ("Standard of Proof in Criminal Cases", ["beyond reasonable doubt", "prosecution"]),
            136: ("Burden of Proof as to Particular Fact", ["burden of proof", "particular fact", "burden"]),
            258: ("Interpretation", ["bankers' books", "court", "custom", "document"])
        }
    },
    "police_act_2020": {
        "file": "police_act_2020.json",
        "name": "Nigeria Police Act 2020",
        "expected": 142,
        "landmarks": {
            1: ("Objective of the Act", ["objective", "police force", "effective"]),
            4: ("Duties of the Police Force", ["prevent", "detect", "crimes", "peace"]),
            38: ("Prohibition of Arrest on Civil Matters", ["civil wrong", "breach of contract", "civil"]),
            66: ("Right of Arrested Person to Legal Counsel", ["legal practitioner", "free legal aid"]),
            91: ("Power to Prosecute", ["prosecute", "criminal", "consent", "police officer"])
        }
    },
    "labour_act": {
        "file": "labour_act.json",
        "name": "Labour Act",
        "expected": 92,
        "landmarks": {
            1: ("Written Terms of Employment", ["written terms", "contract", "employer", "worker", "wages"]),
            7: ("Written Terms of Employment", ["particulars", "employment", "wages"]),
            9: ("Contracts of Employment Generally", ["contract of employment", "validity", "contract"]),
            11: ("Notice of Termination of Contract", ["notice", "termination", "contract"]),
            54: ("Maternity Protection", ["pregnant", "maternity", "leave", "confinement"]),
            59: ("Young Persons Employment", ["young person", "child", "employment"])
        }
    },
    "employee_compensation_act_2010": {
        "file": "employee_compensation_act_2010.json",
        "name": "Employees' Compensation Act 2010",
        "expected": 74,
        "landmarks": {
            1: ("Objectives of the Act", ["objectives", "compensation", "death", "injury"]),
            7: ("Compensation for Injury Occurring in Course of Employment", ["injury", "employment", "compensation"]),
            12: ("Compensation in Case of Death", ["death", "dependants", "monthly payments"]),
            31: ("Establishment of Employees' Compensation Fund", ["fund", "contributions", "board"]),
            56: ("Establishment of Management Board", ["board", "nsitf", "management"])
        }
    },
    "penal_code_act_1960": {
        "file": "penal_code_act_1960.json",
        "name": "Penal Code Act (Federal Provisions)",
        "expected": 73,
        "landmarks": {
            1: ("Short Title", ["short title", "penal code"]),
            410: ("Treason Defined", ["treason", "president", "levies war", "war"]),
            416: ("Sedition", ["seditious", "intention", "government"]),
            430: ("Unlawful Assembly / Riot", ["assembly", "riot", "peace"]),
            475: ("Bribery / Public Servants", ["public servant", "gratification", "bribe", "property"])
        }
    },
    "cybercrimes_act_2015": {
        "file": "cybercrimes_act_2015.json",
        "name": "Cybercrimes (Prohibition, Prevention, etc.) Act 2015",
        "expected": 59,
        "landmarks": {
            1: ("Objectives", ["objectives", "framework", "cybercrime"]),
            3: ("Designation of Critical National Infrastructure", ["critical", "national information infrastructure"]),
            5: ("Offences against Critical National Infrastructure", ["critical infrastructure", "death", "imprisonment"]),
            14: ("Computer Related Fraud", ["fraud", "computer", "financial gain"]),
            23: ("Child Pornography", ["child pornography", "visual depiction", "minor"]),
            24: ("Cyberstalking / Offensive Messages", ["cyberstalking", "offensive", "annoyance", "false"]),
            38: ("Record Retention by Service Providers", ["traffic data", "service provider", "retention"]),
            58: ("Interpretation", ["computer", "cybercrime", "data", "traffic data"])
        }
    },
    "land_use_act_1978": {
        "file": "land_use_act_1978.json",
        "name": "Land Use Act 1978",
        "expected": 51,
        "landmarks": {
            1: ("Vesting of All Land in State Governors", ["all land", "territory of each state", "vested in the governor", "governor"]),
            5: ("Powers of the Governor to Grant Rights of Occupancy", ["statutory right of occupancy", "governor", "grant"]),
            21: ("Alienation of Customary Right of Occupancy", ["customary right of occupancy", "consent", "local government"]),
            22: ("Alienation of Statutory Right of Occupancy", ["consent of the governor", "alienate", "mortgage", "transfer", "consent"]),
            28: ("Revocation of Rights of Occupancy", ["revoke", "right of occupancy", "overriding public interest"])
        }
    }
}

def run_master_audit():
    print("=" * 80)
    print("        MASTER STATUTORY FIDELITY AUDIT — STATUTES 1 THROUGH 10")
    print("=" * 80)

    base_dir = Path("data/json_laws")

    for key, spec in STATUTE_CHECKS.items():
        file_path = base_dir / spec["file"]
        print(f"\n>> AUDITING: {spec['name']}")
        print(f"   File: {file_path.name}")

        if not file_path.exists():
            print(f"   [FAIL] File does not exist: {file_path.name}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_sections = data.get("sections", [])
        
        sec_map = {}
        for s in raw_sections:
            digits = re.findall(r'\d+', s.get("section_number", ""))
            if digits:
                sec_map[int(digits[0])] = s

        total_found = len(raw_sections)
        lengths = [len(s.get("full_text", "")) for s in raw_sections]
        short_entries = [s.get("section_number") for s in raw_sections if len(s.get("full_text", "")) < 35]
        avg_len = sum(lengths) // len(lengths) if lengths else 0

        print(f"   • Total Sections Indexed : {total_found} (Target: ~{spec['expected']})")
        if short_entries:
            print(f"   • [WARN] Short snippets (<35 chars): {short_entries[:6]}")
        else:
            print(f"   • Substantive Depth      : Passed (Avg {avg_len:,} chars/section, 0 TOC snippets)")

        print(f"   • Landmark Checks        :")
        statute_passed = True
        for sec_num, (desc, keywords) in spec["landmarks"].items():
            if sec_num in sec_map:
                body = sec_map[sec_num].get("full_text", "").lower()
                title = sec_map[sec_num].get("section_title", "").lower()
                comb = f"{title} {body}"
                
                matched = [k for k in keywords if k.lower() in comb]
                if matched:
                    print(f"     ✓ Sec {sec_num:>3} [{desc:<38}]: Verified '{matched[0]}'")
                else:
                    print(f"     ✗ Sec {sec_num:>3} [{desc:<38}]: Text preview: {body[:90]}...")
                    statute_passed = False
            else:
                print(f"     ✗ Sec {sec_num:>3} [{desc:<38}]: Section missing from map!")
                statute_passed = False

        status = "PASSED" if statute_passed and not short_entries else "ATTENTION NEEDED"
        print(f"   --> Status: [{status}]")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_master_audit()
