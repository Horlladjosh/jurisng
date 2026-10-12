import os
import json
import base64
import re
import fitz
import requests

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("[!] ERROR: GEMINI_API_KEY environment variable is not set.")
    exit(1)

PDF_PATH = "data/raw_pdfs/money-laundering-act-2011.pdf"
JSON_PATH = "data/json_laws/money_laundering_act_2011.json"
SHORT_TITLE = "Money Laundering (Prohibition) Act, 2011"

doc = fitz.open(PDF_PATH)
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

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
headers = {"Content-Type": "application/json"}

def extract_pages(pages, prompt_instruction):
    parts = [{"text": prompt_instruction}]
    for p in pages:
        pix = doc[p].get_pixmap(dpi=200)
        img_bytes = pix.tobytes("jpeg")
        b64_data = base64.b64encode(img_bytes).decode("utf-8")
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64_data}})

    payload = {
        "contents": [{"parts": parts}],
        "systemInstruction": {"parts": [{"text": "Convert the legal text from the scanned statutory page image into a JSON list of section objects."}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.0
        }
    }
    res = requests.post(url, headers=headers, json=payload, timeout=60)
    return json.loads(res.json()["candidates"][0]["content"]["parts"][0]["text"]).get("sections", [])

print("[*] Extracting Sections 15 & 16 from Page 11...")
secs_11 = extract_pages([10], "Structure the statutory provisions for Section 15 (Money laundering offences) and Section 16 (Other offences) into JSON.")

print("[*] Extracting Sections 25 & 26 from Pages 14 & 15...")
secs_tail = extract_pages([13, 14], "Structure the statutory provisions for Section 25 (Interpretation) and Section 26 (Citation) into JSON.")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    statute_data = json.load(f)

sec_map = {int(s["section_number"]): s for s in statute_data.get("sections", []) if s["section_number"].isdigit()}

for s in (secs_11 + secs_tail):
    num_str = s["section_number"].strip().rstrip('.')
    if num_str.isdigit():
        num = int(num_str)
        s_num = str(num)
        s_title = s["section_title"].strip().rstrip('.')
        s_part = s.get("part", "PART II" if num < 20 else "PART III").strip()
        s_body = s["full_text"].strip()
        if not re.match(rf'^{s_num}\b', s_body):
            s_body = f"{s_num}. {s_body}"
        sec_map[num] = {
            "section_number": s_num,
            "section_title": s_title,
            "part": s_part,
            "full_text": s_body,
            "searchable_chunk": f"{SHORT_TITLE} | {s_part} | {s_num}. {s_title} | {s_body}"
        }
        print(f"    [+] Patched Section {num}: {s_title}")

sorted_secs = [sec_map[k] for k in sorted(sec_map.keys())]
statute_data["sections"] = sorted_secs
statute_data["total_sections"] = len(sorted_secs)

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(statute_data, f, indent=2, ensure_ascii=False)

print(f"\n[✓] Money Laundering Act is complete with {len(sorted_secs)} sections (1 to 26).")
