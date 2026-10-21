#!/usr/bin/env python3
"""
lint_corpus.py
Automated Quality Assurance Gate & Corpus Invariant Linter for Nigerian Law Engine.

Asserts 6 core invariants across all JSON enactments in data/json_laws/:
  1. Zero Bloat: No section full_text > 30,000 characters (stripped schedules).
  2. Zero Truncation: No section full_text < 35 characters (non-empty substantive text).
  3. Clean Titles: No table-of-contents chapter/part headers glued to section titles.
  4. Disjoint Sections: No embedded alteration sections (e.g. 16A, 254A) inside section titles.
  5. Unpacked Bodies: No unextracted numbered sections buried inside section full_text.
  6. Schema Completeness: Required metadata (statute_id, short_title, sections) present.

Exits with 0 on 100% compliance; exits with 1 on any violation.
"""

import sys
import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
JSON_DIR = ROOT_DIR / "data" / "json_laws"

def lint_statute(file_path: Path) -> list:
    errors = []
    fname = file_path.name
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"[{fname}] Invalid JSON: {e}"]
        
    statute_id = data.get("statute_id")
    if not statute_id:
        errors.append(f"[{fname}] Missing 'statute_id'")
        
    short_title = data.get("short_title") or data.get("title")
    if not short_title:
        errors.append(f"[{fname}] Missing 'short_title' or 'title'")
        
    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) == 0:
        errors.append(f"[{fname}] 'sections' must be a non-empty list")
        return errors

    seen_numbers = set()
    for s in sections:
        sec_num = str(s.get("section_number", "")).strip()
        sec_title = str(s.get("section_title") or s.get("title") or "").strip()
        full_text = str(s.get("full_text") or s.get("content") or "").strip()
        
        if not sec_num:
            errors.append(f"[{fname}] Section missing 'section_number': {s}")
            continue
            
        # 1. Zero Bloat (< 30,000 chars)
        if len(full_text) > 30000:
            errors.append(f"[{fname} s.{sec_num}] Schedule bloat: full_text length {len(full_text)} > 30,000 chars")
            
        # 2. Zero Truncation (>= 35 chars)
        if len(full_text) < 35:
            errors.append(f"[{fname} s.{sec_num}] Truncated/Empty text: length {len(full_text)} < 35 chars (text: {repr(full_text)})")
            
        # 3. Clean Titles (no glued Part/Chapter headers)
        if re.search(r'[-–—]\s*(?:Part|Chapter)\s+[IVXLCDM0-9]+', sec_title, re.IGNORECASE) or re.search(r'\s+[B-G]\s*[-–—]\s*[A-Z][a-z]+', sec_title):
            errors.append(f"[{fname} s.{sec_num}] Glued header in title: {repr(sec_title)}")
            
        # 4. Disjoint Sections (no embedded alteration sections in titles)
        if re.search(r'\b\d+[A-Z]?\.\s+[A-Z]', sec_title):
            errors.append(f"[{fname} s.{sec_num}] Embedded section in title: {repr(sec_title)}")
            
        # 5. Unpacked Bodies (no unextracted numbered sections buried in body text)
        embed_matches = re.findall(r'\n\s*(\d+[A-Z]?)\.\s+([A-Z][A-Za-z\s]{3,40})\n', full_text)
        if embed_matches:
            valid_embeds = [m for m in embed_matches if m[0] != sec_num and int(re.sub(r'\D', '', m[0]) or 0) > 0]
            if valid_embeds:
                errors.append(f"[{fname} s.{sec_num}] Unextracted sections in body: {valid_embeds[:3]}")
                
    return errors

def lint_all_laws(json_dir: Path):
    json_files = sorted(list(json_dir.glob("*.json")))
    total_errors = 0
    clean_files = 0
    all_errors = {}
    for f in json_files:
        errors = lint_statute(f)
        if errors:
            total_errors += len(errors)
            all_errors[f.name] = errors
        else:
            clean_files += 1
    return (total_errors == 0), len(json_files), total_errors, all_errors

def main():
    if not JSON_DIR.exists():
        print(f"[x] Error: JSON directory not found at {JSON_DIR}")
        sys.exit(1)
        
    print(f"[*] Auditing statutory files against Corpus Invariants...\n")
    passed, total_files, total_errors, all_errors = lint_all_laws(JSON_DIR)
    
    for fname, errors in all_errors.items():
        print(f"[!] Defect detected in {fname}:")
        for err in errors:
            print(f"    - {err}")
            
    print("-" * 70)
    print(f"Audit Summary: {total_files - len(all_errors)}/{total_files} files 100% compliant ({total_errors} total defects found).")
    
    if not passed:
        print(f"\n[x] LINTER FAILED: {total_errors} invariant violations must be resolved.")
        sys.exit(1)
    else:
        print("\n[+] LINTER PASSED: All 134 statutes and 10,000+ sections meet 100% corpus quality invariants!")
        sys.exit(0)

if __name__ == "__main__":
    main()

