"""
Statutory Corpus Legal Typography & OCR Reflow Pipeline.
Cleans up OCR artifacts, broken hyphenations, stray spaces before punctuation,
and unnatural line-breaks while strictly preserving statutory numbering, subsections, and hierarchy.
"""

import json
import glob
import re
import os

def clean_and_reflow_legal_text(text: str) -> str:
    if not text:
        return ""
    
    # 1. Standardize unicode quotes, hyphens, dashes, ligatures
    text = text.replace("\uf0b7", "-").replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = text.replace("“", "\"").replace("”", "\"").replace("’", "'").replace("‘", "'")
    text = text.replace("–", "—").replace("--", "—")
    
    # 2. Fix split words across hyphens
    def fix_hyphen(m):
        w1, w2 = m.group(1), m.group(2)
        combined = f"{w1}-{w2}"
        known_compounds = {
            "north-west", "north-central", "north-east", "south-east", "south-south", "south-west",
            "ex-officio", "socio-economic", "non-governmental", "agro-allied", "cross-examination",
            "re-appointment", "re-appointed", "off-shore", "on-shore", "sub-section", "sub-paragraph",
            "co-operation", "co-operate", "co-operative", "co-ordination", "co-ordinate", "by-law", "by-laws",
            "cross-border", "anti-corruption", "anti-money", "quasi-judicial", "long-term", "short-term",
            "pre-action", "inter-state", "intra-state", "well-being", "decision-making", "policy-making",
            "oil-producing", "gas-producing", "fee-charging", "in-service", "in-depth", "time-table"
        }
        if combined.lower() in known_compounds:
            return f"{w1}-{w2}"
        if w2[0].islower():
            return f"{w1}{w2}"
        return f"{w1}-{w2}"

    text = re.sub(r"\b([a-zA-Z]{2,})-\s*\n\s*([a-zA-Z]{2,})\b", fix_hyphen, text)
    text = re.sub(r"\b([a-zA-Z]{3,})-\s+([a-z]{3,})\b", fix_hyphen, text)

    # 3. Clean spaces before punctuation
    text = re.sub(r"[ \t]+([;:,.])", r"\1", text)
    
    # 4. Reflow structural blocks
    lines = text.split("\n")
    processed_lines = []
    
    # Markers for legal structure:
    # e.g., (1), (2), (a), (b), (i), (ii), (A), (B), 1., 2., "Provided that", "Provided always", "Notwithstanding", "Subject to"
    structural_re = re.compile(
        r"^(\([0-9a-zA-Z]+\)|\([ivxIVX]+\)|[0-9]+\.|\bProvided\s+(?:that|always)\b|\bNotwithstanding\b|\bSubject to\b|\bWhere\b|\bIn this\b|\bFor the purpose)",
        re.IGNORECASE
    )
    
    current_block = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_block:
                processed_lines.append(current_block)
                current_block = ""
            continue
        
        is_structural = bool(structural_re.match(stripped))
        
        if is_structural:
            if current_block:
                processed_lines.append(current_block)
            current_block = stripped
        else:
            if current_block:
                current_block = current_block + " " + stripped
            else:
                current_block = stripped
                
    if current_block:
        processed_lines.append(current_block)
        
    result = "\n".join(processed_lines)
    # Normalize multiple internal spaces
    result = re.sub(r"[ \t]{2,}", " ", result)
    # Normalize em-dash clause transitions
    result = re.sub(r"\s*—\s*(\n|$)", " —\n", result)
    # Remove accidental consecutive blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def run_corpus_reflow():
    json_dir = os.path.join(os.path.dirname(__file__), "..", "data", "json_laws")
    files = sorted(glob.glob(os.path.join(json_dir, "*.json")))
    print(f"[*] Auditing and reflowing {len(files)} statute JSON files...")
    
    total_sections_reflowed = 0
    statutes_reflowed = 0
    
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            
        statute_title = data.get("title", "")
        statute_short = data.get("short_title", "")
        sections = data.get("sections", [])
        
        statute_changed = 0
        for s in sections:
            old_full = s.get("full_text", "")
            new_full = clean_and_reflow_legal_text(old_full)
            
            # Reconstruct searchable chunk
            part_str = f"\n{s.get('part')}" if s.get("part") else ""
            new_chunk = f"{statute_title} - Section {s.get('section_number')}: {s.get('section_title')}{part_str}\n{new_full}"
            
            if old_full != new_full:
                statute_changed += 1
                s["full_text"] = new_full
                s["searchable_chunk"] = new_chunk
            else:
                # Ensure searchable chunk is always up-to-date
                s["searchable_chunk"] = new_chunk
                
        if statute_changed > 0:
            statutes_reflowed += 1
            total_sections_reflowed += statute_changed
            with open(f, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2, ensure_ascii=False)
            print(f"    [✓] Reflowed {statute_changed:3d}/{len(sections):3d} sections: {statute_short or statute_title}")
            
    print(f"\n[✓] Reflow Complete! Reflowed {total_sections_reflowed} sections across {statutes_reflowed} statutes.")


if __name__ == "__main__":
    run_corpus_reflow()
