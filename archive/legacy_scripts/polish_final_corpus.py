import json
import re
from pathlib import Path

JSON_DIR = Path("data/json_laws")

def deep_clean(text: str) -> str:
    # 1. Punctuation & character misrecognitions
    replacements = [
        (r"\b01'\b", "or"),
        (r"\b01\b(?=\s+[a-z])", "or"),
        (r"\b1I1\b", "in"),
        (r"\bu!\'\b", "of"),
        (r"\bu!\b", "of"),
        (r"\basmay\b", "as may"),
        (r"\bwhether->\b", "whether—"),
        (r'combinations of"\s*computers', "combinations of computers"),
        (r'certificate\s*-\.', "certificate—"),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    
    # 2. Fix Section 84 incomplete ending specifically
    if "Section 84" in text or text.startswith("84."):
        if text.rstrip().endswith("produced by"):
            text = text.rstrip() + " it directly or (with or without human intervention) by means of any appropriate equipment."
        elif "(e) a document shall be taken" in text and not text.rstrip().endswith("."):
            text = re.sub(r'\(e\)\s*a document shall be taken to have been produced by a computer whether it was produced by.*',
                          '(c) a document shall be taken to have been produced by a computer whether it was produced by it directly or (with or without human intervention) by means of any appropriate equipment.',
                          text)

    # 3. Clean spacing
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def run_polish():
    for j_file in sorted(JSON_DIR.glob("*.json")):
        with open(j_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        statute_title = data.get("short_title", j_file.stem)
        for sec in data.get("sections", []):
            cleaned = deep_clean(sec.get("full_text", ""))
            sec["full_text"] = cleaned
            sec["searchable_chunk"] = f"{statute_title} | Section {sec.get('section_number', '')} | {cleaned}"

        with open(j_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[✓] Polished: {j_file.name}")

if __name__ == "__main__":
    run_polish()
