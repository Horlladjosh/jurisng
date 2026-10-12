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
total_pages = len(doc)
print(f"[*] Extracting remaining pages (11 to {total_pages}) for {SHORT_TITLE}...")

parts = [
    {
        "text": (
            f"Extract all substantive legal sections from these final scanned pages of '{SHORT_TITLE}' (2011). "
            "Focus specifically on sections 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25."
        )
    }
]

for p_idx in range(10, total_pages):
    page = doc[p_idx]
    pix = page.get_pixmap(dpi=200)
    img_bytes = pix.tobytes("jpeg")
    b64_data = base64.b64encode(img_bytes).decode("utf-8")
    parts.append({
        "inline_data": {
            "mime_type": "image/jpeg",
            "data": b64_data
        }
    })

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
    "contents": [{"parts": parts}],
    "generationConfig": {
        "responseMimeType": "application/json",
        "responseSchema": schema,
        "temperature": 0.0
    }
}

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
headers = {"Content-Type": "application/json"}

res = requests.post(url, headers=headers, json=payload, timeout=120)
res_json = res.json()

if "candidates" not in res_json or not res_json["candidates"][0].get("content", {}).get("parts"):
    print("[!] Raw response error:", res_json)
    exit(1)

extracted_tail = json.loads(res_json["candidates"][0]["content"]["parts"][0]["text"]).get("sections", [])
print(f"[*] Extracted {len(extracted_tail)} sections from pages 11–{total_pages}.")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    statute_data = json.load(f)

sec_map = {int(s["section_number"]): s for s in statute_data.get("sections", []) if s["section_number"].isdigit()}

for s in extracted_tail:
    num_str = s["section_number"].strip().rstrip('.')
    if num_str.isdigit():
        num = int(num_str)
        s_num = str(num)
        s_title = s["section_title"].strip().rstrip('.')
        s_part = s.get("part", "PART II").strip()
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
        print(f"    [+] Integrated Section {num}: {s_title}")

sorted_secs = [sec_map[k] for k in sorted(sec_map.keys())]
statute_data["sections"] = sorted_secs
statute_data["total_sections"] = len(sorted_secs)

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(statute_data, f, indent=2, ensure_ascii=False)

print(f"\n[✓] Money Laundering Act now contains {len(sorted_secs)} complete sections.")
