import sqlite3
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from engine.cleaner import clean_statute_dict

DB_PATH = Path("data/nigerian_law.db")
JSON_DIR = Path("data/json_laws")

def init_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[*] Rebuilding database at {DB_PATH}...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Relational Tables
    cursor.execute("""
    CREATE TABLE statutes (
        statute_id TEXT PRIMARY KEY,
        short_title TEXT NOT NULL,
        year INTEGER,
        jurisdiction TEXT,
        total_sections INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        statute_id TEXT NOT NULL,
        section_number TEXT NOT NULL,
        section_title TEXT NOT NULL,
        part TEXT,
        full_text TEXT NOT NULL,
        searchable_chunk TEXT NOT NULL,
        FOREIGN KEY (statute_id) REFERENCES statutes(statute_id)
    );
    """)

    # Standalone FTS5 Virtual Table (Self-Contained Storage)
    cursor.execute("""
    CREATE VIRTUAL TABLE sections_fts USING fts5(
        statute_title,
        section_number,
        section_title,
        part,
        full_text,
        tokenize='porter unicode61'
    );
    """)

    json_files = sorted(list(JSON_DIR.glob("*.json")))
    print(f"[*] Ingesting & auto-cleaning {len(json_files)} statutory files into SQLite + FTS5...")

    total_statutes = 0
    total_sections = 0
    auto_cleaned_statutes = 0

    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Automatic cleaning step for any new or modified articles
        data, cleaned_count = clean_statute_dict(data)
        if cleaned_count > 0:
            with open(jf, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            auto_cleaned_statutes += 1
            print(f"    [✨ Auto-Cleaned: {cleaned_count} sections with extraction artifacts in {jf.name}]")

        statute_id = data.get("statute_id", jf.stem)
        short_title = data.get("short_title", data.get("statute_title", jf.stem))
        year = data.get("year", None)
        jurisdiction = data.get("jurisdiction", "Federal Republic of Nigeria")
        sections = data.get("sections", [])

        cursor.execute("""
        INSERT INTO statutes (statute_id, short_title, year, jurisdiction, total_sections)
        VALUES (?, ?, ?, ?, ?);
        """, (statute_id, short_title, year, jurisdiction, len(sections)))

        for s in sections:
            sec_num = str(s.get("section_number", ""))
            sec_title = s.get("section_title", s.get("title", ""))
            part = s.get("part", "")
            full_text = s.get("full_text", s.get("content", ""))
            searchable_chunk = s.get("searchable_chunk", f"{short_title} Sec {sec_num}: {sec_title}. {full_text[:200]}")

            # Insert into relational table
            cursor.execute("""
            INSERT INTO sections (statute_id, section_number, section_title, part, full_text, searchable_chunk)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (statute_id, sec_num, sec_title, part, full_text, searchable_chunk))

            # Insert directly into FTS5 index table
            cursor.execute("""
            INSERT INTO sections_fts (statute_title, section_number, section_title, part, full_text)
            VALUES (?, ?, ?, ?, ?);
            """, (short_title, sec_num, sec_title, part, full_text))

        total_statutes += 1
        total_sections += len(sections)
        print(f"    [+] Indexed: {short_title} ({len(sections)} sections)")

    conn.commit()
    conn.close()

    print("\n" + "=" * 80)
    print(f"[✓] DATABASE & FTS5 INDEX REBUILT SUCCESSFULLY!")
    print(f"    • Database File: {DB_PATH}")
    print(f"    • Total Statutes: {total_statutes}")
    print(f"    • Total Indexed Sections: {total_sections}")
    print("=" * 80)

if __name__ == "__main__":
    init_db()
