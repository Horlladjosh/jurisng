import json

def audit_cybercrimes():
    json_path = "data/json_laws/cybercrimes_act_2015.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sections = {int(s["section_number"]): s for s in data["sections"]}
    print("=" * 65)
    print("LEGAL INTEGRITY AUDIT: CYBERCRIMES ACT 2015")
    print("=" * 65)

    # Key landmark provisions
    landmarks = {
        1: ("Objectives", ["objectives", "framework"]),
        3: ("Critical National Information Infrastructure", ["critical", "infrastructure"]),
        5: ("Offences against Critical National Infrastructure", ["death", "imprisonment", "unauthorised"]),
        12: ("System Interference", ["computer", "access", "interferes"]),
        14: ("Child Pornography", ["child", "pornography", "visual"]),
        15: ("Cyberstalking", ["cyberstalking", "message", "threat"]),
        24: ("Cyberstalking / Offensive Messages", ["offensive", "false", "annoyance", "insult"]),
        38: ("Record Retention by Service Providers", ["traffic data", "service provider"]),
        44: ("Establishment of Cybercrime Advisory Council", ["advisory council", "national security adviser"]),
        58: ("Interpretation", ["computer", "cybercrime", "data"])
    }

    passed = 0
    for sec_num, (desc, keywords) in landmarks.items():
        if sec_num in sections:
            txt = sections[sec_num]["full_text"].lower()
            matches = [k for k in keywords if k.lower() in txt]
            if matches:
                print(f"  ✓ Section {sec_num:>2} [{desc:<38}]: Found '{matches[0]}'")
                passed += 1
            else:
                print(f"  ✗ Section {sec_num:>2} [{desc:<38}]: Keyword mismatch")
        else:
            print(f"  ✗ Section {sec_num:>2} missing entirely!")

    print("\n" + "-" * 65)
    print(f"Total Sections Indexed: {len(sections)} / 59")
    print("=" * 65)

if __name__ == "__main__":
    audit_cybercrimes()
