import json
import sys

JSON_PATH = "data/json_laws/acja_2015.json"

try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"[!] {JSON_PATH} not found. Please run the parser first.")
    sys.exit(1)

sec_map = {int(s["section_number"]): s["full_text"] for s in data.get("sections", [])}

def show_section(num):
    if num not in sec_map:
        print(f"\n[!] Section {num} not found (Valid range: 1 - {max(sec_map.keys())}).")
        return
    
    text = sec_map[num]
    print(f"\n{'='*75}")
    print(f"  ACJA 2015 — SECTION {num} (Length: {len(text):,} chars | Words: {len(text.split()):,})")
    print(f"{'='*75}")
    print(text)
    print(f"{'='*75}\n")

if len(sys.argv) > 1:
    arg = sys.argv[1].strip()
    if "-" in arg:
        try:
            start, end = map(int, arg.split("-"))
            for n in range(start, end + 1):
                show_section(n)
        except ValueError:
            print("[!] Format range as start-end (e.g., 15-18)")
    else:
        try:
            show_section(int(arg))
        except ValueError:
            print("[!] Please enter a valid integer section number.")
else:
    # Interactive CLI loop
    print("=" * 75)
    print("ACJA 2015 SECTION INSPECTOR")
    print("Enter a section number (e.g. 15), range (e.g. 15-18), or 'q' to quit.")
    print("=" * 75)
    while True:
        try:
            user_input = input("Enter section number or range: ").strip()
            if not user_input or user_input.lower() in ['q', 'exit', 'quit']:
                print("Exiting.")
                break
            if "-" in user_input:
                start, end = map(int, user_input.split("-"))
                for n in range(start, end + 1):
                    show_section(n)
            else:
                show_section(int(user_input))
        except (ValueError, KeyboardInterrupt):
            print("\nExiting.")
            break
