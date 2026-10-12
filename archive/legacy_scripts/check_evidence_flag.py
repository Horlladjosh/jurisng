import json
import re
from pathlib import Path

REAL_OCR_DEFECTS = {
    'Broken Subsection Parens': r'\(\s*\]|\(l\s*\)|\(I\s*\)|\b0\)',
    'Corrupted Word (01 or or)': r"\b01\'\b|\b01\b\s+[a-z]",
    'Corrupted Word (1I1 or in)': r'\b1I1\b|\b111\b\s+[a-z]',
    'Corrupted Word (lo or to)': r'\blo\b|\bhv\b',
    'Punctuation Glitch': r"u!\'|asmay|whether->|certificate\s*—\.",
    'Merged Words': r'\bofthe\b|\binthe\b|\bforthe\b|\bbythe\b',
    'Gazette Watermark': r'Adnussibilu|dfKII|Official\s+Gazette\s+No\.',
}

path = Path('data/json_laws/evidence_act_2011.json')
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

found = False
for sec in data.get('sections', []):
    num = sec.get('section_number')
    text = sec.get('full_text', '')
    for label, pat in REAL_OCR_DEFECTS.items():
        m = re.search(pat, text)
        if m:
            found = True
            print(f'Evidence Act Section {num} failed on: [{label}] -> Matched: {repr(m.group(0))}')
            print('Context:', repr(text[max(0, m.start()-30):min(len(text), m.end()+30)]))

if not found:
    print('No flags detected in Evidence Act 2011.')
