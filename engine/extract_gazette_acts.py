import fitz, re, json, os

def normalize_sec_start(line):
    line = re.sub(r"^(?:IO|I0|1O)[\x27\•\.\—\-\:\)\,\s]+", "10. ", line)
    line = re.sub(r"^(?:ll|1l|l1|II|1I|I1)[\x27\•\.\—\-\:\)\,\s]+", "11. ", line)
    line = re.sub(r"^l(\d)[\x27\•\.\—\-\:\)\,\s]+", r"1\1. ", line)
    line = re.sub(r"^(\d{1,3})[\x27\•\.\—\-\:\)\,\s]+", r"\1. ", line)
    return line

def parse_toc(doc, toc_start, toc_end):
    toc_text = "\n".join([doc[p].get_text() for p in range(toc_start - 1, toc_end)])
    
    toc_sections = {}
    part_map = {}
    current_part = "General Provisions"
    
    # Normalize lines
    raw_lines = [l.strip() for l in toc_text.splitlines() if l.strip()]
    i = 0
    while i < len(raw_lines):
        l = raw_lines[i]
        
        # Match Part / Chapter header
        pm = re.match(r"^(?:PART|CHAPTER)\s+([IVXLCDM0-9]+)\s*[\—\-\–\:]\s*(.*)$", l, re.I)
        if pm:
            current_part = f"Part {pm.group(1)} — {pm.group(2).strip().title()}"
            i += 1
            continue
            
        l_norm = normalize_sec_start(l)
        # Match Section entry: either "1. Title" or "1." on line i and "Title" on line i+1
        sm1 = re.match(r"^(\d{1,3})\.\s+(.*)$", l_norm)
        sm2 = re.match(r"^(\d{1,3})\.$", l_norm)
        
        if sm1:
            s_no = int(sm1.group(1))
            s_t = sm1.group(2).strip()
            # look ahead for continuation
            while i + 1 < len(raw_lines) and not re.match(r"^(\d{1,3}\.?|PART\s+[IVXLCDM0-9]+|CHAPTER\s+[IVXLCDM0-9]+|SCHEDULE|FIRST|SECOND|THIRD)", normalize_sec_start(raw_lines[i+1]), re.I):
                s_t += " " + raw_lines[i+1].strip()
                i += 1
            s_t = re.sub(r"\s+", " ", s_t).rstrip(".")
            toc_sections[s_no] = s_t
            part_map[s_no] = current_part
        elif sm2 and i + 1 < len(raw_lines):
            s_no = int(sm2.group(1))
            i += 1
            s_t = raw_lines[i].strip()
            while i + 1 < len(raw_lines) and not re.match(r"^(\d{1,3}\.?|PART\s+[IVXLCDM0-9]+|CHAPTER\s+[IVXLCDM0-9]+|SCHEDULE|FIRST|SECOND|THIRD)", normalize_sec_start(raw_lines[i+1]), re.I):
                s_t += " " + raw_lines[i+1].strip()
                i += 1
            s_t = re.sub(r"\s+", " ", s_t).rstrip(".")
            toc_sections[s_no] = s_t
            part_map[s_no] = current_part
            
        i += 1
        
    return toc_sections, part_map

def extract_body_lines(doc, body_start, body_end, margin_side_notes=True):
    substantive_lines = []
    for p in range(body_start - 1, min(body_end, len(doc))):
        page = doc[p]
        pnum = p + 1
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0]))
        for b in blocks:
            x0, y0, x1, y1, text, bno, btype = b
            text = text.strip()
            if not text:
                continue
            if margin_side_notes:
                # Header / footer filter for standard Gazettes
                if y1 < 145 or y0 > 740:
                    continue
                # Margin filter on odd pages
                if pnum % 2 == 1 and x0 >= 435:
                    continue
                # Margin filter on even pages (if isolated margin note block)
                if pnum % 2 == 0 and x1 <= 160:
                    continue
            for line in text.splitlines():
                l = line.strip()
                if l and not l.startswith("A Bill") and not l.startswith("For") and not "EXPLANATORY MEMORANDUM" in l and not "DEVELOPMENT COMMISSION (ESTABLISHMENT)" in l:
                    substantive_lines.append((pnum, l))
    return substantive_lines

def locate_sections(substantive_lines, toc_sections):
    sec_starts = {}
    for idx, (pnum, line) in enumerate(substantive_lines):
        l_norm = normalize_sec_start(line)
        m = re.match(r"^(\d{1,3})\.\s+(.*)$", l_norm)
        if m:
            s_no = int(m.group(1))
            if s_no in toc_sections:
                if not sec_starts and s_no == 1:
                    sec_starts[s_no] = idx
                elif sec_starts and s_no == max(sec_starts.keys()) + 1:
                    sec_starts[s_no] = idx
    return sec_starts

def generate_statute_json(config):
    pdf_path = config["pdf_path"]
    doc = fitz.open(pdf_path)
    
    margin_side_notes = config.get("margin_side_notes", True)
    toc_sections, part_map = parse_toc(doc, config["toc_start"], config["toc_end"])
    substantive_lines = extract_body_lines(doc, config["body_start"], config["body_end"], margin_side_notes=margin_side_notes)
    sec_starts = locate_sections(substantive_lines, toc_sections)
    
    print(f"\n=======================================================")
    print(f"[*] Processing: {config['statute']}")
    print(f"    • TOC Sections: {len(toc_sections)}")
    print(f"    • Body Starts Found: {len(sec_starts)}")
    
    missing = [s for s in toc_sections.keys() if s not in sec_starts]
    if missing:
        print(f"    [!] WARNING: Missing starts for sections: {missing}")
        
    sorted_sec = sorted(sec_starts.keys())
    sections_json = []
    
    for i, s_no in enumerate(sorted_sec):
        start_idx = sec_starts[s_no]
        end_idx = sec_starts[sorted_sec[i+1]] if i + 1 < len(sorted_sec) else len(substantive_lines)
        
        sec_lines = [substantive_lines[j][1] for j in range(start_idx, end_idx)]
        raw_body = "\n".join(sec_lines).strip()
        
        # Clean section number prefix
        body_clean = re.sub(r"^\d{1,3}\s*[\.\—\-]+\s*", "", raw_body).strip()
        sec_title = toc_sections[s_no]
        part_name = part_map.get(s_no, "General Provisions")
        
        sections_json.append({
            "section_number": str(s_no),
            "section_title": sec_title,
            "part": part_name,
            "full_text": body_clean,
            "searchable_chunk": f"{config['statute']} - Section {s_no}: {sec_title}\n{part_name}\n{body_clean}"
        })
        
    statute_id = re.sub(r"[^a-zA-Z0-9]+", "_", config["statute"].lower()).strip("_")
    manifest = {
        "statute_id": statute_id,
        "title": config["statute"],
        "short_title": config["short_title"],
        "year": config["year"],
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": config["gazette_number"],
        "enactment_date": config["enactment_date"],
        "description": config["description"],
        "total_sections": len(sections_json),
        "sections": sections_json
    }
    
    out_path = f"data/json_laws/{config['output_filename']}"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"    [✓] Generated {out_path} ({len(sections_json)} verified sections)")
    return len(sections_json)

GAZETTE_CONFIGS = [
    {
        "pdf_path": "data/raw_pdfs/startup_act_2022.pdf",
        "statute": "Nigeria Startup Act, 2022",
        "short_title": "Nigeria Startup Act",
        "year": 2022,
        "gazette_number": "Federal Republic of Nigeria Official Gazette No. 188, Vol. 109, Act No. 32 of 2022",
        "enactment_date": "19th October 2022",
        "description": "An Act to establish the National Council for Digital Innovation and Entrepreneurship, provide for the creation and development of an enabling environment for technology-enabled startups in Nigeria, and for related matters.",
        "toc_start": 3,
        "toc_end": 4,
        "body_start": 5,
        "body_end": 24,
        "output_filename": "nigeria_startup_act_2022.json"
    },
    {
        "pdf_path": "data/raw_pdfs/civil_aviation_act_2022.pdf",
        "statute": "Civil Aviation Act, 2022",
        "short_title": "Civil Aviation Act",
        "year": 2022,
        "gazette_number": "Federal Republic of Nigeria Official Gazette No. 153, Vol. 109, Act No. 30 of 2022",
        "enactment_date": "16th August 2022",
        "description": "An Act to repeal the Civil Aviation Act, No. 6, 2006 and enact the Civil Aviation Act, 2022 for the regulation of civil aviation in Nigeria, and for related matters.",
        "toc_start": 3,
        "toc_end": 6,
        "body_start": 7,
        "body_end": 85,
        "output_filename": "civil_aviation_act_2022.json"
    },
    {
        "pdf_path": "data/raw_pdfs/arcon_act_2022.pdf",
        "statute": "Advertising Regulatory Council of Nigeria Act, 2022",
        "short_title": "ARCON Act",
        "year": 2022,
        "gazette_number": "Federal Republic of Nigeria Official Gazette No. 120, Vol. 109, Act No. 23 of 2022",
        "enactment_date": "14th July 2022",
        "description": "An Act to repeal the Advertising Practitioners (Registration, etc.) Act, Cap. A7, Laws of the Federation of Nigeria, 2004 and enact the Advertising Regulatory Council of Nigeria Act, 2022.",
        "toc_start": 3,
        "toc_end": 5,
        "body_start": 6,
        "body_end": 48,
        "output_filename": "arcon_act_2022.json"
    },
    {
        "pdf_path": "data/raw_pdfs/pharmacy_council_act_2022.pdf",
        "statute": "Pharmacy Council of Nigeria (Establishment) Act, 2022",
        "short_title": "Pharmacy Council Act",
        "year": 2022,
        "gazette_number": "Federal Republic of Nigeria Official Gazette No. 157, Vol. 109, Act No. 24 of 2022",
        "enactment_date": "16th August 2022",
        "description": "An Act to repeal the Pharmacists Council of Nigeria Act, Cap. P17, Laws of the Federation of Nigeria, 2004 and enact the Pharmacy Council of Nigeria (Establishment) Act, 2022.",
        "toc_start": 3,
        "toc_end": 5,
        "body_start": 6,
        "body_end": 44,
        "output_filename": "pharmacy_council_act_2022.json"
    },
    {
        "pdf_path": "data/raw_pdfs/meteorological_agency_act_2022.pdf",
        "statute": "Nigerian Meteorological Agency (Establishment) Act, 2022",
        "short_title": "NIMET Act",
        "year": 2022,
        "gazette_number": "Federal Republic of Nigeria Official Gazette No. 184, Vol. 109, Act No. 29 of 2022",
        "enactment_date": "16th August 2022",
        "description": "An Act to repeal the Nigerian Meteorological Agency (Establishment, etc.) Act, No. 9, 2003 and enact the Nigerian Meteorological Agency (Establishment) Act, 2022.",
        "toc_start": 3,
        "toc_end": 4,
        "body_start": 5,
        "body_end": 29,
        "output_filename": "meteorological_agency_act_2022.json"
    },
    {
        "pdf_path": "data/raw_pdfs/raw_materials_council_act_2022.pdf",
        "statute": "Raw Materials Research and Development Council Act, 2022",
        "short_title": "RMRDC Act",
        "year": 2022,
        "gazette_number": "Federal Republic of Nigeria Official Gazette No. 183, Vol. 109, Act No. 26 of 2022",
        "enactment_date": "16th August 2022",
        "description": "An Act to repeal the Raw Materials Research and Development Council Act, Cap. R3, Laws of the Federation of Nigeria, 2004 and enact the Raw Materials Research and Development Council Act, 2022.",
        "toc_start": 3,
        "toc_end": 3,
        "body_start": 4,
        "body_end": 14,
        "output_filename": "raw_materials_council_act_2022.json"
    },
    {
        "pdf_path": "data/raw_pdfs/management_dev_council_act_2022.pdf",
        "statute": "Nigerian Council for Management Development Act, 2022",
        "short_title": "NCMD Act",
        "year": 2022,
        "gazette_number": "Federal Republic of Nigeria Official Gazette No. 182, Vol. 109, Act No. 24 of 2022",
        "enactment_date": "16th August 2022",
        "description": "An Act to repeal the Nigerian Council for Management Development Act, Cap. N99, Laws of the Federation of Nigeria, 2004 and enact the Nigerian Council for Management Development Act, 2022.",
        "toc_start": 3,
        "toc_end": 4,
        "body_start": 5,
        "body_end": 17,
        "output_filename": "management_dev_council_act_2022.json"
    },
    {
        "pdf_path": "data/raw_pdfs/social_work_practitioners_act_2022.pdf",
        "statute": "Chartered Institute of Social Work Practitioners (Establishment) Act, 2022",
        "short_title": "Social Work Practitioners Act",
        "year": 2022,
        "gazette_number": "Federal Republic of Nigeria Official Gazette No. 181, Vol. 109, Act No. 25 of 2022",
        "enactment_date": "16th August 2022",
        "description": "An Act to establish the Chartered Institute of Social Work Practitioners charged with the responsibility for determining the standard of knowledge and skill to be attained by persons seeking to become members of the institute.",
        "toc_start": 3,
        "toc_end": 4,
        "body_start": 5,
        "body_end": 24,
        "output_filename": "social_work_practitioners_act_2022.json"
    },
    {
        "pdf_path": "data/raw_pdfs/south_west_dev_comm_act_2025.pdf",
        "statute": "South-West Development Commission (Establishment) Act, 2025",
        "short_title": "South-West Development Commission Act",
        "year": 2025,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act of 2025",
        "enactment_date": "2025",
        "description": "An Act to establish the South-West Development Commission charged with the responsibility of receiving and managing funds from allocation of the Federation Account and other sources for the development and reconstruction of the South-West zone.",
        "toc_start": 2,
        "toc_end": 3,
        "body_start": 4,
        "body_end": 15,
        "margin_side_notes": False,
        "output_filename": "south_west_dev_comm_act_2025.json"
    },
    {
        "pdf_path": "data/raw_pdfs/south_south_dev_comm_act_2025.pdf",
        "statute": "South-South Development Commission (Establishment) Act, 2025",
        "short_title": "South-South Development Commission Act",
        "year": 2025,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act of 2025",
        "enactment_date": "2025",
        "description": "An Act to establish the South-South Development Commission charged with the responsibility to receive and manage funds from the Federation Account allocation and other sources for the socio-economic development of the South-South zone.",
        "toc_start": 2,
        "toc_end": 3,
        "body_start": 4,
        "body_end": 15,
        "margin_side_notes": False,
        "output_filename": "south_south_dev_comm_act_2025.json"
    }
]

if __name__ == "__main__":
    total = 0
    for cfg in GAZETTE_CONFIGS:
        total += generate_statute_json(cfg)
    print(f"\n=======================================================")
    print(f"COMPLETED EXTRACTION: Generated {len(GAZETTE_CONFIGS)} Acts with {total} certified sections!")

