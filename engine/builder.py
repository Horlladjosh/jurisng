import json
import sqlite3
import os
from typing import Dict, List, Any
from pathlib import Path

DB_PATH = Path("data/nigerian_law.db")
JSON_DIR = Path("data/json_laws")

class CorpusBuilder:
    @staticmethod
    def save_statute_json(statute_id: str, short_title: str, year: int, jurisdiction: str, sections: List[Dict[str, Any]]) -> str:
        JSON_DIR.mkdir(parents=True, exist_ok=True)
        file_path = JSON_DIR / f"{statute_id}.json"

        data = {
            "statute_id": statute_id,
            "title": short_title,
            "short_title": short_title,
            "year": year,
            "jurisdiction": jurisdiction,
            "total_sections": len(sections),
            "sections": sections
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return str(file_path)

    @staticmethod
    def rebuild_database():
        print("[*] Rebuilding SQLite database and FTS5 search index...")
        os.system("python3 build_database.py")
        print("[✓] Database rebuild complete.")
