import json
import re
from pathlib import Path
from pypdf import PdfReader

JSON_DIR = Path("data/json_laws")
RAW_DIR = Path("data/raw_pdfs")

# 1. Fix CFRN 1999 Section 143
cfrn_path = JSON_DIR / "cfrn_1999.json"
if cfrn_path.exists():
    with open(cfrn_path, "r", encoding="utf-8") as f:
        cfrn_data = json.load(f)
    
    CFRN_143 = (
        "143. (1) The President or Vice-President may be removed from office in accordance with the provisions of this section. "
        "(2) Whenever a notice of any allegation in writing signed by not less than one-third of the members of the National Assembly— "
        "(a) is presented to the President of the Senate; (b) stating that the holder of the office of President or Vice-President "
        "is guilty of gross misconduct in the performance of the functions of his office, detailed particulars of which shall be specified, "
        "the President of the Senate shall within seven days of the receipt of the notice cause a copy thereof to be served on the holder "
        "of the office and on each member of the National Assembly, and shall also cause any statement made in reply to the allegation "
        "by the holder of the office to be served on each member of the National Assembly. "
        "(3) Within fourteen days of the presentation of the notice to the President of the Senate (whether or not any statement was "
        "made by the holder of the office in reply to the allegation contained in the notice) each House of the National Assembly shall "
        "resolve by motion without any debate whether or not the allegation shall be investigated. "
        "(4) A motion of the National Assembly that the allegation be investigated shall not be declared as having been passed, unless "
        "it is supported by the votes of not less than two-thirds majority of all the members of each House of the National Assembly. "
        "(5) Within seven days of the passing of a motion under the foregoing provisions, the Chief Justice of Nigeria shall at the "
        "request of the President of the Senate appoint a Panel of seven persons who in his opinion are of unquestionable integrity, "
        "not being members of any public service, legislative house or political party, to investigate the allegation as provided in this section. "
        "(6) The holder of an office whose conduct is being investigated under this section shall have the right to defend himself in "
        "person and be represented before the Panel by legal practitioners of his own choice. "
        "(7) A Panel appointed under this section shall— (a) have such powers and exercise its functions in accordance with such procedure "
        "as may be prescribed by the National Assembly; and (b) within three months of its appointment report its findings to each House "
        "of the National Assembly. "
        "(8) Where the Panel reports to each House of the National Assembly that the allegation has not been proved, no further "
        "proceedings shall be taken under this section in respect of the matter. "
        "(9) Where the report of the Panel is that the allegation against the holder of the office has been proved, then within fourteen "
        "days of the receipt of the report at the House the National Assembly shall consider the report, and if by a resolution of each "
        "House of the National Assembly supported by not less than two-thirds majority of all its members, the report of the Panel is "
        "adopted, then the holder of the office shall stand removed from office as from the date of the adoption of the report. "
        "(10) No proceedings or determination of the Panel or of the National Assembly or any matter relating thereto shall be "
        "entertained or questioned in any court. "
        "(11) In this section 'gross misconduct' means a grave violation or breach of the provisions of this Constitution or a "
        "misconduct of such nature as amounts in the opinion of the National Assembly to gross misconduct."
    )
    
    for sec in cfrn_data.get("sections", []):
        if str(sec.get("section_number")) == "143":
            sec["full_text"] = CFRN_143
            sec["searchable_chunk"] = f"CFRN 1999 | Section 143 | {CFRN_143}"
            break
            
    with open(cfrn_path, "w", encoding="utf-8") as f:
        json.dump(cfrn_data, f, indent=2, ensure_ascii=False)
    print("[✓] Patched CFRN 1999 Section 143.")

# 2. Fix Penal Code Act stubs by parsing with correct PDF filename
penal_json = JSON_DIR / "penal_code_act_1960.json"
penal_pdf = RAW_DIR / "penal-code-act.pdf"

if penal_json.exists() and penal_pdf.exists():
    with open(penal_json, "r", encoding="utf-8") as f:
        penal_data = json.load(f)
        
    reader = PdfReader(str(penal_pdf))
    full_pdf_text = "\n".join(p.extract_text() or "" for p in reader.pages[4:])
    
    for sec in penal_data.get("sections", []):
        num = str(sec.get("section_number"))
        txt = sec.get("full_text", "").strip()
        if len(txt) < 45:
            pat = rf'(?:\n|\b){num}\.\s+([A-Z][a-zA-Z\s,\-\(\)]+)(.*?)(?=(?:\n|\b)\d+\.\s+[A-Z]|\Z)'
            m = re.search(pat, full_pdf_text, re.DOTALL)
            if m:
                heading = m.group(1).strip()
                body = m.group(2).strip()
                reconstructed = f"{num}. {heading} {body}"
                cleaned = re.sub(r'\s+', ' ', reconstructed).strip()
                if cleaned and cleaned[-1].isalnum():
                    cleaned += "."
                sec["full_text"] = cleaned
                sec["searchable_chunk"] = f"Penal Code Act | Section {num} | {cleaned}"

    with open(penal_json, "w", encoding="utf-8") as f:
        json.dump(penal_data, f, indent=2, ensure_ascii=False)
    print("[✓] Patched Penal Code Act stub sections.")

