import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", message=".*LibreSSL.*")

import os
import sys
import json
import sqlite3
import re
import requests
from pathlib import Path

DB_PATH = Path("data/nigerian_law.db")
API_KEY = os.environ.get("GEMINI_API_KEY")

STATUTE_REGISTRY = [
    "Constitution of the Federal Republic of Nigeria 1999 (CFRN)",
    "Labour Act, 1971",
    "Administration of Criminal Justice Act, 2015 (ACJA)",
    "Nigeria Police Act, 2020",
    "Evidence Act, 2011",
    "Cybercrimes (Prohibition, Prevention, etc.) Act, 2015",
    "Federal Competition and Consumer Protection Act, 2018 (FCCPA)",
    "Money Laundering (Prohibition) Act, 2011",
    "Child's Rights Act, 2003",
    "Corrupt Practices and Other Related Offences Act, 2000 (ICPC)",
    "Economic and Financial Crimes Commission Act, 2004 (EFCC)",
    "Terrorism (Prevention) Act, 2011",
    "Penal Code Federal Provisions Act, 1960"
]

def call_gemini(prompt: str, response_json: bool = False, temperature: float = 0.0) -> str:
    if not API_KEY:
        return ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 800
        }
    }
    if response_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    try:
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=12)
        if res.status_code == 200:
            return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass
    return ""

def check_direct_citation(query: str, conn) -> list:
    pattern = r'(?:section|sec\.?|s\.)\s*(\d+[a-zA-Z]?)'
    match = re.search(pattern, query, re.IGNORECASE)
    if not match:
        return []

    sec_num = match.group(1)
    cursor = conn.cursor()
    for statute in STATUTE_REGISTRY:
        short = statute.split(",")[0].split("(")[0].strip()
        stat_tokens = [t.lower() for t in re.findall(r'\w+', short) if len(t) > 3]
        if any(t in query.lower() for t in stat_tokens):
            cursor.execute("""
                SELECT statute_title, section_number, section_title, part, full_text
                FROM sections_fts
                WHERE statute_title LIKE ? AND section_number = ?
                LIMIT 1;
            """, (f"%{short}%", sec_num))
            row = cursor.fetchone()
            if row:
                return [{
                    "statute": row[0],
                    "section_number": row[1],
                    "section_title": row[2],
                    "part": row[3],
                    "snippet": row[4][:300] + "...",
                    "analysis": f"Direct statutory match for Section {sec_num} of {row[0]}."
                }]
    return []

def analyze_and_route(scenario: str) -> dict:
    statute_list_str = "\n".join([f"- {s}" for s in STATUTE_REGISTRY])
    
    prompt = f"""
You are a principal Nigerian legal intelligence routing system.
Analyze this user query or case scenario:
"{scenario}"

Available Statutes in Corpus:
{statute_list_str}

Execution Steps:
1. Determine the exact legal issue, right infringed, crime committed, or regulatory procedure involved.
2. Select 1 to 3 candidate statutes from the list that govern this issue.
3. Identify 4 to 6 specific Nigerian statutory doctrines, terms of art, marginal notes, or key prohibitions (e.g. "arrest in lieu", "in place of a suspect", "electronic records", "maternity protection", "search of person", "implied warranty").
4. Extract 3 to 4 individual keyword stems.

Return ONLY a JSON object:
{{
  "legal_summary": "1-sentence summary of the legal issue",
  "target_statutes": ["Exact Statute Name 1", "Exact Statute Name 2"],
  "legal_phrases": ["phrase 1", "phrase 2", "phrase 3"],
  "keyword_stems": ["stem1", "stem2"]
}}
"""
    raw = call_gemini(prompt, response_json=True)
    try:
        return json.loads(raw)
    except Exception:
        words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', scenario.lower())]
        return {
            "legal_summary": scenario,
            "target_statutes": [],
            "legal_phrases": [],
            "keyword_stems": words[:4]
        }

def retrieve_candidate_pool(conn, plan: dict, raw_query: str) -> list:
    cursor = conn.cursor()
    candidates = {}

    phrases = plan.get("legal_phrases", [])
    stems = plan.get("keyword_stems", [])
    target_statutes = plan.get("target_statutes", [])

    fts_parts = []
    for p in phrases:
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', p).strip()
        if clean:
            fts_parts.append(f'"{clean}"')
    for s in stems:
        clean = re.sub(r'[^a-zA-Z0-9]', '', s).strip()
        if clean:
            fts_parts.append(f"{clean}*")
            
    fts_query = " OR ".join(fts_parts) if fts_parts else raw_query

    sql_global = """
    SELECT 
        statute_title,
        section_number,
        section_title,
        part,
        snippet(sections_fts, 4, '⟦', '⟧', '...', 35) as snippet,
        bm25(sections_fts) as rank,
        full_text
    FROM sections_fts
    WHERE sections_fts MATCH ?
    ORDER BY rank
    LIMIT 25;
    """

    try:
        cursor.execute(sql_global, (fts_query,))
        for r in cursor.fetchall():
            key = (r[0], str(r[1]))
            if key not in candidates:
                candidates[key] = {
                    "statute": r[0],
                    "section_number": r[1],
                    "section_title": r[2],
                    "part": r[3],
                    "snippet": r[4],
                    "rank": r[5],
                    "full_text": r[6]
                }
    except Exception:
        pass

    for stat in target_statutes:
        short = stat.split(",")[0].split("(")[0].strip()
        sql_scoped = """
        SELECT 
            statute_title,
            section_number,
            section_title,
            part,
            snippet(sections_fts, 4, '⟦', '⟧', '...', 35) as snippet,
            bm25(sections_fts) as rank,
            full_text
        FROM sections_fts
        WHERE statute_title LIKE ? AND sections_fts MATCH ?
        ORDER BY rank
        LIMIT 6;
        """
        try:
            cursor.execute(sql_scoped, (f"%{short}%", fts_query))
            for r in cursor.fetchall():
                key = (r[0], str(r[1]))
                if key not in candidates:
                    candidates[key] = {
                        "statute": r[0],
                        "section_number": r[1],
                        "section_title": r[2],
                        "part": r[3],
                        "snippet": r[4],
                        "rank": r[5],
                        "full_text": r[6]
                    }
        except Exception:
            pass

    return list(candidates.values())

def rank_and_verify(scenario: str, legal_summary: str, candidates: list) -> list:
    if not candidates or not API_KEY:
        return candidates[:3]

    cards = []
    for idx, c in enumerate(candidates):
        cards.append(
            f"ID [{idx}] | {c['statute']} | Sec {c['section_number']}: {c['section_title']}\n"
            f"Text: {c['full_text'][:450]}..."
        )
    blob = "\n\n".join(cards)

    prompt = f"""
User Query: "{scenario}"
Legal Context: "{legal_summary}"

Candidate Statutory Provisions:
{blob}

Task:
1. Select ONLY provisions that directly govern, penalize, prohibit, or provide a remedy for the issue.
2. EXCLUDE generic administrative sections (e.g. general duties, preamble definitions, objectives) when a specific substantive provision exists.
3. Return up to 3 highest-signal provisions in strict order of relevance.

Return JSON format:
[
  {{
    "id": 0,
    "legal_analysis": "One concise sentence explaining how this section directly governs the situation."
  }}
]
"""
    raw = call_gemini(prompt, response_json=True)
    try:
        selected = json.loads(raw)
        results = []
        for item in selected:
            idx = item.get("id")
            if idx is not None and 0 <= idx < len(candidates):
                c = candidates[idx]
                c["analysis"] = item.get("legal_analysis", "")
                results.append(c)
        return results if results else candidates[:1]
    except Exception:
        return candidates[:2]

def search(user_input: str):
    if not DB_PATH.exists():
        print("[!] Database not found. Run build_database.py first.")
        return

    conn = sqlite3.connect(DB_PATH)

    direct_hits = check_direct_citation(user_input, conn)
    if direct_hits:
        conn.close()
        print("\n" + "=" * 85)
        print(f"DIRECT STATUTORY CITATION MATCH: '{user_input}'")
        print("=" * 85)
        m = direct_hits[0]
        print(f"\n[1] {m['statute']}")
        print(f"    • Section {m['section_number']}: {m['section_title']} ({m['part']})")
        print(f"    • Application: {m['analysis']}")
        print(f"    • Statutory Excerpt:\n      {m['snippet']}")
        print("\n" + "=" * 85)
        return

    print("\n" + "=" * 85)
    print(f"[*] Analyzing legal inquiry: '{user_input}'...")
    plan = analyze_and_route(user_input)
    
    print(f"[*] Legal Issue: {plan.get('legal_summary')}")
    if plan.get('target_statutes'):
        print(f"[*] Targeted Statutes: {', '.join(plan.get('target_statutes'))}")
    if plan.get('legal_phrases'):
        print(f"[*] Statutory Concepts: {', '.join(plan.get('legal_phrases'))}")

    candidates = retrieve_candidate_pool(conn, plan, user_input)
    conn.close()

    if not candidates:
        print("\nNo matching statutory provisions found.")
        print("=" * 85)
        return

    print(f"[*] Evaluated candidate pool of {len(candidates)} provisions. Ranking substantive hits...")
    final_matches = rank_and_verify(user_input, plan.get('legal_summary', user_input), candidates)

    print("\n" + "=" * 85)
    print(f"AUTHORITATIVE STATUTORY PROVISIONS ({len(final_matches)} result{'s' if len(final_matches) != 1 else ''})")
    print("=" * 85)

    for idx, match in enumerate(final_matches, 1):
        print(f"\n[{idx}] {match['statute']}")
        print(f"    • Section {match['section_number']}: {match['section_title']} ({match['part']})")
        if match.get("analysis"):
            print(f"    • Application: {match['analysis']}")
        print(f"    • Statutory Excerpt:\n      {match['snippet']}")

    print("\n" + "=" * 85)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 search_law.py \"<scenario, legal question, or citation>\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    search(query)
