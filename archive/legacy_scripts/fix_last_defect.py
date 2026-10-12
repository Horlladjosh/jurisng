import json
import re
from pathlib import Path

path = Path("data/json_laws/evidence_act_2011.json")
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

for sec in data.get("sections", []):
    t = sec.get("full_text", "")
    # Check against the audit patterns
    if re.search(r"\bu!\'|\bu!|\basmay|\bwhether->|certificate\s*—\.|\bofthe|\binthe|\bforthe|\bbythe|\b01\'|\b01\s+[a-z]|\b1I1\b|\b111\s+[a-z]|\blo\b|\bhv\b|\(\s*\]|\(l\s*\)|\(I\s*\)|\b0\)", t):
        print(f"Found issue in Section {sec.get('section_number')}:")
        print(repr(t[:200]))
        
        # Apply strict fixes
        t = re.sub(r'\bu!\'\b', 'of', t)
        t = re.sub(r'\bu!\b', 'of', t)
        t = re.sub(r'\basmay\b', 'as may', t)
        t = re.sub(r'\bwhether->\b', 'whether—', t)
        t = re.sub(r'\b01\'\b', 'or', t)
        t = re.sub(r'\b01\b(?=\s+[a-z])', 'or', t)
        t = re.sub(r'\b1I1\b', 'in', t)
        t = re.sub(r'\b111\b(?=\s+[a-z])', 'in', t)
        t = re.sub(r'\bhv\b', 'by', t)
        t = re.sub(r'\blo\b', 'to', t)
        t = re.sub(r'\bofthe\b', 'of the', t)
        t = re.sub(r'\binthe\b', 'in the', t)
        t = re.sub(r'\bforthe\b', 'for the', t)
        t = re.sub(r'\bbythe\b', 'by the', t)
        t = re.sub(r'\s+', ' ', t).strip()
        
        sec["full_text"] = t
        sec["searchable_chunk"] = f"Evidence Act 2011 | Section {sec.get('section_number')} | {t}"

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("[✓] Cleaned last Evidence Act section.")
