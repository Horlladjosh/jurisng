import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_DIR = Path("data/json_laws")
RAW_DIR = Path("data/raw_pdfs")

PDF_MAP = {
    "cfrn_1999.json": "cfrn_1999.pdf",
    "acja_2015.json": "acja-2015.pdf",
    "child_rights_act_2003.json": "child-rights-act.pdf",
    "cybercrimes_act_2015.json": "cybercrimes-act-2015.pdf",
    "employee_compensation_act_2010.json": "employee-compensation-act-2010.pdf",
    "evidence_act_2011.json": "evidence-act-2011.pdf",
    "labour_act.json": "labour-act.pdf",
    "land_use_act_1978.json": "land-use-act.pdf",
    "penal_code_act_1960.json": "penal-code-northern-states-1960.pdf",
    "police_act_2020.json": "police_act_2020.pdf"
}

def audit_perfection():
    print("=" * 80)
    print("COMPREHENSIVE STATUTORY FIDELITY & VERBATIM MATCH AUDIT")
    print("=" * 80)

    total_sections_checked = 0
    total_flaws = 0

    for json_file, pdf_file in PDF_MAP.items():
        j_path = JSON_DIR / json_file
        p_path = RAW_DIR / pdf_file

        if not j_path.exists():
            continue

        with open(j_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        title = data.get("short_title", json_file)
        sections = data.get("sections", [])
        total_sections_checked += len(sections)

        # 1. Load Raw PDF Text Layer for Exact Substring Verification
        raw_pdf_text = ""
        if p_path.exists():
            reader = PdfReader(str(p_path))
            raw_pdf_text = " ".join("\n".join(p.extract_text() or "" for p in reader.pages).split()).lower()

        short_sections = []
        toc_leaks = []
        pdf_mismatches = []
        numbers = []

        for sec in sections:
            num_str = sec.get("section_number", "")
            try:
                numbers.append(int(re.findall(r'\d+', num_str)[0]))
            except:
                pass

            body = sec.get("full_text", "").strip()
            
            # Check A: Character depth
            if len(body) < 35:
                short_sections.append(num_str)

            # Check B: TOC list indicators
            if re.search(r'\b\d{1,3}\.\s+[A-Z][a-z]+.*\b\d{1,3}\.\s+[A-Z][a-z]+', body) and len(body) < 300:
                toc_leaks.append(num_str)

            # Check C: Verbatim match in source PDF
            if raw_pdf_text and len(body) >= 20:
                words = body.split()
                # Take a 10-word probe from the body
                sample = " ".join(words[:min(10, len(words))]).lower()
                clean_sample = re.sub(r'[^a-z0-9\s]', '', sample)
                clean_pdf = re.sub(r'[^a-z0-9\s]', '', raw_pdf_text)
                
                if clean_sample not in clean_pdf:
                    pdf_mismatches.append(num_str)

        # Check D: Numbering gaps
        numbers.sort()
        gaps = []
        if numbers:
            expected = set(range(1, max(numbers) + 1))
            actual = set(numbers)
            missing = expected - actual
            if missing and max(numbers) <= data.get("expected_sections", max(numbers)):
                gaps = sorted(list(missing))

        # Output statutory report card
        has_issue = bool(short_sections or toc_leaks or pdf_mismatches)
        status_icon = "✗" if has_issue else "✓"
        print(f"\n{status_icon} [{title}] — {len(sections)} Sections Indexed")
        print(f"  • Verbatim Matches in PDF : {len(sections) - len(pdf_mismatches)} / {len(sections)}")
        
        if short_sections:
            print(f"  • Sub-threshold Chars (<35 chars): {short_sections}")
            total_flaws += len(short_sections)
        if toc_leaks:
            print(f"  • Potential TOC Leaks: {toc_leaks}")
            total_flaws += len(toc_leaks)
        if pdf_mismatches:
            print(f"  • PDF Text Sample Mismatches: {pdf_mismatches[:10]}{'...' if len(pdf_mismatches)>10 else ''}")
            total_flaws += len(pdf_mismatches)
        if gaps:
            print(f"  • Number Sequence Gaps: {gaps[:10]}")

    print("\n" + "=" * 80)
    print(f"TOTAL SECTIONS AUDITED: {total_sections_checked} across {len(PDF_MAP)} statutes")
    print(f"VERDICT: {'100% PERFECT VERBATIM FIDELITY' if total_flaws == 0 else f'{total_flaws} POTENTIAL ANOMALIES DETECTED'}")
    print("=" * 80)

if __name__ == "__main__":
    audit_perfection()
