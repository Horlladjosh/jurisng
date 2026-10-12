import os
import json
import re
import fitz
import requests

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("[!] GEMINI_API_KEY not set.")
    exit(1)

PATCH_TARGETS = [
    {
        "pdf_name": "evidence-act-2011.pdf",
        "json_name": "evidence_act_2011.json",
        "short_title": "Evidence Act, 2011",
        "missing_sections": ["132", "133", "134", "135", "136", "137"]
    },
    {
        "pdf_name": "fccpa-2018.pdf",
        "json_name": "fccpa_2018.json",
        "short_title": "Federal Competition and Consumer Protection Act, 2018",
        "missing_sections": ["86", "110", "111"]
    }
]

def call_gemini(prompt: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    schema = {
        "type": "OBJECT",
        "properties": {
            "sections": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "section_number": {"type": "STRING"},
                        "section_title": {"type": "STRING"},
                        "part": {"type": "STRING"},
                        "full_text": {"type": "STRING"}
                    },
                    "required": ["section_number", "section_title", "part", "full_text"]
                }
            }
        },
        "required": ["sections"]
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.0
        }
    }
    res = requests.post(url, headers=headers, json=payload, timeout=60)
    return res.json()

for target in PATCH_TARGETS:
    pdf_path = f"data/raw_pdfs/{target['pdf_name']}"
    json_path = f"data/json_laws/{target['json_name']}"
    
    print(f"[*] Patching gaps for {target['short_title']}...")
    doc = fitz.open(pdf_path)
    full_pdf_text = "\n".join([page.get_text("text") for page in doc])
    
    prompt = f"""
Extract ONLY the following exact missing sections from '{target['short_title']}':
Missing section numbers: {target['missing_sections']}

DOCUMENT TEXT:
{full_pdf_text}
"""
    res = call_gemini(prompt)
    raw_content = res["candidates"][0]["content"]["parts"][0]["text"]
    extracted = json.loads(raw_content).get("sections", [])
    
    with open(json_path, "r", encoding="utf-8") as f:
        statute_data = json.load(f)
        
    sec_map = {int(s["section_number"]): s for s in statute_data["sections"] if s["section_number"].isdigit()}
    
    for s in extracted:
        num_str = s["section_number"].strip().rstrip('.')
        if num_str.isdigit():
            num = int(num_str)
            s_num = str(num)
            s_title = s["section_title"].strip().rstrip('.')
            s_part = s.get("part", "PART I").strip()
            s_body = s["full_text"].strip()
            if not re.match(rf'^{s_num}\b', s_body):
                s_body = f"{s_num}. {s_body}"
            sec_map[num] = {
                "section_number": s_num,
                "section_title": s_title,
                "part": s_part,
                "full_text": s_body,
                "searchable_chunk": f"{target['short_title']} | {s_part} | {s_num}. {s_title} | {s_body}"
            }
            print(f"    [+] Patched Section {num}: {s_title}")
            
    sorted_secs = [sec_map[k] for k in sorted(sec_map.keys())]
    statute_data["sections"] = sorted_secs
    statute_data["total_sections"] = len(sorted_secs)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(statute_data, f, indent=2, ensure_ascii=False)
        
    print(f"[✓] {target['short_title']} now has {len(sorted_secs)} total sections.")
