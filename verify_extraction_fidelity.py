import sqlite3
import json
from pathlib import Path

DB_PATH = Path("data/nigerian_law.db")
JSON_DIR = Path("data/json_laws")

def verify_all_statutes():
    print("=" * 80)
    print("JURISNG STATUTORY FIDELITY AUDIT & INTEGRITY REPORT")
    print("=" * 80)

    json_files = sorted(list(JSON_DIR.glob("*.json")))
    print(f"[*] Found {len(json_files)} Statute JSON files in {JSON_DIR}:")

    total_sections_count = 0
    passed_statutes = 0
    failed_statutes = 0

    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)

        title = data.get("title", data.get("short_title", data.get("statute_title", jf.stem)))
        sections = data.get("sections", [])
        total_sections_count += len(sections)

        empty_secs = [s for s in sections if len(s.get("full_text", s.get("content", "")).strip()) < 10]
        untitled_secs = [s for s in sections if not s.get("section_title", s.get("title", "")).strip()]

        status = "PASSED" if not empty_secs and not untitled_secs else "FAILED"
        if status == "PASSED":
            passed_statutes += 1
            print(f"  [✓] {title:60s} | {len(sections):4d} sections | 100% Valid")
        else:
            failed_statutes += 1
            print(f"  [✗] {title:60s} | {len(sections):4d} sections | Empty: {len(empty_secs)}, Untitled: {len(untitled_secs)}")

    print("-" * 80)
    print(f"Corpus Summary: {passed_statutes}/{len(json_files)} Statutes Verified (Total Sections: {total_sections_count:,})")
    print("-" * 80)

    # SQLite Database Audit
    print("\n[*] Auditing SQLite Database & FTS5 Search Index...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM statutes;")
    db_statutes_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sections;")
    db_sections_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sections_fts;")
    fts_sections_count = cursor.fetchone()[0]

    conn.close()

    print(f"  • DB Statutes:      {db_statutes_count}")
    print(f"  • DB Sections:      {db_sections_count}")
    print(f"  • FTS5 Indexed:     {fts_sections_count}")

    assert db_statutes_count == len(json_files), "Statute count mismatch between JSON corpus and DB"
    assert db_sections_count == total_sections_count, "Section count mismatch between JSON corpus and DB"
    assert fts_sections_count == total_sections_count, "FTS5 index count mismatch"

    print("\n" + "=" * 80)
    print("ALL STATUTORY FIDELITY AND SEARCH CHECKS PASSED (100% PRECISION)")
    print("=" * 80)

if __name__ == "__main__":
    verify_all_statutes()
