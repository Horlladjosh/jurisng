import os
import json
import re
import time
import warnings
from pathlib import Path
import fitz
import requests

warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

STATUTE_REGISTRY = [
    {
        "pdf_name": "cybercrimes-act-2015.pdf",
        "statute_id": "cybercrimes_act_2015",
        "short_title": "Cybercrimes (Prohibition, Prevention, etc.) Act, 2015",
        "year": 2015
    },
    {
        "pdf_name": "land-use-act.pdf",
        "statute_id": "land_use_act_1978",
        "short_title": "Land Use Act, 1978",
        "year": 1978
    },
    {
        "pdf_name": "penal-code-northern-states-1960.pdf",
        "statute_id": "penal_code_1960",
        "short_title": "Penal Code (Northern States) Federal Provisions Act, 1960",
        "year": 1960
    },
    {
        "pdf_name": "national-health-act-2014.pdf",
        "statute_id": "national_health_act_2014",
        "short_title": "National Health Act, 2014",
        "year": 2014
    },
    {
        "pdf_name": "employee-compensation-act-2010.pdf",
        "statute_id": "employee_compensation_act_2010",
        "short_title": "Employees' Compensation Act, 2010",
        "year": 2010
    },
    {
        "pdf_name": "police_act_2020.pdf",
        "statute_id": "police_act_2020",
        "short_title": "Nigeria Police Act, 2020",
        "year": 2020
    },
    {
        "pdf_name": "evidence-act-2011.pdf",
        "statute_id": "evidence_act_2011",
        "short_title": "Evidence Act, 2011",
        "year": 2011
    },
    {
        "pdf_name": "labour-act.pdf",
        "statute_id": "labour_act_1971",
        "short_title": "Labour Act, 1971",
        "year": 1971
    },
    {
        "pdf_name": "fccpa-2018.pdf",
        "statute_id": "fccpa_2018",
        "short_title": "Federal Competition and Consumer Protection Act, 2018",
        "year": 2018
    },
    {
        "pdf_name": "cfrn_1999.pdf",
        "statute_id": "cfrn_1999",
        "short_title": "Constitution of the Federal Republic of Nigeria, 1999 (as amended)",
        "year": 1999
    },
    {
        "pdf_name": "child-rights-act.pdf",
        "statute_id": "child_rights_act_2003",
        "short_title": "Child's Rights Act, 2003",
        "year": 2003
    },
    {
        "pdf_name": "acja-2015.pdf",
        "statute_id": "acja_2015",
        "short_title": "Administration of Criminal Justice Act, 2015",
        "year": 2015
    }
]

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
    model_name = "gemini-3.5-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
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
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.0
        }
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                res_json = response.json()
                text_content = res_json["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
            
            if response.status_code == 429:
                # Full 60-second bucket rollover for rate limits
                wait_time = 60
                print(f"    [!] Rate limited (429). Cooling down for {wait_time}s to reset quota (Attempt {attempt}/{max_retries})...")
                time.sleep(wait_time)
                continue
                
            if response.status_code in [500, 503, 504]:
                wait_time = attempt * 8
                print(f"    [!] Server busy ({response.status_code}). Retrying in {wait_time}s (Attempt {attempt}/{max_retries})...")
                time.sleep(wait_time)
                continue
                
            raise RuntimeError(f"API Error ({response.status_code}): {response.text}")
            
        except requests.exceptions.RequestException as e:
            wait_time = attempt * 8
            print(f"    [!] Network hiccup: {e}. Retrying in {wait_time}s (Attempt {attempt}/{max_retries})...")
            time.sleep(wait_time)
            
    raise RuntimeError(f"Failed API call after {max_retries} attempts.")

def process_statute(api_key: str, pdf_path: str, statute_id: str, short_title: str, year: int):
    pdf_file = Path(pdf_path)
    output_path = Path(f"data/json_laws/{statute_id}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.exists() and output_path.stat().st_size > 500:
        print(f"[→] Skipping {short_title} (already ingested in {output_path.name})")
        return
    
    print("\n" + "=" * 80)
    print(f"[*] Starting Ingestion: {short_title}")
    print(f"[*] File: {pdf_file.name}")
    
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
        print(f"[*] Parsing Pages {start_p + 1} to {end_p} / {total_pages}...")
        
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
        # Pacing between chunks to stay safely below RPM thresholds
        time.sleep(4)

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

    print(f"[✓] Saved {len(final_sections)} sections to {output_path.name}")

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[!] ERROR: GEMINI_API_KEY environment variable is not set.")
        exit(1)
        
    raw_dir = Path("data/raw_pdfs")
    print(f"[*] Starting Batch Processing of Registry ({len(STATUTE_REGISTRY)} statutes)...")

    for entry in STATUTE_REGISTRY:
        pdf_path = raw_dir / entry["pdf_name"]
        if pdf_path.exists():
            process_statute(
                api_key=api_key,
                pdf_path=str(pdf_path),
                statute_id=entry["statute_id"],
                short_title=entry["short_title"],
                year=entry["year"]
            )
        else:
            print(f"[!] File not found: {pdf_path}")
            
    print("\n" + "=" * 80)
    print("[✓] ALL DIGITAL STATUTES PROCESSED SUCCESSFULLY!")
    print("=" * 80)
