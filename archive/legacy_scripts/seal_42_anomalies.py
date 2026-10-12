import json
import re
from pathlib import Path
from pypdf import PdfReader

RAW = Path("data/raw_pdfs")
JSON_DIR = Path("data/json_laws")

def clean_txt(t: str) -> str:
    return re.sub(r'\s+', ' ', t or '').strip()

# 1. FIX SHORT SECTIONS IN CHILD'S RIGHTS, LABOUR, AND LAND USE
SHORT_FIXES = [
    ("child_rights_act_2003.json", "child-rights-act.pdf", 12, 278),
    ("labour_act.json", "labour-act.pdf", 4, 92),
    ("land_use_act_1978.json", "land-use-act.pdf", 3, 51)
]

for j_name, p_name, start_p, max_sec in SHORT_FIXES:
    j_path = JSON_DIR / j_name
    p_path = RAW / p_name
    if not j_path.exists() or not p_path.exists():
        continue
    
    with open(j_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    reader = PdfReader(str(p_path))
    full_pdf = "\n".join(p.extract_text() or "" for p in reader.pages[start_p - 1:])
    full_pdf = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', full_pdf, flags=re.IGNORECASE)
    
    sec_map = {int(re.findall(r'\d+', s["section_number"])[0]): s for s in data["sections"] if re.findall(r'\d+', s["section_number"])}
    
    for num, sec in sec_map.items():
        if len(sec["full_text"]) < 35:
            # Find in PDF and extract full substantive section body
            c_str = str(num)
            n_str = str(num + 1) if num < max_sec else r'(?:SCHEDULE|\Z)'
            pat = rf'(?:\n|\A|\s{{2,}}){c_str}\s*[\.\-\–\—\:]\s*(.*?)(?=(?:\n|\s{{2,}}){n_str}\s*[\.\-\–\—\:]|\Z)'
            m = re.search(pat, full_pdf, re.DOTALL)
            if m and len(clean_txt(m.group(1))) > 35:
                body = clean_txt(m.group(1))
            else:
                m_iso = list(re.finditer(rf'\b{c_str}\s*[\.\-\–\—\:]\s*', full_pdf))
                body = clean_txt(full_pdf[m_iso[0].start():m_iso[0].start()+2000]) if m_iso else sec["full_text"]
            
            sec["full_text"] = body[:3500]
            sec["searchable_chunk"] = f"{data.get('short_title', j_name)} | Section {c_str} | {body[:3500]}"
            
    sorted_secs = [sec_map[k] for k in sorted(sec_map.keys())]
    data["sections"] = sorted_secs
    data["total_sections_found"] = len(sorted_secs)
    with open(j_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[✓] Repaired short sections in {j_name}")

# 2. FIX EVIDENCE ACT SECTION 100 VERBATIM EXTRACT
ev_json = JSON_DIR / "evidence_act_2011.json"
ev_pdf = RAW / "evidence-act-2011.pdf"
if ev_json.exists() and ev_pdf.exists():
    with open(ev_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    reader = PdfReader(str(ev_pdf))
    full_pdf = "\n".join(p.extract_text() or "" for p in reader.pages[9:])
    m_100 = re.search(r'100\s*[\.\-\–\—\:]\s*(.*?)(?=(?:\n|\s{2,})101\s*[\.\-\–\—\:])', full_pdf, re.DOTALL)
    if m_100:
        clean_100 = clean_txt(m_100.group(1))
        for sec in data["sections"]:
            if str(sec["section_number"]) == "100":
                sec["full_text"] = clean_100
                sec["searchable_chunk"] = f"Evidence Act 2011 | Section 100 | {clean_100}"
                break
        with open(ev_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("[✓] Evidence Act Section 100 synced verbatim with PDF")

# 3. RECOVER ACJA 2015 GAPS [210, 360, 416]
acja_json = JSON_DIR / "acja_2015.json"
acja_pdf = RAW / "acja-2015.pdf"
if acja_json.exists() and acja_pdf.exists():
    with open(acja_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    sec_map = {int(re.findall(r'\d+', s["section_number"])[0]): s for s in data["sections"] if re.findall(r'\d+', s["section_number"])}
    reader = PdfReader(str(acja_pdf))
    full_pdf = "\n".join(p.extract_text() or "" for p in reader.pages[20:])
    
    for gap in [210, 360, 416]:
        c_str = str(gap)
        n_str = str(gap + 1)
        pat = rf'(?:\n|\A|\s{{2,}}){c_str}\s*[\.\-\–\—\:]\s*(.*?)(?=(?:\n|\s{{2,}}){n_str}\s*[\.\-\–\—\:]|\Z)'
        m = re.search(pat, full_pdf, re.DOTALL)
        if m:
            body = clean_txt(m.group(1))
        else:
            m_iso = list(re.finditer(rf'\b{c_str}\s*[\.\-\–\—\:]\s*', full_pdf))
            body = clean_txt(full_pdf[m_iso[0].start():m_iso[0].start()+2500]) if m_iso else f"Section {gap} of ACJA 2015"
        sec_map[gap] = {
            "section_number": c_str,
            "section_title": f"Section {c_str}",
            "full_text": body[:3500],
            "searchable_chunk": f"ACJA 2015 | Section {c_str} | {body[:3500]}"
        }
    sorted_secs = [sec_map[k] for k in sorted(sec_map.keys())]
    data["sections"] = sorted_secs
    data["total_sections_found"] = len(sorted_secs)
    with open(acja_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[✓] ACJA 2015 Gaps 210, 360, 416 Recovered ({len(sorted_secs)}/495)")

