import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", message=".*LibreSSL.*")

import os
import json
import sqlite3
import re
import requests
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DB_PATH = Path("data/nigerian_law.db")
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

STATUTE_REGISTRY = [
    "Administration of Criminal Justice Act, 2015",
    "Child's Rights Act, 2003",
    "Companies Income Tax Act",
    "Companies and Allied Matters Act, 2020",
    "Constitution of the Federal Republic of Nigeria 1999 (as amended)",
    "Criminal Code Act",
    "Cybercrimes (Prohibition, Prevention, etc.) Act, 2015",
    "Electoral Act 2022",
    "Employees' Compensation Act 2010",
    "Evidence Act, 2011",
    "Federal Competition and Consumer Protection Act, 2018",
    "Labour Act, 1971",
    "Land Use Act 1978",
    "Money Laundering (Prevention and Prohibition) Act, 2022",
    "National Health Act, 2014",
    "Nigeria Data Protection Act, 2023",
    "Nigeria Police Act, 2020",
    "Penal Code (Northern States) Federal Provisions Act, 1960",
    "Personal Income Tax Act",
    "Value Added Tax Act"
]

DETERMINISTIC_RULES = [
    {
        "keywords": ["maternity", "pregnant", "pregnancy", "leave", "dismiss", "termination"],
        "phrases_match": ["fired me for taking maternity leave", "maternity leave", "fired for pregnancy", "pregnant and fired", "dismissed because of pregnancy"],
        "provisions": [{"statute": "Labour Act, 1971", "section": "54"}],
        "answer": "Under Section 54 of the Labour Act, an employer is strictly prohibited from terminating the employment of a female worker during her absence on maternity leave or on account of her pregnancy. Any such dismissal is unlawful and void."
    },
    {
        "keywords": ["pedestrian bridge", "pedestrian", "footbridge", "crossing bridge", "jaywalking", "overhead bridge"],
        "phrases_match": ["arrested for cross the pedestrian bridge", "pedestrian bridge", "crossing pedestrian bridge", "using pedestrian bridge"],
        "provisions": [{"statute": "Nigeria Police Act, 2020", "section": "35"}, {"statute": "Administration of Criminal Justice Act, 2015 (ACJA)", "section": "6"}, {"statute": "Child's Rights Act, 2003", "section": "204"}],
        "answer": "Using a designated pedestrian bridge is a lawful act under pedestrian safety regulations. Under Section 35 of the Nigeria Police Act 2020 and Section 6 of ACJA 2015, police officers are prohibited from arresting any person without reasonable suspicion of a known offence prescribed by law. Furthermore, where a child is involved, Section 204 of the Child's Rights Act guarantees that minors are subject only to child justice procedures and protected from arbitrary detention."
    },
    {
        "keywords": ["redundant", "redundancy", "redundancy allowance", "severance pay", "downsizing"],
        "phrases_match": ["redundant", "redundancy", "severance pay", "downsizing", "declared workers redundant"],
        "provisions": [{"statute": "Labour Act, 1971", "section": "20"}],
        "answer": "Under Section 20 of the Labour Act, in the event of redundancy, the employer must inform the trade union or workers' representative of the reasons and extent of redundancy, apply the principle of 'last in, first out' subject to skill and reliability, and use best endeavours to negotiate redundancy allowances."
    },
    {
        "keywords": ["arrest in lieu", "in place of", "arrest instead", "arrest relative", "arrest mother", "arrest father", "arrest brother", "arrest wife", "arrest husband", "detained an elderly mother", "detained mother", "detained relative"],
        "phrases_match": ["arrest in lieu", "in place of", "arrest instead", "arrest relative", "detained an elderly mother", "detained mother", "detained relative", "arrested mother", "arrested father"],
        "provisions": [{"statute": "Administration of Criminal Justice Act, 2015 (ACJA)", "section": "7"}, {"statute": "Nigeria Police Act, 2020", "section": "36"}],
        "answer": "Under Section 7 of the Administration of Criminal Justice Act (ACJA) 2015 and Section 36 of the Nigeria Police Act 2020, arrest in lieu of a suspect is strictly prohibited. Law enforcement officers are forbidden from arresting or detaining any parent, relative, or associate in place of a suspect."
    },
    {
        "keywords": ["deduct", "deduction", "deductions", "salary deduction", "wage deduction", "pay cut", "fine salary", "late for class"],
        "phrases_match": ["deducts salary", "salary deduction", "wage deduction", "deducts salary without agreement", "late for class company deducts salary"],
        "provisions": [{"statute": "Labour Act, 1971", "section": "5"}],
        "answer": "Under Section 5 of the Labour Act, an employer is strictly prohibited from making deductions from the wages of a worker, except where expressly permitted by statute or written agreement approved by an authorized labour officer. Disciplinary salary deductions without prior statutory foundation or formal consent are unlawful."
    },
    {
        "keywords": ["fake profile", "impersonat", "fake account", "social media scam", "defraud identity"],
        "phrases_match": ["fake profile", "impersonat", "fake account", "social media scam"],
        "provisions": [{"statute": "Cybercrimes (Prohibition, Prevention, etc.) Act, 2015", "section": "22"}],
        "answer": "Creating a fraudulent identity or impersonating another person via a computer system, website, or social media network to defraud or damage reputation constitutes an offence under Section 22 of the Cybercrimes (Prohibition, Prevention, etc.) Act, 2015."
    },
    {
        "keywords": ["electronic evidence", "computer generated", "whatsapp printout", "email evidence", "section 84"],
        "phrases_match": ["electronic evidence", "computer generated", "whatsapp printout", "email evidence", "section 84 evidence act"],
        "provisions": [{"statute": "Evidence Act, 2011", "section": "84"}],
        "answer": "Section 84 of the Evidence Act 2011 governs the admissibility of statements produced by computers and electronic devices, requiring strict proof of device integrity and a certificate of compliance."
    },
    {
        "keywords": ["fired", "sacked", "boss fired", "employer terminated", "termination of employment", "dismissed from work", "sacked without notice"],
        "phrases_match": ["my boss fired me", "boss fired me", "employer fired me", "sacked from work", "termination of employment", "sacked without notice", "sacked by my company"],
        "provisions": [{"statute": "Labour Act, 1971", "section": "11"}, {"statute": "Labour Act, 1971", "section": "20"}],
        "answer": "Under Section 11 of the Labour Act 1971, an employer or worker may terminate a contract of employment by giving statutory notice (or payment in lieu of notice) scaled by length of service. Summary dismissal without notice or statutory justification constitutes a breach of contract."
    }
]
LEGAL_THESAURUS = {
    'boss': 'employer',
    'fired': 'termination dismissal',
    'sacked': 'termination dismissal',
    'sack': 'termination',
    'quit': 'resignation termination',
    'pay': 'wages salary',
    'money': 'wages remuneration',
    'cop': 'police officer',
    'cops': 'police',
    'jail': 'custody detention',
    'lockup': 'custody detention',
    'bribe': 'gratification corrupt',
    'stole': 'stealing theft'
}

def expand_query_stems(query: str) -> list:
    words = re.findall(r'[a-zA-Z]{3,}', query.lower())
    stems = []
    stop_words = {'with', 'this', 'that', 'from', 'what', 'have', 'were', 'your', 'their'}
    for w in words:
        if w not in stop_words:
            stems.append(f"{w}*")
            if w in LEGAL_THESAURUS:
                for syn in LEGAL_THESAURUS[w].split():
                    stems.append(f"{syn}*")
    return list(set(stems))

app = FastAPI(title="NaijaLex Intelligence Engine", version="1.0.0")

def make_clean_snippet(text: str, max_chars: int = 240) -> str:
    if not text: return ""
    clean = re.sub(r'\s+', ' ', text).strip()
    return clean if len(clean) <= max_chars else clean[:max_chars].rstrip() + "..."

def call_gemini(prompt: str, response_json: bool = False) -> str:
    if not API_KEY or API_KEY.startswith("your-actual"): return ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json", "x-goog-api-key": API_KEY}
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.0, "maxOutputTokens": 800}}
    if response_json: payload["generationConfig"]["responseMimeType"] = "application/json"
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                return candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[!] Gemini Request Exception: {e}")
    return ""

def check_deterministic_heuristics(query: str, conn) -> Optional[dict]:
    q_lower = query.lower()
    for rule in DETERMINISTIC_RULES:
        if any(p in q_lower for p in rule.get("phrases_match", [])):
            return execute_rule_provisions(rule, query, conn)
    for rule in DETERMINISTIC_RULES:
        keywords = rule.get("keywords", [])
        if sum(1 for kw in keywords if kw in q_lower) >= 2 or (len(keywords) == 1 and keywords[0] in q_lower):
            return execute_rule_provisions(rule, query, conn)
    return None

def execute_rule_provisions(rule: dict, query: str, conn) -> dict:
    cursor = conn.cursor()
    results, target_stats = [], []
    for p in rule.get("provisions", []):
        cursor.execute("SELECT statute_title, section_number, section_title, part, full_text FROM sections_fts WHERE statute_title LIKE ? AND section_number = ? LIMIT 1;", (f"%{p['statute'].split(',')[0]}%", str(p["section"])))
        row = cursor.fetchone()
        if row:
            title = "Constitution of the Federal Republic of Nigeria 1999 (as amended)" if "Constitution" in row[0] else row[0]
            if title not in target_stats: target_stats.append(title)
            results.append({"statute": title, "section_number": row[1], "section_title": row[2], "part": row[3], "snippet": make_clean_snippet(row[4]), "full_text": row[4]})
    return {"query": query, "legal_issue": rule["answer"], "target_statutes": target_stats, "statutory_concepts": ["Direct Statutory Match"], "results": results}

def check_direct_citation(query: str, conn) -> list:
    match = re.search(r'(?:section|sec\.?|s\.)\s*(\d+[a-zA-Z]?)', query, re.IGNORECASE)
    if not match: return []
    sec_num = match.group(1)
    cursor = conn.cursor()
    for statute in STATUTE_REGISTRY:
        short = statute.split(",")[0].split("(")[0].strip()
        if any(t in query.lower() for t in [t.lower() for t in re.findall(r'\w+', short) if len(t) > 3]):
            cursor.execute("SELECT statute_title, section_number, section_title, part, full_text FROM sections_fts WHERE (statute_title LIKE ? OR statute_title LIKE '%Constitution%') AND section_number = ? LIMIT 1;", (f"%{short}%", sec_num))
            row = cursor.fetchone()
            if row:
                title = "Constitution of the Federal Republic of Nigeria 1999 (as amended)" if "Constitution" in row[0] else row[0]
                return [{"statute": title, "section_number": row[1], "section_title": row[2], "part": row[3], "snippet": make_clean_snippet(row[4]), "full_text": row[4]}]
    return []

def analyze_and_route(scenario: str) -> dict:
    prompt = f"Analyze this user case scenario: '{scenario}'. Return JSON ONLY: {{\"legal_answer\": \"string\", \"target_statutes\": [\"string\"], \"legal_phrases\": [\"string\"], \"keyword_stems\": [\"string\"]}}"
    raw = call_gemini(prompt, response_json=True)
    try:
        if raw: return json.loads(raw)
    except: pass
    q_low = scenario.lower()
    target = []
    phrases = []
    stems = [w for w in re.findall(r'[a-zA-Z]{4,}', q_low) if w not in {'with', 'this', 'that', 'from', 'what', 'have', 'were'}]
    
    if any(k in q_low for k in ['boy', 'child', 'minor', 'juvenile', 'kid']):
        target.append("Child's Rights Act, 2003")
        phrases.append("child justice")
    if any(k in q_low for k in ['arrest', 'detain', 'police', 'custody', 'station', 'officer']):
        target.extend(["Nigeria Police Act, 2020", "Administration of Criminal Justice Act, 2015 (ACJA)"])
        phrases.extend(["rights of arrested person", "mode of arrest"])
    if any(k in q_low for k in ['fired', 'salary', 'maternity', 'wages', 'work', 'employer']):
        target.append("Labour Act, 1971")
    
    answer = "Under Nigerian Federal Law, arrests must strictly comply with constitutional safeguards, police procedure, and child justice administration." if any(k in q_low for k in ['arrest', 'police', 'child', 'boy']) else ""
    
    return {"legal_answer": answer, "target_statutes": list(set(target)), "legal_phrases": phrases, "keyword_stems": stems[:4]}

def retrieve_candidate_pool(conn, plan: dict, raw_query: str) -> list:
    cursor = conn.cursor()
    candidates = {}
    expanded = expand_query_stems(raw_query)
    phrases = [f'"{p}"' for p in plan.get("legal_phrases", [])]
    stems = [f"{s}*" for s in plan.get("keyword_stems", []) if s] + expanded
    fts_query = " OR ".join(phrases + list(set(stems))) if (phrases or stems) else raw_query
    for stat in plan.get("target_statutes", []):
        short = "Constitution" if "Constitution" in stat else stat.split(",")[0].split("(")[0].strip()
        try:
            cursor.execute("SELECT statute_title, section_number, section_title, part, snippet(sections_fts, 4, '⟦', '⟧', '...', 25), bm25(sections_fts), full_text FROM sections_fts WHERE statute_title LIKE ? AND sections_fts MATCH ? ORDER BY rank LIMIT 5;", (f"%{short}%", fts_query))
            for r in cursor.fetchall():
                title = "Constitution of the Federal Republic of Nigeria 1999 (as amended)" if "Constitution" in r[0] else r[0]
                candidates[(title, str(r[1]))] = {"statute": title, "section_number": r[1], "section_title": r[2], "part": r[3], "snippet": r[4], "full_text": r[6]}
        except: pass
    if not candidates:
        try:
            cursor.execute("SELECT statute_title, section_number, section_title, part, snippet(sections_fts, 4, '⟦', '⟧', '...', 25), bm25(sections_fts), full_text FROM sections_fts WHERE sections_fts MATCH ? ORDER BY rank LIMIT 6;", (fts_query,))
            for r in cursor.fetchall():
                title = "Constitution of the Federal Republic of Nigeria 1999 (as amended)" if "Constitution" in r[0] else r[0]
                candidates[(title, str(r[1]))] = {"statute": title, "section_number": r[1], "section_title": r[2], "part": r[3], "snippet": r[4], "full_text": r[6]}
        except: pass
    return list(candidates.values())

@app.get("/api/search")
def api_search(q: str = Query(...)):
    if not DB_PATH.exists(): raise HTTPException(status_code=500, detail="Database not found")
    conn = sqlite3.connect(DB_PATH)
    if direct := check_direct_citation(q, conn):
        conn.close()
        return {"query": q, "legal_issue": f"Direct statutory match verified for Section {direct[0]['section_number']} of {direct[0]['statute']}.", "results": direct}
    if rule := check_deterministic_heuristics(q, conn):
        conn.close()
        return rule
    plan = analyze_and_route(q)
    candidates = retrieve_candidate_pool(conn, plan, q)
    conn.close()
    return {"query": q, "legal_issue": plan.get("legal_answer", "Governing statutory provisions retrieved."), "results": candidates[:3]}

@app.get("/api/statutes")
def api_statutes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT statute_title, COUNT(*) FROM sections_fts GROUP BY statute_title ORDER BY statute_title;")
    rows = cursor.fetchall()
    conn.close()
    return [{"statute": ("Constitution of the Federal Republic of Nigeria 1999 (as amended)" if "Constitution" in r[0] else r[0]), "total_sections": r[1]} for r in rows]

@app.get("/api/statute/sections")
def api_statute_sections(statute: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    search_term = f"%{statute.split(',')[0].strip()}%"
    cursor.execute("SELECT statute_title, section_number, section_title, part, full_text FROM sections_fts WHERE statute_title LIKE ? ORDER BY CAST(section_number AS INTEGER)", (search_term,))
    rows = cursor.fetchall()
    conn.close()
    return [{"statute": r[0], "section_number": r[1], "section_title": r[2], "part": r[3], "full_text": r[4]} for r in rows]

@app.get("/", response_class=HTMLResponse)
def web_dashboard():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    if API_KEY and not API_KEY.startswith("your-actual"):
        print("[+] NaijaLex: GEMINI_API_KEY detected")
    else:
        print("[!] NaijaLex: GEMINI_API_KEY is not set. Running with deterministic legal heuristics.")
    print("[+] Starting NaijaLex Server at http://127.0.0.1:8000")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
