#!/usr/bin/env python3
"""
Nigerian Law Engine - Corpus Cleaning CLI
Cleans PDF/extraction artifacts across statutory JSON files.

Usage:
    # Dry run on all files (preview changes without modifying disk):
    python clean_corpus.py --all --dry-run

    # Apply cleaning to all files:
    python clean_corpus.py --all --write

    # Clean a single statute file:
    python clean_corpus.py --file data/json_laws/freedom_of_information_act_2011.json --dry-run
    python clean_corpus.py --file data/json_laws/freedom_of_information_act_2011.json --write
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from engine.cleaner import clean_statute_dict, clean_section_text

JSON_DIR = Path("data/json_laws")

def process_file(file_path: Path, write: bool = False, verbose: bool = True):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    statute_title = data.get("short_title", data.get("statute_title", file_path.stem))
    sections = data.get("sections", [])
    
    modified_sections = []
    
    for s in sections:
        raw = s.get("full_text", "")
        cleaned = clean_section_text(raw)
        if cleaned != raw:
            diff_chars = len(raw) - len(cleaned)
            modified_sections.append({
                "section_number": s.get("section_number"),
                "section_title": s.get("section_title", s.get("title")),
                "raw_tail": raw[-150:],
                "cleaned_tail": cleaned[-150:],
                "diff_chars": diff_chars,
                "cleaned_text": cleaned
            })

    if not modified_sections:
        return 0

    if verbose:
        print(f"\n[!] Statute: {statute_title} ({file_path.name})")
        print(f"    Modified Sections: {len(modified_sections)} of {len(sections)}")
        for m in modified_sections:
            sec_num = m["section_number"]
            print(f"    • Sec {sec_num} (-{m['diff_chars']} chars removed):")
            print(f"      RAW END    : {repr(m['raw_tail'])}")
            print(f"      CLEANED END: {repr(m['cleaned_tail'])}")

    if write:
        cleaned_data, _ = clean_statute_dict(data)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        if verbose:
            print(f"    [✓] Written back to {file_path.name}")

    return len(modified_sections)


def main():
    parser = argparse.ArgumentParser(description="Nigerian Law Engine - Corpus Cleaning Utility")
    parser.add_argument("--all", action="store_true", help="Process all statutes in data/json_laws/")
    parser.add_argument("--file", type=str, help="Process a single JSON statute file")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Preview cleaning without writing changes")
    parser.add_argument("--write", action="store_true", default=False, help="Write cleaned text to JSON file(s)")

    args = parser.parse_args()

    # If neither flag is provided, default to dry-run for safety
    is_write = args.write and not args.dry_run

    if args.file:
        target_path = Path(args.file)
        if not target_path.exists():
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        files = [target_path]
    elif args.all:
        files = sorted(list(JSON_DIR.glob("*.json")))
    else:
        print("Please specify --all or --file <path>.")
        parser.print_help()
        sys.exit(1)

    mode_label = "APPLYING WRITES" if is_write else "DRY-RUN (NO FILES MODIFIED)"
    print("=" * 80)
    print(f"NIGERIAN LAW ENGINE - CORPUS CLEANING UTILITY")
    print(f"Mode: {mode_label}")
    print(f"Files to inspect: {len(files)}")
    print("=" * 80)

    total_modified_statutes = 0
    total_modified_sections = 0

    for f in files:
        count = process_file(f, write=is_write, verbose=True)
        if count > 0:
            total_modified_statutes += 1
            total_modified_sections += count

    print("\n" + "=" * 80)
    print("CLEANING SUMMARY:")
    print(f"  • Total Statutes Checked : {len(files)}")
    print(f"  • Statutes with Artifacts: {total_modified_statutes}")
    print(f"  • Sections Cleaned       : {total_modified_sections}")
    print(f"  • Mode Executed          : {mode_label}")
    if not is_write and total_modified_sections > 0:
        print("\n  -> To apply these cleanups to the JSON corpus, re-run with: python clean_corpus.py --all --write")
    print("=" * 80)

if __name__ == "__main__":
    main()
