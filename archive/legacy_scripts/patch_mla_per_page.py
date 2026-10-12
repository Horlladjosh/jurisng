import os
import json
import base64
import re
import time
from pathlib import Path
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
print(f"[*] Extracting remaining pages (11 to {total_pages}) for {SHORT_TITLE} page-by-page...")

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

system_instruction = (
    "You are a legislative data structuring engine. Convert the legal text in the provided statutory page image into a JSON list of section objects. "
    "Maintain subsection markers ((1), (2), (a), (b)) and marginal notes as section_title."
)

all_tail_sections = []
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
headers = {"Content-Type": "application/json"}

for p_idx in range(10, total_pages):
    print(f"[*] Processing Scanned Page {p_idx + 1} / {total_pages}...")
    page = doc[p_idx]
    pix = page.get_pixmap(dpi=200)
    img_bytes = pix.tobytes("jpeg")
    b64_data = base64.b64encode(img_bytes).decode("utf-8")

    payload = {
        "contents": [{
            "parts": [
                {"text": f"Extract all numbered legal sections appearing on page {p_idx + 1} of Money Laundering (Prohibition) Act 2011 into JSON."},
                {"inline_data": {"mime_type": "image/jpeg", "data": b64_data}}
            ]
        }],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.0
        }
    }

    for attempt in range(1, 4):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=60)
            res_json = res.json()
            if res.status_code == 200 and "candidates" in res_json:
                candidate = res_json["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    chunk_text = candidate["content"]["parts"][0]["text"]
                    secs = json.loads(chunk_text).get("sections", [])
                    print(f"    -> Extracted {len(secs)} section(s) from page {p_idx + 1}")
                    all_tail_sections.extend(secs)
                    break
                elif candidate.get("finishReason") == "RECITATION":
                    print(f"    [!] Recitation block on page {p_idx + 1}. Moving to fallback phrasing...")
            time.sleep(3)
        except Exception as e:
            print(f"    [!] Error: {e}. Retrying in 4s...")
            time.sleep(4)

    time.sleep(2)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    statute_data = json.load(f)

sec_map = {int(s["section_number"]): s for s in statute_data.get("sections", []) if s["section_number"].isdigit()}

for s in all_tail_sections:
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
        print(f"    [+] Saved Section {num}: {s_title}")

sorted_secs = [sec_map[k] for k in sorted(sec_map.keys())]
statute_data["sections"] = sorted_secs
statute_data["total_sections"] = len(sorted_secs)

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(statute_data, f, indent=2, ensure_ascii=False)

print(f"\n[✓] Successfully finalized {SHORT_TITLE} with {len(sorted_secs)} total sections.")
