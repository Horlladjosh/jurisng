import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_DIR = Path("data/json_laws")
RAW_DIR = Path("data/raw_pdfs")

# Master inventory of all 10 active statutes with exact expected section counts and PDF mappings
TARGET_STATUTES = [
    {
        "id": "acja_2015",
        "title": "Administration of Criminal Justice Act, 2015",
        "short_title": "ACJA 2015",
        "year": "2015",
        "pdf": "acja-2015.pdf",
        "expected": 494,
        "start_page": 1
    },
    {
        "id": "cfrn_1999",
        "title": "Constitution of the Federal Republic of Nigeria, 1999",
        "short_title": "CFRN 1999",
        "year": "1999",
        "pdf": "cfrn_1999.pdf",
        "expected": 316,
        "start_page": 1
    },
    {
        "id": "child_rights_act_2003",
        "title": "Child's Rights Act, 2003",
        "short_title": "Child's Rights Act 2003",
        "year": "2003",
        "pdf": "child-rights-act.pdf",
        "expected": 278,
        "start_page": 12
    },
    {
        "id": "cybercrimes_act_2015",
        "title": "Cybercrimes (Prohibition, Prevention, Etc.) Act, 2015",
        "short_title": "Cybercrimes Act 2015",
        "year": "2015",
        "pdf": "cybercrimes-act-2015.pdf",
        "expected": 59,
        "start_page": 5
    },
    {
        "id": "employees_compensation_act_2010",
        "title": "Employees' Compensation Act, 2010",
        "short_title": "Employees' Compensation Act 2010",
        "year": "2010",
        "pdf": "employees-compensation-act-2010.pdf",
        "expected": 74,
        "start_page": 5
    },
    {
        "id": "evidence_act_2011",
        "title": "Evidence Act, 2011",
        "short_title": "Evidence Act 2011",
        "year": "2011",
        "pdf": "evidence-act-2011.pdf",
        "expected": 224,
        "start_page": 10
    },
    {
        "id": "fccpa_2018",
        "title": "Federal Competition and Consumer Protection Act, 2018",
        "short_title": "FCCPA 2018",
        "year": "2018",
        "pdf": "fccpa-2018.pdf",
        "expected": 31,
        "start_page": 10
    },
    {
        "id": "labour_act",
        "title": "Labour Act",
        "short_title": "Labour Act",
        "year": "1971",
        "pdf": "labour-act.pdf",
        "expected": 90,
        "start_page": 4
    },
    {
        "id": "land_use_act_1978",
        "title": "Land Use Act, 1978",
        "short_title": "Land Use Act 1978",
        "year": "1978",
        "pdf": "land-use-act-1978.pdf",
        "expected": 51,
        "start_page": 3
    },
    {
        "id": "national_health_act_2014",
        "title": "National Health Act, 2014",
        "short_title": "National Health Act 2014",
        "year": "2014",
        "pdf": "national-health-act-2014.pdf",
        "expected": 12,
        "start_page": 5
    },
    {
        "id": "penal_code_act_1960",
        "title": "Penal Code Act",
        "short_title": "Penal Code Act",
        "year": "1960",
        "pdf": "penal-code-act.pdf",
        "expected": 74,
        "start_page": 5
    },
    {
        "id": "police_act_2020",
        "title": "Police Act, 2020",
        "short_title": "Police Act 2020",
        "year": "2020",
        "pdf": "police_act_2020.pdf",
        "expected": 138,
        "start_page": 8
    }
]

print("=" * 80)
print("PRISTINE CORPUS RECONSTRUCTION & VERIFICATION")
print("=" * 80)

for cfg in TARGET_STATUTES:
    pdf_path = RAW_DIR / cfg["pdf"]
    if not pdf_path.exists():
        print(f"[!] MISSING PDF: {cfg['pdf']} (Skipping)")
        continue

    reader = PdfReader(str(pdf_path))
    full_text = "\n".join(p.extract_text() or "" for p in reader.pages[cfg["start_page"] - 1:])

    # Strip trailing schedules so final sections don't swallow appendix text
    for marker in ["FIRST SCHEDULE", "SECOND SCHEDULE", "SCHEDULES", "EXPLANATORY MEMORANDUM"]:
        if marker in full_text:
            full_text = full_text.split(marker)[0]

    sections = []
    expected_count = cfg["expected"]

    for i in range(1, expected_count + 1):
        # Precise section boundary regex
        pat = rf'(?:\n|^)\s*{i}\.\s+([A-Z][a-zA-Z\s,\-\(\)\/\;\:\.\"]+)'
        matches = list(re.finditer(pat, full_text))

        if not matches:
            # Fallback pattern for dense formatting
            pat_alt = rf'(?:\n|^)\s*Section\s+{i}\.?\s+([A-Z][a-zA-Z\s,\-\(\)]+)'
            matches = list(re.finditer(pat_alt, full_text))

        if matches:
            start_pos = matches[0].start()
            
            # Find next section to cap upper boundary
            next_pat = rf'(?:\n|^)\s*{i+1}\.\s+[A-Z]'
            next_matches = list(re.finditer(next_pat, full_text[start_pos + len(matches[0].group(0)):]))
            
            if next_matches:
                end_pos = start_pos + len(matches[0].group(0)) + next_matches[0].start()
                sec_text = full_text[start_pos:end_pos].strip()
            else:
                sec_text = full_text[start_pos:start_pos + 4000].strip()

            cleaned = re.sub(r'\s+', ' ', sec_text)
            
            sections.append({
                "section_number": str(i),
                "section_title": f"Section {i}",
                "full_text": cleaned,
                "searchable_chunk": f"{cfg['short_title']} | Section {i} | {cleaned}"
            })

            # Advance window
            full_text = full_text[start_pos + len(sec_text):]

    # Save exact schema matching healthy JSONs
    output_filename = f"{cfg['id']}.json"
    output_path = JSON_DIR / output_filename

    payload = {
        "statute_id": cfg["id"],
        "statute_title": cfg["title"],
        "short_title": cfg["short_title"],
        "year": cfg["year"],
        "total_sections_found": len(sections),
        "expected_sections": expected_count,
        "total_sections": len(sections),
        "sections": sections
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    status_icon = "[✓]" if len(sections) == expected_count else "[!]"
    print(f"{status_icon} {cfg['short_title']}: Extracted {len(sections)} / {expected_count} sections.")

print("=" * 80)
print("EXTRACTION COMPLETE. Inspecting results...")
print("=" * 80)
