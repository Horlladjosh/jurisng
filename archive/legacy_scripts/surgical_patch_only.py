import re
import json
from pathlib import Path
from pypdf import PdfReader

RAW_DIR = Path("data/raw_pdfs")
JSON_DIR = Path("data/json_laws")

TARGETS = [
    {
        "json": "evidence_act_2011.json",
        "pdf": "evidence-act-2011.pdf",
        "title": "Evidence Act 2011",
        "max_sec": 259,
        "start_page": 10
    },
    {
        "json": "police_act_2020.json",
        "pdf": "police_act_2020.pdf",
        "title": "Police Act 2020",
        "max_sec": 142,
        "start_page": 8
    },
    {
        "json": "labour_act.json",
        "pdf": "labour-act.pdf",
        "title": "Labour Act",
        "max_sec": 92,
        "start_page": 4
    }
]

def clean_txt(t: str) -> str:
    return re.sub(r'\s+', ' ', t or '').strip()

def patch_file(target):
    json_path = JSON_DIR / target["json"]
    pdf_path = RAW_DIR / target["pdf"]
    
    if not json_path.exists() or not pdf_path.exists():
        print(f"[-] Missing file: {target['json']} or {target['pdf']}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Map existing valid sections (keep everything already extracted)
    existing_map = {}
    for sec in data.get("sections", []):
        try:
            num = int(re.findall(r'\d+', sec["section_number"])[0])
            existing_map[num] = sec
        except:
            pass

    max_sec = target["max_sec"]
    missing_nums = [i for i in range(1, max_sec + 1) if i not in existing_map]
    
    print(f"\n>> {target['title']}: {len(existing_map)}/{max_sec} present. Missing {len(missing_nums)} sections.")
    
    if not missing_nums:
        print(f"   [✓] Already 100% complete.")
        return

    # 2. Extract PDF text once
    reader = PdfReader(str(pdf_path))
    pages = [p.extract_text() or "" for p in reader.pages[target["start_page"] - 1:]]
    pdf_body = "\n".join(pages)
    pdf_body = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', pdf_body, flags=re.IGNORECASE)

    # 3. Surgically find only the missing sections
    recovered = 0
    for num in missing_nums:
        c_str = str(num)
        # Match section number anchored on newline/word boundary
        patterns = [
            rf'(?:\n|\A|\s{{2,}}){c_str}\s*[\.\-\–\—\:]\s*(.*?)(?=(?:\n|\s{{2,}})\d{{1,3}}\s*[\.\-\–\—\:]|\Z)',
            rf'(?:\n|\A|\s{{2,}}){c_str}\s*[\.\-\–\—\:]\s*(.*)',
            rf'\b{c_str}\.\s*(.*)'
        ]
        
        extracted_text = None
        for pat in patterns:
            m = re.search(pat, pdf_body, re.DOTALL)
            if m:
                candidate = clean_txt(m.group(1))
                if len(candidate) > 20:
                    # Take up to 2500 characters
                    extracted_text = candidate[:2500]
                    break
        
        if extracted_text:
            existing_map[num] = {
                "section_number": c_str,
                "section_title": f"Section {c_str}",
                "full_text": extracted_text,
                "searchable_chunk": f"{target['title']} | Section {c_str} | {extracted_text}"
            }
            recovered += 1

    # 4. Sort and save back into the JSON without touching other statutes
    sorted_sections = [existing_map[k] for k in sorted(existing_map.keys())]
    data["sections"] = sorted_sections
    data["total_sections_found"] = len(sorted_sections)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"   [+] Surgically recovered: {recovered}/{len(missing_nums)} -> Total now: {len(sorted_sections)}/{max_sec}")

if __name__ == "__main__":
    for t in TARGETS:
        patch_file(t)
