import json
import re
from pathlib import Path
from pypdf import PdfReader

RAW_DIR = Path("data/raw_pdfs")
JSON_DIR = Path("data/json_laws")

def robust_parse_pdf(pdf_filename, json_filename, short_title, title, start_page, max_sections):
    pdf_path = RAW_DIR / pdf_filename
    if not pdf_path.exists():
        print(f"[!] PDF not found: {pdf_filename}")
        return

    reader = PdfReader(str(pdf_path))
    full_text = "\n".join(p.extract_text() or "" for p in reader.pages[start_page - 1:])

    sections = []
    
    for i in range(1, max_sections + 1):
        # Build patterns to find Section N and Section N+1
        # Pattern for current section start
        curr_patterns = [
            rf'\n\s*{i}\.\s+[A-Z]',
            rf'\n\s*Section\s+{i}\.?\s*',
            rf'\n\s*{i}\s+[\-\–\—]\s*',
        ]
        
        start_pos = -1
        for pat in curr_patterns:
            m = re.search(pat, full_text)
            if m:
                start_pos = m.start()
                break
                
        if start_pos == -1:
            # Fallback search without newline requirement
            m = re.search(rf'\b{i}\.\s+[A-Z][a-z]', full_text)
            if m:
                start_pos = m.start()

        if start_pos == -1:
            continue

        # Find next section start to bound the text
        next_pos = len(full_text)
        for j in range(i + 1, min(i + 15, max_sections + 1)):
            next_patterns = [
                rf'\n\s*{j}\.\s+[A-Z]',
                rf'\n\s*Section\s+{j}\.?\s*',
                rf'\n\s*{j}\s+[\-\–\—]\s*',
            ]
            for pat in next_patterns:
                nm = re.search(pat, full_text[start_pos + 3:])
                if nm:
                    next_pos = start_pos + 3 + nm.start()
                    break
            if next_pos < len(full_text):
                break

        section_raw = full_text[start_pos:next_pos].strip()
        
        # Clean up text
        cleaned = re.sub(r'\s+', ' ', section_raw)
        if cleaned and cleaned[-1].isalnum():
            cleaned += "."

        sections.append({
            "section_number": str(i),
            "section_title": f"Section {i}",
            "full_text": cleaned,
            "searchable_chunk": f"{short_title} | Section {i} | {cleaned}"
        })
        
        # Advance full_text window to avoid matching previous numbers
        full_text = full_text[next_pos - len(section_raw):]

    out_path = JSON_DIR / json_filename
    payload = {
        "statute_title": title,
        "short_title": short_title,
        "jurisdiction": "Nigeria",
        "total_sections": len(sections),
        "sections": sections
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"[✓] Robustly parsed {short_title}: {len(sections)} sections extracted.")

# Re-run key statutes with robust bounds
robust_parse_pdf("fccpa-2018.pdf", "fccpa_2018.json", "FCCPA 2018", "Federal Competition and Consumer Protection Act, 2018", 10, 168)
robust_parse_pdf("labour-act.pdf", "labour_act.json", "Labour Act", "Labour Act (Chapter L1, LFN 2004)", 4, 92)
robust_parse_pdf("child-rights-act.pdf", "child_rights_act_2003.json", "Child's Rights Act 2003", "Child's Rights Act, 2003", 12, 278)
robust_parse_pdf("penal-code-act.pdf", "penal_code_act_1960.json", "Penal Code Act", "Penal Code Act", 5, 478)
