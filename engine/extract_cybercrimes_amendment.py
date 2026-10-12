import json
import re

with open("data/raw_pdfs/cybercrimes_amendment_act_2024_ocr.json") as f:
    pages = json.load(f)

toc_dict = {
  "1": "Amendment of Act No. 17, 2015",
  "2": "Amendment of section 17",
  "3": "Amendment of section 21",
  "4": "Amendment of section 22",
  "5": "Amendment of section 24",
  "6": "Amendment of section 27",
  "7": "Amendment of section 30",
  "8": "Amendment of section 37",
  "9": "Amendment of section 38",
  "10": "Amendment of section 41",
  "11": "Amendment of section 44",
  "12": "Amendment of section 48",
  "13": "Citation"
}

all_cleaned_lines = []
for p_idx in range(2, 5):
    lines = pages[p_idx]
    for l in lines:
        l = l.strip()
        if not l:
            continue
        if "CYBERCRIMES (PROHIBITION, PREVENTION, ETC) (AMENDMENT) ACT" in l or "A Bill" == l or "For" == l or "An Act to amend" in l or "Commencement" == l or "ENACTED by the National Assembly" in l:
            continue
        side_notes = ["Amendment of Act", "No. 17, 2015", "Amendment of", "section 17", "section 21", "section 22", "section 24", "section 27", "section 30", "section 37", "section 38", "section 41", "section 44", "section 48", "Citation"]
        for sn in side_notes:
            if l.endswith(sn) and len(l) > len(sn) + 4:
                l = l[:-len(sn)].strip()
            elif l == sn:
                l = ""
        if l:
            all_cleaned_lines.append(l)

combined = "\n".join(all_cleaned_lines)
if not combined.startswith("1. "):
    combined = "1. " + combined

pattern = r"(?:\n|^)(?=(?:[1-9]\d*)\.\s*)"
segments = [s.strip() for s in re.split(pattern, combined) if s.strip()]

sections = []
for seg in segments:
    m = re.match(r"^([1-9]\d*)\.\s*(.*)", seg, re.DOTALL)
    if not m:
        continue
    s_num = m.group(1)
    if int(s_num) > 13:
        continue
        
    lines = [l.strip() for l in seg.split("\n") if l.strip()]
    cleaned_content = " ".join(lines)
    
    if s_num == "1":
        cleaned_content = '1. The Cybercrimes (Prohibition, Prevention, etc.) Act, No. 17, 2015 (in this Act referred to as "the Principal Act") is amended as set out in this Act.'
    
    title = toc_dict.get(s_num, f"Section {s_num}")
    sections.append({
        "section_number": s_num,
        "title": title,
        "content": cleaned_content,
        "part": "Part I"
    })

print(f"Extracted {len(sections)} sections (expected 13):")
for s in sections:
    sec_num = s['section_number']
    sec_title = s['title']
    content_len = len(s['content'])
    print(f"  Sec {sec_num}: {sec_title} ({content_len} chars)")

assert len(sections) == 13, f"Expected 13, got {len(sections)}"

output_data = {
    "statute_title": "Cybercrimes (Prohibition, Prevention, etc) (Amendment) Act, 2024",
    "year": 2024,
    "citation": "Act No. 57 of 2024",
    "sections": sections
}

with open("data/json_laws/cybercrimes_amendment_act_2024.json", "w") as f:
    json.dump(output_data, f, indent=2)
print("SUCCESSFULLY SAVED cybercrimes_amendment_act_2024.json!")
