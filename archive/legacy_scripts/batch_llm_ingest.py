import os
import json
import re
import time
import warnings
from pathlib import Path
import fitz
import requests

# Suppress urllib3 LibreSSL warning on macOS
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

def clean_whitespace(s: str) -> str:
    s = s.replace('\xa0', ' ').replace('\xad', '').replace('\r', '').replace('\t', ' ')
    return re.sub(r'[ \t]+', ' ', s).strip()

def extract_pdf_pages_text(pdf_path: Path, start_page: int = 0, max_pages: int = None) -> str:
    doc = fitz.open(str(pdf_path))
    end_page = len(doc) if max_pages is None else min(len(doc), start_page + max_pages)
    
    pages_text = []
    for p_idx in range(start_page, end_page):
        page_str = doc[p_idx].get_text("text")
        cleaned = clean_whitespace(page_str)
        pages_text.append(f"--- PAGE {p_idx + 1} ---\n{cleaned}")
    return "\n\n".join(pages_text)

def call_gemini_api(api_key: str, system_instruction: str, prompt: str, max_retries: int = 5) -> dict:
    model_name = "gemini-3.6-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
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
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_instruction}
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.0
        }
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            
            if response.status_code == 200:
                res_json = response.json()
                text_content = res_json["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
            
            # If rate limited (429) or transient server busy (503/500)
            if response.status_code in [429, 500, 503, 504]:
                wait_time = attempt * 4
                print(f"    [!] Server busy ({response.status_code}). Retrying in {wait_time}s (Attempt {attempt}/{max_retries})...")
                time.sleep(wait_time)
                continue
                
            raise RuntimeError(f"API Error ({response.status_code}): {response.text}")
            
        except requests.exceptions.RequestException as e:
            wait_time = attempt * 4
            print(f"    [!] Network error: {e}. Retrying in {wait_time}s (Attempt {attempt}/{max_retries})...")
            time.sleep(wait_time)
            
    raise RuntimeError(f"Failed to complete API call after {max_retries} attempts.")

def process_statute(api_key: str, pdf_path: str, statute_id: str, short_title: str, year: int):
    pdf_file = Path(pdf_path)
    output_path = Path(f"data/json_laws/{statute_id}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print(f"[*] Processing: {short_title}")
    print(f"[*] Input File: {pdf_file}")
    
    doc = fitz.open(str(pdf_file))
    total_pages = len(doc)
    print(f"[*] Total Pages: {total_pages}")

    chunk_size = 15
    all_sections = []
    
    system_instruction = """
You are an expert statutory law extraction engine specializing in Nigerian Federal Gazettes and Acts of the National Assembly.
Your task is to parse raw text into a strict structured JSON array of legal sections.

Rules:
1. Extract all numbered sections in the chunk.
2. Capture the authoritative marginal note or TOC description as `section_title`.
3. Keep exact verbatim statutory wording, subsections ((1), (2)), and paragraphs ((a), (b), (c)).
4. Strip running headers (e.g. 'A Bill For', gazette headers), page numbers, and soft hyphens.
5. If a section continues across page boundaries, merge the text seamlessly.
6. Exclude appendix schedules from the substantive sections array.
"""

    for start_p in range(0, total_pages, chunk_size):
        end_p = min(total_pages, start_p + chunk_size)
        print(f"[*] Parsing Pages {start_p + 1} to {end_p} with Gemini Flash...")
        
        batch_text = extract_pdf_pages_text(pdf_file, start_page=start_p, max_pages=(end_p - start_p))
        
        prompt = f"""
Parse the following pages from '{short_title}' ({year}).
Extract all sections that appear in this chunk into JSON.

Statute metadata:
- statute_id: {statute_id}
- short_title: {short_title}
- year: {year}

DOCUMENT TEXT:
{batch_text}
"""
        
        chunk_data = call_gemini_api(api_key, system_instruction, prompt)
        extracted = chunk_data.get("sections", [])
        all_sections.extend(extracted)
        print(f"    -> Extracted {len(extracted)} sections from chunk.")
        time.sleep(2)

    # Deduplicate and sort
    deduped = {}
    for sec in all_sections:
        num_str = sec["section_number"].strip().rstrip('.')
        if num_str.isdigit():
            num_int = int(num_str)
            if num_int not in deduped:
                deduped[num_int] = sec
            else:
                existing_text = deduped[num_int]["full_text"]
                if len(sec["full_text"]) > len(existing_text):
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
            "searchable_chunk": f"{short_title} | {s_part} | {s_num}. {s_title} | {s_body}"
        })

    final_payload = {
        "statute_id": statute_id,
        "short_title": short_title,
        "year": year,
        "jurisdiction": "Federal Republic of Nigeria",
        "total_sections": len(final_sections),
        "sections": final_sections
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print(f"[✓] Completed! Extracted {len(final_sections)} structured sections.")
    print(f"[✓] Saved to: {output_path}")
    print("=" * 80)
    return final_payload

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[!] ERROR: GEMINI_API_KEY environment variable is not set.")
        print("[!] Run: export GEMINI_API_KEY=\"your_key_here\"")
        exit(1)
        
    process_statute(
        api_key=api_key,
        pdf_path="data/raw_pdfs/cybercrimes-act-2015.pdf",
        statute_id="cybercrimes_act_2015",
        short_title="Cybercrimes (Prohibition, Prevention, etc.) Act, 2015",
        year=2015
    )
