import fitz
import re
import json

def clean_cita():
    doc = fitz.open('data/raw_pdfs/cita_tax_act.pdf')
    
    pages_text = []
    for p in range(3, 72): # Page 4 to Page 72
        t = doc[p].get_text('text')
        if p == 3: # Page 4
            idx = t.find('COMPANIES INCOME TAX ACT\nAn Act')
            if idx != -1:
                t = t[idx:]
        pages_text.append(t)
    
    full_text = '\n'.join(pages_text)
    full_text = full_text.replace('\xa0', ' ')
    
    # Remove running headers / footers
    full_text = re.sub(r'\[Issue\s*\d+\)', '', full_text)
    full_text = re.sub(r'C21\s*[-–—]\s*\d+', '', full_text)
    full_text = re.sub(r'(?:^|\n)\s*Companies\s+Income\s+Tax\s+Act\s*(?=\n)', '\n', full_text, flags=re.IGNORECASE)
    
    # 90 active statutory sections with their metadata
    sections_meta = [
        # Part 2: Imposition of tax and profits chargeable
        {"sec": "9", "part": "Part 2", "title": "Charge of tax"},
        {"sec": "10", "part": "Part 2", "title": "Identification of a company"},
        {"sec": "11", "part": "Part 2", "title": "Charge of tax on interest relating to foreign and agricultural loans and certain reliefs"},
        {"sec": "12", "part": "Part 2", "title": "Full disclosure of agreement to be made"},
        {"sec": "13", "part": "Part 2", "title": "Nigerian companies"},
        {"sec": "14", "part": "Part 2", "title": "Companies engaged in shipping or air transport"},
        {"sec": "15", "part": "Part 2", "title": "Cable undertakings"},
        {"sec": "16", "part": "Part 2", "title": "Insurance companies"},
        {"sec": "17", "part": "Part 2", "title": "Authorised unit trust scheme"},
        {"sec": "18", "part": "Part 2", "title": "Profits of a company from certain dividends"},
        {"sec": "19", "part": "Part 2", "title": "Payment of dividend by a Nigerian company"},
        {"sec": "20", "part": "Part 2", "title": "Nigerian dividends received by companies other than Nigerian companies"},
        {"sec": "21", "part": "Part 2", "title": "Certain undistributed profits may be treated as distributed"},
        {"sec": "22", "part": "Part 2", "title": "Artificial transactions, etc."},
        {"sec": "23", "part": "Part 2", "title": "Profits exempted"},
        
        # Part 3: Ascertainment of profits
        {"sec": "24", "part": "Part 3", "title": "Deductions allowed"},
        {"sec": "25", "part": "Part 3", "title": "Deductible donations"},
        {"sec": "25A", "part": "Part 3", "title": "Deduction for donation to university and tertiary or research institutions"},
        {"sec": "26", "part": "Part 3", "title": "Deduction for research and development"},
        {"sec": "27", "part": "Part 3", "title": "Deductions not allowed"},
        {"sec": "28", "part": "Part 3", "title": "Waivers or refund of liability or expenses"},
        
        # Part 4: Ascertainment of assessable profits
        {"sec": "29", "part": "Part 4", "title": "Basis for computing assessable profits"},
        {"sec": "30", "part": "Part 4", "title": "Board's power to assess and charge on turn-over of trade or business"},
        
        # Part 5: Ascertainment of total profits
        {"sec": "31", "part": "Part 5", "title": "Total profits from all sources"},
        {"sec": "32", "part": "Part 5", "title": "Reconstruction investment allowance"},
        {"sec": "33", "part": "Part 5", "title": "Payment of minimum tax"},
        {"sec": "34", "part": "Part 5", "title": "Rural investment allowance"},
        {"sec": "35", "part": "Part 5", "title": "Export processing zone allowance"},
        {"sec": "36", "part": "Part 5", "title": "Mining of solid minerals"},
        {"sec": "37", "part": "Part 5", "title": "Incomes in convertible currencies to be exempt"},
        
        # Part 6: Incentives to gas industry
        {"sec": "39", "part": "Part 6", "title": "Gas utilisation (downstream operations)"},
        
        # Part 7: Rate of tax, deduction of tax from dividends and relief from double taxation
        {"sec": "40", "part": "Part 7", "title": "Rates of tax"},
        {"sec": "41", "part": "Part 7", "title": "Replacement of obsolete plant and machinery"},
        {"sec": "43", "part": "Part 7", "title": "Dividends and tax on interim dividends paid by Nigerian companies"},
        {"sec": "44", "part": "Part 7", "title": "Relief in respect of Commonwealth income tax"},
        {"sec": "45", "part": "Part 7", "title": "Double taxation arrangements"},
        {"sec": "46", "part": "Part 7", "title": "Method of calculating relief to be allowed for double taxation"},
        
        # Part 8: Persons chargeable, agents, liquidators, etc.
        {"sec": "47", "part": "Part 8", "title": "Chargeability to tax"},
        {"sec": "48", "part": "Part 8", "title": "Manager, etc., to be answerable"},
        {"sec": "49", "part": "Part 8", "title": "Power to appoint agent"},
        {"sec": "50", "part": "Part 8", "title": "Indemnification of manager, etc., or agent"},
        {"sec": "51", "part": "Part 8", "title": "Company wound up"},
        {"sec": "52", "part": "Part 8", "title": "Liability to file return"},
        {"sec": "53", "part": "Part 8", "title": "Self-assessment of tax payable"},
        {"sec": "54", "part": "Part 8", "title": "Currency of assessment"},
        
        # Part 9: Returns
        {"sec": "55", "part": "Part 9", "title": "Returns and provisional accounts"},
        {"sec": "57", "part": "Part 9", "title": "Filing of returns by companies operating in the capital market"},
        {"sec": "58", "part": "Part 9", "title": "Board may call for further returns"},
        {"sec": "59", "part": "Part 9", "title": "Extension of period of making returns"},
        {"sec": "60", "part": "Part 9", "title": "Call for returns, books, documents and information"},
        {"sec": "61", "part": "Part 9", "title": "Information to be delivered by bankers"},
        {"sec": "62", "part": "Part 9", "title": "Return deemed to be furnished by due authority"},
        {"sec": "63", "part": "Part 9", "title": "Books of account"},
        {"sec": "64", "part": "Part 9", "title": "Power to enter and search premises"},
        
        # Part 10: Assessments
        {"sec": "65", "part": "Part 10", "title": "Board to make assessments"},
        {"sec": "66", "part": "Part 10", "title": "Additional assessments"},
        {"sec": "67", "part": "Part 10", "title": "Lists of companies assessed"},
        {"sec": "68", "part": "Part 10", "title": "Service of notice of assessment"},
        {"sec": "69", "part": "Part 10", "title": "Revision of assessment in case of objection"},
        {"sec": "70", "part": "Part 10", "title": "Errors and defects in assessment and notice"},
        
        # Part 11: Appeals
        {"sec": "76", "part": "Part 11", "title": "Assessments to be final and conclusive"},
        
        # Part 12: Collection, recovery and repayment of tax
        {"sec": "77", "part": "Part 12", "title": "Time within which tax (including provisional tax) is to be paid"},
        {"sec": "78", "part": "Part 12", "title": "Deduction of tax from interest, etc."},
        {"sec": "79", "part": "Part 12", "title": "Deduction of tax on rent"},
        {"sec": "80", "part": "Part 12", "title": "Deduction of tax from dividend"},
        {"sec": "81", "part": "Part 12", "title": "Deduction of tax at source"},
        {"sec": "82", "part": "Part 12", "title": "Penalty for failure to deduct tax"},
        {"sec": "83", "part": "Part 12", "title": "Accountant-General of the Federation to deduct tax"},
        {"sec": "84", "part": "Part 12", "title": "Payment of tax deducted"},
        {"sec": "85", "part": "Part 12", "title": "Addition for non-payment of tax and enforcement of payment"},
        {"sec": "86", "part": "Part 12", "title": "Power to distrain for non-payment of tax"},
        {"sec": "87", "part": "Part 12", "title": "Action for tax by Board and refusal of clearance where tax is in default"},
        {"sec": "88", "part": "Part 12", "title": "Attendance of director, etc., at proceedings, etc."},
        {"sec": "89", "part": "Part 12", "title": "Remission of tax"},
        {"sec": "90", "part": "Part 12", "title": "Relief in respect of error or mistake"},
        {"sec": "91", "part": "Part 12", "title": "Repayment of tax"},
        
        # Part 13: Offences and penalties
        {"sec": "92", "part": "Part 13", "title": "Penalty for offences"},
        {"sec": "94", "part": "Part 13", "title": "False statements and returns"},
        {"sec": "95", "part": "Part 13", "title": "Penalties for offences by authorised and unauthorised persons"},
        {"sec": "96", "part": "Part 13", "title": "Tax to be payable notwithstanding proceedings for penalties"},
        {"sec": "97", "part": "Part 13", "title": "Prosecution to be with the sanction of the Board"},
        {"sec": "98", "part": "Part 13", "title": "Savings for criminal proceedings"},
        {"sec": "99", "part": "Part 13", "title": "Place of an offence"},
        
        # Part 14: Miscellaneous
        {"sec": "100", "part": "Part 14", "title": "Power to alter rate of tax, etc."},
        {"sec": "101", "part": "Part 14", "title": "Tax clearance certificate"},
        {"sec": "102", "part": "Part 14", "title": "Conduct of proceedings"},
        {"sec": "103", "part": "Part 14", "title": "Power to pay reward"},
        {"sec": "104", "part": "Part 14", "title": "Repeals, transitional provisions, etc."},
        {"sec": "105", "part": "Part 14", "title": "Interpretation"},
        {"sec": "106", "part": "Part 14", "title": "Short title and application"}
    ]
    
    # Locate positions
    positions = []
    for item in sections_meta:
        s = item["sec"]
        if s == "13":
            pats = [r'ϭϯ͘[^\n]*', r'(?:^|\n)\s*13\.\s*']
        elif s == "25A":
            pats = [r'(?:^|\n)\s*25A\.\s*']
        elif s == "31":
            pats = [r'(?:^|\n)\s*(?:3\s*1|31)\.\s*']
        else:
            pats = [rf'(?:^|\n)\s*{s}\.\s*']
        
        found = None
        for pat in pats:
            m = list(re.finditer(pat, full_text))
            if m:
                prev_pos = positions[-1][1] if positions else 0
                for match in m:
                    if match.start() >= prev_pos:
                        found = match
                        break
            if found:
                break
        if not found:
            raise Exception(f"Section {s} not found!")
        positions.append((s, found.start(), found.end()))
    
    schedules_idx = full_text.find('SCHEDULES', positions[-1][1])
    if schedules_idx == -1:
        schedules_idx = len(full_text)
    
    parsed_sections = []
    statute_name = "Companies Income Tax Act"
    
    for i in range(len(positions)):
        sec_num, s_start, s_end = positions[i]
        meta = sections_meta[i]
        
        if i + 1 < len(positions):
            next_start = positions[i+1][1]
            raw_chunk = full_text[s_start:next_start]
        else:
            raw_chunk = full_text[s_start:schedules_idx]
        
        chunk = raw_chunk.strip()
        
        # 1. Remove leading section heading line(s)
        lines = chunk.split('\n')
        first_line = lines[0].strip()
        if re.match(rf'^(?:{sec_num}\.|ϭϯ͘|3\s*1\.)', first_line):
            lines = lines[1:]
        
        body_text = '\n'.join(lines).strip()
        
        # 2. Strip trailing editorial notes, PART headers, repealed sections, and schedules
        patterns_to_strip_from_tail = [
            r'\[EDITORIAL\s+NOTE:[\s\S]*?\Z',
            r'PART\s+III\s*\n\s*Ascertainment\s+of\s+profits[\s\S]*?\Z',
            r'PART\s+IV\s*\n\s*Ascertainment\s+of\s+assessable\s+profits[\s\S]*?\Z',
            r'PART\s+V\s*\n\s*Ascertainment\s+of\s+total\s+profits[\s\S]*?\Z',
            r'38\.\s*\.{3,}[\s\S]*?\Z',
            r'PART\s+VI\s*\n\s*Incentives\s+to\s+(?:the\s+)?gas\s+industry[\s\S]*?\Z',
            r'42\.\s*\(\s*Deleted\s+by[^\)]*\)[\s\S]*?\Z',
            r'42\.\s*\.{3,}[\s\S]*?\Z',
            r'PART\s+VII\s*\n\s*Rate\s+of\s+tax[^\n]*[\s\S]*?\Z',
            r'PART\s+VIII\s*\n\s*Persons\s+chargeable[^\n]*[\s\S]*?\Z',
            r'PART\s+IX\s*\n\s*Returns[\s\S]*?\Z',
            r'56\.\s*\([^\)]*Deleted[^\)]*\)[\s\S]*?\Z',
            r'PART\s+X\s*\n\s*Assessments[\s\S]*?\Z',
            r'PART\s+XI\s*\n\s*Appeals[\s\S]*?\Z',
            r'71\s+to\s+75[^\n]*[\s\S]*?\Z',
            r'PART\s+XII\s*\n\s*Collection,\s*recovery\s+and\s+repayment\s+of\s+tax[\s\S]*?\Z',
            r'PART\s+XIII\s*\n\s*Offences\s+and\s+penalties[\s\S]*?\Z',
            r'93\.\s*\([^\)]*Deleted[^\)]*\)[\s\S]*?\Z',
            r'93\.\s*\.{3,}[\s\S]*?\Z',
            r'PART\s+XIV\s*\n\s*Miscellaneous[\s\S]*?\Z',
            r'SCHEDULES\s*\n\s*FIRST\s+SCHEDULE[\s\S]*?\Z'
        ]
        
        for pat in patterns_to_strip_from_tail:
            body_text = re.sub(pat, '', body_text, flags=re.IGNORECASE).strip()
        
        body_text = re.sub(r'\n{3,}', '\n\n', body_text)
        
        # Build standard schema
        searchable_chunk = f"{statute_name} Sec {sec_num}: {meta['title']}\n{body_text}"
        
        sec_obj = {
            "section_number": sec_num,
            "section_title": meta["title"],
            "title": meta["title"],
            "part": meta["part"],
            "full_text": body_text,
            "text": body_text,
            "searchable_chunk": searchable_chunk
        }
        parsed_sections.append(sec_obj)
        
    cita_json = {
        "title": statute_name,
        "short_title": statute_name,
        "jurisdiction": "Federal",
        "statute_type": "Act",
        "year": 1977,
        "sections": parsed_sections
    }
    
    with open('data/json_laws/companies_income_tax_act.json', 'w') as f:
        json.dump(cita_json, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully wrote {len(parsed_sections)} sections to companies_income_tax_act.json with unified schema.")

if __name__ == '__main__':
    clean_cita()
