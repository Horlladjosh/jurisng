import os
import json
import base64
import re
import time
import warnings
from pathlib import Path
import fitz
import requests

warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("[!] ERROR: GEMINI_API_KEY environment variable is not set.")
    exit(1)

PDF_PATH = "data/raw_pdfs/money-laundering-act-2011.pdf"
OUTPUT_PATH = "data/json_laws/money_laundering_act_2011.json"
SHORT_TITLE = "Money Laundering (Prohibition) Act, 2011"
STATUTE_ID = "money_laundering_act_2011"
YEAR = 2011

doc = fitz.open(PDF_PATH)
total_pages = len(doc)
print(f"[*] Starting Multimodal OCR Ingestion for {SHORT_TITLE}")
print(f"[*] Total Scanned Pages: {total_pages}")

schema = {
    "type": "OBJECT",
    "properties": {
        "statute_id": {"type": "STRING"},
        "short_title": {"type": "STRING"},
        "year": {"type": "INTEGER"},
        "jurisdiction": {"type": "STRING"},
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
    "required": ["statute_id", "short_title", "year", "sections"]
}

system_instruction = """
You are an expert statutory law extraction and OCR engine specializing in scanned Nigerian Federal Gazettes and Acts.
Your task is to parse images of scanned statutory pages into a strict structured JSON array of legal sections.

Rules:
1. Perform high-accuracy verbatim OCR extraction on all text.
2. Extract all numbered sections present in the scanned page batch.
3. Capture the authoritative marginal note or section header as `section_title`.
4. Keep exact verbatim statutory wording, subsections ((1), (2)), and paragraphs ((a), (b), (c)).
5. Strip running headers, gazette page headers, stamp marks, and page numbers.
6. If a section spans across page boundaries, merge the text seamlessly.
7. Exclude appendix schedules from substantive sections.
"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
headers = {"Content-Type": "application/json"}

chunk_size = 5
all_sections = []

for start_p in range(0, total_pages, chunk_size):
    end_p = min(total_pages, start_p + chunk_size)
    print(f"[*] OCR Processing Scanned Pages {start_p + 1} to {end_p} / {total_pages}...")

    parts = [
        {
            "text": f"Extract all legal sections from these scanned pages of '{SHORT_TITLE}' ({YEAR}) into JSON format."
        }
    ]

    for p_idx in range(start_p, end_p):
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

    payload = {
        "contents": [{"parts": parts}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.0
        }
    }

    for attempt in range(1, 4):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=120)
            if res.status_code == 200:
                chunk_data = json.loads(res.json()["candidates"][0]["content"]["parts"][0]["text"])
                extracted = chunk_data.get("sections", [])
                all_sections.extend(extracted)
                print(f"    -> Extracted {len(extracted)} sections from chunk.")
                break
            elif res.status_code == 429:
                print(f"    [!] Quota pause (429). Waiting 30s...")
                time.sleep(30)
            else:
                print(f"    [!] API status {res.status_code}: {res.text}. Retrying in 5s...")
                time.sleep(5)
        except Exception as e:
            print(f"    [!] Request error: {e}. Retrying in 5s...")
            time.sleep(5)

    time.sleep(3)

# Deduplicate and sort sections
deduped = {}
for sec in all_sections:
    num_str = sec["section_number"].strip().rstrip('.')
    if num_str.isdigit():
        num_int = int(num_str)
        if num_int not in deduped or len(sec["full_text"]) > len(deduped[num_int]["full_text"]):
            deduped[num_int] = sec

sorted_sec_nums = sorted(deduped.keys())
final_sections = []

for num in sorted_sec_nums:
    s = deduped[num]
    s_num = str(num)
    s_title = s["section_title"].strip().rstrip('.')
    s_part = s.get("part", "PART I").strip()
    s_body = s["full_text"].strip()
    if not re.match(rf'^{s_num}\b', s_body):
        s_body = f"{s_num}. {s_body}"
    final_sections.append({
        "section_number": s_num,
        "section_title": s_title,
        "part": s_part,
        "full_text": s_body,
        "searchable_chunk": f"{SHORT_TITLE} | {s_part} | {s_num}. {s_title} | {s_body}"
    })

final_payload = {
    "statute_id": STATUTE_ID,
    "short_title": SHORT_TITLE,
    "year": YEAR,
    "jurisdiction": "Federal Republic of Nigeria",
    "total_sections": len(final_sections),
    "sections": final_sections
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(final_payload, f, indent=2, ensure_ascii=False)

print(f"\n[✓] Successfully ingested {len(final_sections)} sections into {OUTPUT_PATH}")
