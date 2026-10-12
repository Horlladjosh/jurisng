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

def locate_phrase(needle: str, haystack: str) -> int:
    words = needle.split()[:8]
    if not words:
        return -1
    pattern = r'\s+'.join(re.escape(w) for w in words)
    m = re.search(pattern, haystack, re.IGNORECASE)
    return m.start() if m else -1

def patch_by_interpolation(target):
    json_path = JSON_DIR / target["json"]
    pdf_path = RAW_DIR / target["pdf"]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_map = {}
    for sec in data.get("sections", []):
        try:
            num = int(re.findall(r'\d+', sec["section_number"])[0])
            existing_map[num] = sec
        except:
            pass

    max_sec = target["max_sec"]
    missing_nums = sorted([i for i in range(1, max_sec + 1) if i not in existing_map])

    if not missing_nums:
        print(f"[✓] {target['title']}: Already 100% complete ({max_sec}/{max_sec}).")
        return

    # Extract raw substantive PDF text
    reader = PdfReader(str(pdf_path))
    pages = [p.extract_text() or "" for p in reader.pages[target["start_page"] - 1:]]
    pdf_body = "\n".join(pages)
    pdf_body = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', pdf_body, flags=re.IGNORECASE)
    pdf_body = re.sub(r'Page\s+\d+\s+of\s+\d+', '', pdf_body, flags=re.IGNORECASE)

    # Map positions of all existing sections in raw text
    positions = {}
    for num, sec in existing_map.items():
        pos = locate_phrase(sec["full_text"], pdf_body)
        if pos != -1:
            positions[num] = pos

    recovered = 0

    for num in missing_nums:
        # Find nearest preceding and succeeding anchor
        prev_nums = [n for n in positions.keys() if n < num]
        next_nums = [n for n in positions.keys() if n > num]

        prev_pos = positions[max(prev_nums)] if prev_nums else 0
        next_pos = positions[min(next_nums)] if next_nums else len(pdf_body)

        # The missing section is inside this window
        window = pdf_body[prev_pos:next_pos]

        # Find the number inside the bounded window
        m = re.search(rf'\b{num}\b[^\n\.\—\-]*[\.\—\-\:]?\s*(.*)', window, re.DOTALL)
        if m:
            body = clean_txt(m.group(1))
        else:
            # Fallback to entire bounded window
            body = clean_txt(window)

        if len(body) > 15:
            existing_map[num] = {
                "section_number": str(num),
                "section_title": f"Section {num}",
                "full_text": body[:4000],
                "searchable_chunk": f"{target['title']} | Section {num} | {body[:4000]}"
            }
            recovered += 1

    # Save without modifying existing sections
    sorted_sections = [existing_map[k] for k in sorted(existing_map.keys())]
    data["sections"] = sorted_sections
    data["total_sections_found"] = len(sorted_sections)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n>> {target['title']}")
    print(f"   Recovered: {recovered}/{len(missing_nums)} missing sections.")
    print(f"   Final Count: {len(sorted_sections)} / {max_sec} ({(len(sorted_sections)/max_sec)*100:.1f}%)")

if __name__ == "__main__":
    for t in TARGETS:
        patch_by_interpolation(t)
