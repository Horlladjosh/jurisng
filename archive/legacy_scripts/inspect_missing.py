import json
import re
from pathlib import Path
from pypdf import PdfReader

def check_statute(json_path, pdf_path, expected_max):
    print("=" * 65)
    print(f"AUDITING: {json_path}")
    print("=" * 65)
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    found_nums = set()
    for s in data["sections"]:
        # Extract base digits
        digits = re.findall(r'\d+', s["section_number"])
        if digits:
            found_nums.add(int(digits[0]))
            
    all_expected = set(range(1, expected_max + 1))
    missing = sorted(list(all_expected - found_nums))
    print(f"Missing Numbers ({len(missing)} total):\n{missing}\n")
    
    # Read full PDF text to search for where the first 5 missing numbers appear
    reader = PdfReader(pdf_path)
    full_pdf_text = "\n".join(p.extract_text() or "" for p in reader.pages)
    
    print("Inspecting how missing numbers appear in raw PDF text:")
    for num in missing[:5]:
        print(f"\n--- Searching for Section {num} in PDF text ---")
        matches = [m.start() for m in re.finditer(rf'\b{num}\b', full_pdf_text)]
        if not matches:
            print(f"  [X] Number '{num}' does NOT exist anywhere in the extracted text stream.")
        else:
            for idx in matches[:2]:
                snippet = full_pdf_text[max(0, idx-40):min(len(full_pdf_text), idx+100)]
                print(f"  Found '{num}' snippet: {repr(snippet)}")

if __name__ == "__main__":
    check_statute("data/json_laws/cybercrimes_act_2015.json", "data/raw_pdfs/cybercrimes-act-2015.pdf", 59)
    check_statute("data/json_laws/evidence_act_2011.json", "data/raw_pdfs/evidence-act-2011.pdf", 259)
