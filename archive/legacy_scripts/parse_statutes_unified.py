import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_DIR = Path("data/json_laws")
RAW_DIR = Path("data/raw_pdfs")

# Universal Nigerian Act Schedule / Closing markers
SCHEDULE_SPLIT_PATTERNS = [
    r'\n\s*FIRST\s+SCHEDULE\b',
    r'\n\s*SCHEDULE\s+1\b',
    r'\n\s*SCHEDULES\b',
    r'\n\s*EXPLANATORY\s+MEMORANDUM\b'
]

def extract_statute_sections(pdf_filename, start_page, total_expected, statute_id, statute_title, short_title, year):
    pdf_path = RAW_DIR / pdf_filename
    if not pdf_path.exists():
        print(f"[!] PDF not found: {pdf_filename} — skipping.")
        return None

    reader = PdfReader(str(pdf_path))
    raw_pages = [reader.pages[i].extract_text() or "" for i in range(start_page - 1, len(reader.pages))]
    full_text = "\n".join(raw_pages).replace('\xa0', ' ')
    
    # Isolate substantive law from trailing schedules
    substantive_text = full_text
    for sched_pat in SCHEDULE_SPLIT_PATTERNS:
        m = re.search(sched_pat, substantive_text)
        if m:
            substantive_text = substantive_text[:m.start()]
            break

    # 1. Global Section Boundary Locator
    section_positions = {}
    
    for i in range(1, total_expected + 1):
        patterns = [
            rf'(?:\n|^)\s*{i}(?:\.|\s+)\s*(?:\([0-9a-zA-Z]+\)|[A-Z])',
            rf'(?:\n|^)\s*{i}\.\s+',
            rf'(?:\n|^)\s*Section\s+{i}\.?\s+'
        ]
        
        pos = None
        prev_pos = section_positions.get(i - 1, 0)
        
        for pat in patterns:
            matches = list(re.finditer(pat, substantive_text[prev_pos:]))
            if matches:
                pos = prev_pos + matches[0].start()
                break
                
        if pos is not None:
            section_positions[i] = pos
        else:
            print(f"  [!] {short_title}: Missing marker for Section {i}")

    # 2. Contiguous Text Slicing
    sections = []
    found_numbers = sorted(section_positions.keys())
    
    for idx, num in enumerate(found_numbers):
        start_idx = section_positions[num]
        
        if idx + 1 < len(found_numbers):
            next_num = found_numbers[idx + 1]
            end_idx = section_positions[next_num]
            sec_text = substantive_text[start_idx:end_idx].strip()
        else:
            sec_text = substantive_text[start_idx:].strip()

        cleaned = re.sub(r'[ \t]+', ' ', sec_text)
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned).strip()

        sections.append({
            "section_number": str(num),
            "section_title": f"Section {num}",
            "full_text": cleaned,
            "searchable_chunk": f"{short_title} | Section {num} | {cleaned}"
        })

    payload = {
        "statute_id": statute_id,
        "statute_title": statute_title,
        "short_title": short_title,
        "year": str(year),
        "total_sections_found": len(sections),
        "expected_sections": total_expected,
        "total_sections": len(sections),
        "sections": sections
    }

    out_path = JSON_DIR / f"{statute_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    status_icon = "[✓]" if len(sections) == total_expected else "[!]"
    print(f"{status_icon} {short_title}: {len(sections)} / {total_expected} sections parsed.")
    return len(sections)

print("=" * 80)
print("RUNNING MASTER UNIFIED STATUTE PARSER")
print("=" * 80)

STATUTES = [
    {
        "pdf_filename": "acja-2015.pdf",
        "start_page": 21,
        "total_expected": 495,
        "statute_id": "acja_2015",
        "statute_title": "Administration of Criminal Justice Act, 2015",
        "short_title": "ACJA 2015",
        "year": "2015"
    },
    {
        "pdf_filename": "child-rights-act.pdf",
        "start_page": 12,
        "total_expected": 278,
        "statute_id": "child_rights_act_2003",
        "statute_title": "Child's Rights Act, 2003",
        "short_title": "Child's Rights Act 2003",
        "year": "2003"
    },
    {
        "pdf_filename": "cybercrimes-act-2015.pdf",
        "start_page": 5,
        "total_expected": 59,
        "statute_id": "cybercrimes_act_2015",
        "statute_title": "Cybercrimes (Prohibition, Prevention, Etc.) Act, 2015",
        "short_title": "Cybercrimes Act 2015",
        "year": "2015"
    },
    {
        "pdf_filename": "fccpa-2018.pdf",
        "start_page": 10,
        "total_expected": 168,
        "statute_id": "fccpa_2018",
        "statute_title": "Federal Competition and Consumer Protection Act, 2018",
        "short_title": "FCCPA 2018",
        "year": "2018"
    },
    {
        "pdf_filename": "labour-act.pdf",
        "start_page": 4,
        "total_expected": 90,
        "statute_id": "labour_act",
        "statute_title": "Labour Act",
        "short_title": "Labour Act",
        "year": "1971"
    },
    {
        "pdf_filename": "national-health-act-2014.pdf",
        "start_page": 5,
        "total_expected": 65,
        "statute_id": "national_health_act_2014",
        "statute_title": "National Health Act, 2014",
        "short_title": "National Health Act 2014",
        "year": "2014"
    }
]

for stat in STATUTES:
    extract_statute_sections(**stat)

print("=" * 80)
