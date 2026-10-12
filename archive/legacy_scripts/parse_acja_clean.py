import json
import re
from pathlib import Path
from pypdf import PdfReader

PDF_PATH = Path("data/raw_pdfs/acja-2015.pdf")
JSON_PATH = Path("data/json_laws/acja_2015.json")

print("=" * 80)
print("PARSING ACJA 2015 (SECTIONS 1 TO 494) WITH EXACT BOUNDARIES")
print("=" * 80)

reader = PdfReader(str(PDF_PATH))
# Start on substantive page 21 (index 20)
full_text = "\n".join(p.extract_text() or "" for p in reader.pages[20:])

# Strip Schedules and Explanatory Memorandum from end
for marker in ["FIRST SCHEDULE", "SECOND SCHEDULE", "SCHEDULES"]:
    if marker in full_text:
        full_text = full_text.split(marker)[0]

TOTAL_EXPECTED = 494
sections = []
current_text = full_text

for i in range(1, TOTAL_EXPECTED + 1):
    # Match section header 'N. (1)' or 'N. [Word]' at start of line
    pattern = rf'(?:\n|^)\s*{i}\.\s+(\([0-9a-zA-Z]+\)|[A-Z])'
    m = list(re.finditer(pattern, current_text))
    
    if not m:
        # Fallback if there's slightly looser spacing
        pattern_loose = rf'(?:\n|^)\s*{i}\.\s+'
        m = list(re.finditer(pattern_loose, current_text))
        
    if m:
        start_idx = m[0].start()
        
        # Look for start of next section N+1
        next_pat = rf'(?:\n|^)\s*{i+1}\.\s+(\([0-9a-zA-Z]+\)|[A-Z])'
        next_m = list(re.finditer(next_pat, current_text[start_idx + len(m[0].group(0)):]))
        
        if next_m:
            end_idx = start_idx + len(m[0].group(0)) + next_m[0].start()
            sec_text = current_text[start_idx:end_idx].strip()
        else:
            # Final section or boundary cap
            sec_text = current_text[start_idx:start_idx + 4000].strip()
            
        # Clean formatting
        cleaned = re.sub(r'[ \t]+', ' ', sec_text)
        cleaned = re.sub(r'\n+', '\n', cleaned).strip()
        
        sections.append({
            "section_number": str(i),
            "section_title": f"Section {i}",
            "full_text": cleaned,
            "searchable_chunk": f"ACJA 2015 | Section {i} | {cleaned}"
        })
        
        # Advance text window past this section
        current_text = current_text[start_idx + len(sec_text):]
    else:
        print(f"[!] Warning: Missed Section {i}")

# Write payload matching verified schema
payload = {
    "statute_id": "acja_2015",
    "statute_title": "Administration of Criminal Justice Act, 2015",
    "short_title": "ACJA 2015",
    "year": "2015",
    "total_sections_found": len(sections),
    "expected_sections": TOTAL_EXPECTED,
    "total_sections": len(sections),
    "sections": sections
}

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)

print(f"\n[✓] ACJA 2015 Parsing Complete: {len(sections)} / {TOTAL_EXPECTED} sections extracted cleanly.")

# Audit lengths of generated ACJA
anomalies = [s for s in sections if len(s['full_text']) > 5000 or len(s['full_text']) < 30]
print(f"Anomalous sections (>5,000 or <30 chars): {len(anomalies)}")
if anomalies:
    for a in anomalies[:5]:
        print(f"  • Section {a['section_number']}: {len(a['full_text']):,} chars")
print("=" * 80)
