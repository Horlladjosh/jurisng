import unittest
import sqlite3
from pathlib import Path
from engine.lint_corpus import lint_all_laws

class TestCorpusQuality(unittest.TestCase):
    def test_corpus_invariants(self):
        """Invariant QA Gate: All 134 statute files must pass with 0 defects."""
        laws_dir = Path("data/json_laws")
        self.assertTrue(laws_dir.exists(), "data/json_laws must exist")
        
        passed, total_files, total_defects, all_errors = lint_all_laws(laws_dir)
        self.assertTrue(passed, f"Corpus linting failed with {total_defects} defects across {total_files} files: {all_errors}")
        self.assertEqual(total_defects, 0, f"Expected 0 defects, got {total_defects}")
        self.assertGreaterEqual(total_files, 134, f"Expected at least 134 statutes, found {total_files}")

    def test_sqlite_database_integrity(self):
        """Database Integrity QA Gate: SQLite database must contain all statutes and sections."""
        db_path = Path("data/nigerian_law.db")
        self.assertTrue(db_path.exists(), "data/nigerian_law.db must exist")
        
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check total statutes
        c.execute("SELECT COUNT(*) FROM statutes;")
        total_statutes = c.fetchone()[0]
        self.assertGreaterEqual(total_statutes, 134, f"Expected >= 134 statutes, found {total_statutes}")
        
        # Check total sections
        c.execute("SELECT COUNT(*) FROM sections;")
        total_sections = c.fetchone()[0]
        self.assertGreaterEqual(total_sections, 10000, f"Expected >= 10,000 sections, found {total_sections}")
        
        # Check FTS5 index
        c.execute("SELECT COUNT(*) FROM sections_fts;")
        fts_count = c.fetchone()[0]
        self.assertEqual(fts_count, total_sections, "FTS5 table count must match sections table count")
        
        # Check CFRN unpacked sections (254A-F)
        c.execute("SELECT section_number, section_title FROM sections WHERE statute_id = 'cfrn_1999' AND section_number LIKE '254%';")
        nic_secs = dict(c.fetchall())
        for num in ['254', '254A', '254B', '254C', '254D', '254E', '254F']:
            self.assertIn(num, nic_secs, f"CFRN section {num} must be present in database")
            
        # Check CFRN Citation text
        c.execute("SELECT full_text FROM sections WHERE statute_id = 'cfrn_1999' AND section_number = '319';")
        citation_row = c.fetchone()
        self.assertIsNotNone(citation_row, "CFRN section 319 must exist")
        self.assertIn("Constitution of the Federal Republic of Nigeria 1999", citation_row[0])
        
        conn.close()

if __name__ == "__main__":
    unittest.main()
