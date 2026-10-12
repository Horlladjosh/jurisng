import json
import re
from pathlib import Path

JSON_PATH = Path("data/json_laws/evidence_act_2011.json")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

def deep_clean_evidence(text: str) -> str:
    if not text:
        return ""
    
    # 1. Gazette & margin header cleanup
    text = re.sub(r'Federal Republic of Nigeria Official Gazette.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Adnussibilu[^\.\(]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'dfKII1J1clll', 'document', text)
    text = re.sub(r'Jr~a~OlI\s+and\s+nvasonub!c\s+ulfcncc-,\s+l-vidcncc\s+Oil\s+charge\s+nt\'?', '', text)
    text = re.sub(r'Co-defendant\s+not\s+all\s+accomplice\s+Number\s+ofwirncsses', '', text)
    text = re.sub(r'\(\'~[\'\s]*alfirm', 'or affirmation', text)
    text = re.sub(r'\(\(In;~·lll~\(;\[-~dlld;\.\',i:,', '', text)

    # 2. Specific Section 55 and merged phrases
    text = re.sub(r'noticeasmaybepublished', 'notice as may be published', text)
    text = re.sub(r'intheFederalor\s*State', 'in the Federal or State', text)
    text = re.sub(r'intheFederalor', 'in the Federal or', text)
    text = re.sub(r'cified"meansspecified', 'cified" means specified', text)

    # 3. Universal word & character replacements
    subs = [
        (r"\b01\'\b", "or"),
        (r"\b01\b(?=\s+[a-z])", "or"),
        (r"\b1I1\b", "in"),
        (r"\b111\b(?=\s+[a-z])", "in"),
        (r"\b1'01'\b", "for"),
        (r"\bhv\b", "by"),
        (r"\blo\b", "to"),
        (r"\bu!\'\b", "of"),
        (r"\bu!\b", "of"),
        (r"\blucts\b", "facts"),
        (r"\bofproperty\b", "of property"),
        (r"\bifit\b", "if it"),
        (r"\bPartyto\b", "party to"),
        (r"\bGovernmentPharmacist\b", "Government Pharmacist"),
        (r"\bIfora!\b", "If oral"),
        (r"\bgencratf\b", "generally"),
        (r"\bsectionI\b", "section 1"),
        (r"\bgivenof\b", "given of"),
        (r"\basmay\b", "as may"),
        (r"\bwhether->\b", "whether—"),
        (r"\bwhether\s*->\b", "whether—"),
        (r'\bofthe\b', "of the"),
        (r'\binthe\b', "in the"),
        (r'\bforthe\b', "for the"),
        (r'\bbythe\b', "by the"),
        (r'\btothe\b', "to the"),
        (r'\bandthe\b', "and the"),
        (r'referred\s+10\b', "referred to"),
        (r'combinations\s+OJ\b', "combinations of"),
        (r'\"lorthe\b', "for the"),
        (r'certificate\s*—\.', "certificate—"),
        (r'certificate\s*-\.', "certificate—"),
        (r'\(\s*\]\s*', '(1) '),
        (r'\(\s*[lI]\s*\)', '(1)'),
        (r'\(\s*J\s*J\s*', '(1) '),
        (r'\(\)\)', '(1)'),
        (r'\(\s*([a-z\d]+)\s*\]', r'(\1)'),
        (r'\[\s*([a-z\d]+)\s*\)', r'(\1)'),
        (r'\[I\b', 'a'),
        (r'\bpatties\b', 'parties'),
        (r'\bwire\b(?=\s+01\'|\s+or)', 'wife'),
        (r'\bhis\s+wire\b', 'his wife'),
        (r'\bl4\s+years\b', '14 years'),
        (r'\bnil\s+oath\b', 'on oath'),
    ]
    for pat, rep in subs:
        text = re.sub(pat, rep, text)

    # 4. Standardize spacing and punctuation
    text = re.sub(r'\s+([,;:\.\)])', r'\1', text)
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

for sec in data.get("sections", []):
    cleaned = deep_clean_evidence(sec.get("full_text", ""))
    sec["full_text"] = cleaned
    sec["searchable_chunk"] = f"Evidence Act 2011 | Section {sec.get('section_number', '')} | {cleaned}"

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("[✓] Evidence Act 2011 Section 55 and siblings repaired.")
