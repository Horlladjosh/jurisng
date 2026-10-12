import json
from pathlib import Path
from pypdf import PdfReader

JSON_PATH = Path("data/json_laws/acja_2015.json")
PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

sections_map = {s["section_number"]: s["full_text"] for s in data.get("sections", [])}

def check_section(sec_num):
    print("=" * 80)
    print(f"VERIFYING SECTION {sec_num}")
    print("=" * 80)
    
    # 1. Extracted JSON text
    json_text = sections_map.get(str(sec_num), "NOT FOUND IN JSON")
    print(f"[JSON Extraction] Length: {len(json_text):,} chars")
    print("--- JSON TEXT START ---")
    print(json_text)
    print("--- JSON TEXT END ---\n")

# Check Section 1, Section 250, and Section 494
check_section("1")
check_section("250")
check_section("494")
