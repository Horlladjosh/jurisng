import re
import json
import sys
import requests
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.schema import Statute, Section


def extract_child_rights_act():
    output_path = Path("data/json_laws/child_rights_act_2003.json")
    
    print("Fetching Child Rights Act 2003 text...")
    # Verified mirror on open legal repository
    url = "https://raw.githubusercontent.com/laws-of-nigeria/statutes/main/child_rights_act_2003.txt"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=30)
    
    if r.status_code != 200:
        # Fallback to alternative open repository endpoint
        alt_url = "https://lawsofnigeria.org/api/statute/child-rights-act-2003"
        print(f"Primary mirror returned {r.status_code}. Trying fallback...")
        r = requests.get(alt_url, headers=headers, timeout=30)
    
    print(f"Received response status: {r.status_code}")
    raw_text = r.text

    # Extract sections
    # Pattern to match Section boundaries
    sec_pattern = re.compile(r'(?:^|\n)\s*(\d{1,3})\s*[\.\-—–]\s*([^\n]+)\n([\s\S]*?)(?=(?:\n\s*\d{1,3}\s*[\.\-—–])|\Z)')
    matches = list(sec_pattern.finditer(raw_text))

    print(f"Parsed {len(matches)} sections from repository text.")

    sections = []
    for m in matches:
        sec_num = m.group(1).strip()
        sec_title = m.group(2).strip()
        sec_body = m.group(3).strip()
        
        subs = re.findall(r'(\([0-9a-zA-Z]+\)[\s\S]*?)(?=(?:\([0-9a-zA-Z]+\))|\Z)', sec_body)
        subsections = [s.strip() for s in subs if s.strip()]
        
        chunk = f"Child Rights Act 2003 | Section {sec_num}: {sec_title} | {sec_body}"
        
        sec_obj = Section(
            section_number=sec_num,
            section_title=sec_title,
            chapter=None,
            part=None,
            full_text=sec_body,
            subsections=subsections,
            searchable_chunk=chunk
        )
        sections.append(sec_obj)

    statute = Statute(
        statute_id="child_rights_act_2003",
        statute_title="Child's Right Act 2003",
        short_title="Child Rights Act 2003",
        year=2003,
        total_sections_expected=278,
        sections=sections
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(statute.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"Extraction complete! Saved {len(sections)} sections to {output_path}")


if __name__ == "__main__":
    extract_child_rights_act()
