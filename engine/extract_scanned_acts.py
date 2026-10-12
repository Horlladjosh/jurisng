import fitz
import Vision
import Quartz
import json
import os
import re

def ocr_pdf_pages(pdf_path):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)
    
    pages_lines = []
    for p_idx in range(total_pages):
        page = doc[p_idx]
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes('png')
        data = Quartz.CFDataCreate(None, img_bytes, len(img_bytes))
        provider = Quartz.CGDataProviderCreateWithCFData(data)
        cg_image = Quartz.CGImageCreateWithPNGDataProvider(provider, None, False, Quartz.kCGRenderingIntentDefault)
        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
        handler.performRequests_error_([request], None)
        results = request.results()
        
        # Sort observations top-to-bottom (using box origin y)
        # Note: in Vision coordinates, y=0 is bottom, y=1 is top
        obs_sorted = sorted(results, key=lambda o: -float(o.boundingBox().origin.y))
        lines = [o.topCandidates_(1)[0].string().strip() for o in obs_sorted if o.topCandidates_(1)[0].string().strip()]
        pages_lines.append(lines)
    return pages_lines


def extract_dev_commission_act(pdf_path, statute_id, title, short_title, year, gazette_no, enact_date, desc, out_file, total_expected):
    print(f"\n[*] Processing Scanned Act: {title} ({pdf_path})...")
    pages_lines = ocr_pdf_pages(pdf_path)
    
    # Flatten lines while noting page
    full_lines = []
    for p_idx, p_lines in enumerate(pages_lines):
        for l in p_lines:
            # Skip page headers / footers
            if re.search(r"^\d+$", l) or "COMMISSION (ESTABLISHMENT) ACT" in l.upper() and len(l) < 70:
                continue
            full_lines.append(l)

    # 1. Parse Arrangement of Sections (TOC)
    toc_titles = {}
    current_part = "Part I - Establishment of the Commission"
    
    for l in full_lines:
        part_m = re.match(r"^PART\s+([IVXLCDM\d]+)\s*[-—–]\s*(.*)$", l, re.IGNORECASE)
        if part_m:
            current_part = l
            continue
        m = re.match(r"^(\d{1,2})\.\s+(.*)$", l)
        if m:
            s_num = int(m.group(1))
            s_title = m.group(2).strip().rstrip(".")
            if s_num <= total_expected and s_num not in toc_titles:
                toc_titles[s_num] = (s_title, current_part)

    print(f"    TOC parsed: {len(toc_titles)} sections (expected {total_expected})")

    # 2. Extract Substantive Sections
    # Find commencement / Section 1 start
    sec_starts = []
    for idx, l in enumerate(full_lines):
        # Look for substantive section header
        m = re.match(r"^(\d{1,2})\.\s+(.*)$", l)
        m_bare = re.match(r"^(\d{1,2})\.\s*$", l)
        if m:
            s_num = int(m.group(1))
            rest = m.group(2).strip()
            sec_starts.append((s_num, rest, idx))
        elif m_bare:
            s_num = int(m_bare.group(1))
            next_l = full_lines[idx+1] if idx+1 < len(full_lines) else ""
            sec_starts.append((s_num, next_l, idx))

    # Find the substantive monotonic run from 1 to total_expected
    # Usually starts after the TOC (idx > 20)
    substantive_run = []
    for s_num, rest, idx in sec_starts:
        if idx < 15: # Skip TOC
            continue
        expected = 1 if not substantive_run else substantive_run[-1][0] + 1
        if s_num == expected:
            title = rest
            if not title and s_num in toc_titles:
                title = toc_titles[s_num][0]
            part = toc_titles.get(s_num, ("", "General Provisions"))[1]
            substantive_run.append((s_num, title, idx, part))
            if s_num == total_expected:
                break

    print(f"    Substantive run matched: {len(substantive_run)} sections (1 to {substantive_run[-1][0] if substantive_run else 0})")

    sections_json = []
    for i, (s_num, title, line_idx, part) in enumerate(substantive_run):
        body_start = line_idx + 1
        if i + 1 < len(substantive_run):
            body_end = substantive_run[i+1][2]
        else:
            body_end = len(full_lines)
            for j in range(body_start, len(full_lines)):
                if "EXPLANATORY MEMORANDUM" in full_lines[j].upper() or "SCHEDULE" in full_lines[j].upper():
                    body_end = j
                    break

        sec_body_lines = full_lines[body_start:body_end]
        body_text = "\n".join(sec_body_lines).strip()
        if not body_text:
            body_text = title

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.strip().rstrip("."),
            "part": part,
            "full_text": body_text,
            "searchable_chunk": f"{title} - Section {s_num}: {title}\n{part}\n{body_text}"
        })

    manifest = {
        "statute_id": statute_id,
        "title": title,
        "short_title": short_title,
        "year": year,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": gazette_no,
        "enactment_date": enact_date,
        "description": desc,
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = f"data/json_laws/{out_file}"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


def extract_trade_marks_act():
    pdf_path = "data/raw_pdfs/trade_marks_act.pdf"
    print(f"\n[*] Processing Scanned Act: Trade Marks Act 1967 ({pdf_path})...")
    pages_lines = ocr_pdf_pages(pdf_path)
    
    full_lines = []
    for p_idx, p_lines in enumerate(pages_lines):
        for l in p_lines:
            if re.search(r"^\d+$", l) or "TRADE MARKS ACT" in l.upper() and len(l) < 30:
                continue
            full_lines.append(l)

    # Trade Marks Act has 69 sections
    # Scan for section numbers 1 to 69
    sec_hits = []
    for i, l in enumerate(full_lines):
        m = re.match(r"^(\d{1,2})\.\s*(.*)$", l)
        if m:
            s_num = int(m.group(1))
            rest = m.group(2).strip()
            sec_hits.append((s_num, rest, i))

    # Find the substantive run
    substantive_run = []
    for s_num, rest, idx in sec_hits:
        if idx < 60: # Skip arrangement of sections
            continue
        expected = 1 if not substantive_run else substantive_run[-1][0] + 1
        if s_num == expected:
            title = rest
            if not title and idx + 1 < len(full_lines):
                title = full_lines[idx+1]
            substantive_run.append((s_num, title, idx))
            if s_num == 69:
                break

    print(f"    Substantive run matched: {len(substantive_run)} sections (1 to {substantive_run[-1][0] if substantive_run else 0})")

    part_map = {
        1: "Part I: The Register of Trade Marks",
        7: "Part II: Effect of Registration and the Action for Infringement",
        17: "Part III: Registrability and Validity of Registration",
        31: "Part IV: Assignment and Transmission",
        37: "Part V: Use and Non-Use",
        43: "Part VI: General and Miscellaneous Provisions"
    }
    current_part = "Part I: The Register of Trade Marks"

    sections_json = []
    for i, (s_num, title, line_idx) in enumerate(substantive_run):
        if s_num in part_map:
            current_part = part_map[s_num]

        body_start = line_idx + 1
        if i + 1 < len(substantive_run):
            body_end = substantive_run[i+1][2]
        else:
            body_end = len(full_lines)
            for j in range(body_start, len(full_lines)):
                if "SCHEDULE" in full_lines[j].upper():
                    body_end = j
                    break

        sec_body_lines = full_lines[body_start:body_end]
        body_text = "\n".join(sec_body_lines).strip()

        sections_json.append({
            "section_number": str(s_num),
            "section_title": title.strip().rstrip("."),
            "part": current_part,
            "full_text": body_text,
            "searchable_chunk": f"Trade Marks Act, 1967 - Section {s_num}: {title}\n{current_part}\n{body_text}"
        })

    manifest = {
        "statute_id": "trade_marks_act",
        "title": "Trade Marks Act, 1967",
        "short_title": "Trade Marks Act",
        "year": 1967,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Laws of the Federation of Nigeria, Cap. T13, LFN 2004 / Act No. 29 of 1965",
        "enactment_date": "1st June 1967",
        "description": "An Act to make provision relating to trade marks and for other matters connected therewith.",
        "total_sections": len(sections_json),
        "sections": sections_json
    }

    out_path = "data/json_laws/trade_marks_act.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Saved {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)


if __name__ == "__main__":
    t1 = extract_dev_commission_act(
        "data/raw_pdfs/north_central_dev_comm_act_2024.pdf",
        "north_central_dev_comm_act_2024",
        "North-Central Development Commission (Establishment) Act, 2024",
        "North-Central Dev Comm Act",
        2024,
        "Federal Republic of Nigeria Official Gazette / Act No. 64 of 2024",
        "28th November 2024",
        "An Act to establish the North-Central Development Commission charged with the responsibility among other things to receive and manage funds for the reconstruction, rehabilitation, and development of the North-Central States.",
        "north_central_dev_comm_act_2024.json",
        28
    )

    t2 = extract_dev_commission_act(
        "data/raw_pdfs/north_west_dev_comm_act_2025.pdf",
        "north_west_dev_comm_act_2025",
        "North-West Development Commission (Establishment) Act, 2025",
        "North-West Dev Comm Act",
        2025,
        "Federal Republic of Nigeria Official Gazette / Act No. 5 of 2025",
        "15th January 2025",
        "An Act to establish the North-West Development Commission charged with the responsibility for the reconstruction and rehabilitation of infrastructural damages and catalytic development of the North-West zone.",
        "north_west_dev_comm_act_2025.json",
        27
    )

    t3 = extract_dev_commission_act(
        "data/raw_pdfs/south_east_dev_comm_act_2025.pdf",
        "south_east_dev_comm_act_2025",
        "South-East Development Commission (Establishment) Act, 2025",
        "South-East Dev Comm Act",
        2025,
        "Federal Republic of Nigeria Official Gazette / Act No. 6 of 2025",
        "15th January 2025",
        "An Act to establish the South-East Development Commission charged with the responsibility for the reconstruction, rehabilitation, and infrastructural development of the South-East zone.",
        "south_east_dev_comm_act_2025.json",
        28
    )

    t4 = extract_trade_marks_act()

    print(f"\n=======================================================")
    print(f"COMPLETED SCANNED ACTS EXTRACTION: Total sections: {t1+t2+t3+t4}")
