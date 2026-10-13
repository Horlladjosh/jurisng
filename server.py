import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", message=".*LibreSSL.*")

import os
import json
import sqlite3
import re
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv

# Load local environment configuration (.env)
load_dotenv()

DB_PATH = Path("data/nigerian_law.db")
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
FEEDBACK_RECIPIENT_EMAIL = os.environ.get("FEEDBACK_RECIPIENT_EMAIL", "").strip()
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "JurisNG Feedback <onboarding@resend.dev>").strip()

STATUTE_REGISTRY = [
    "Administration of Criminal Justice Act, 2015",
    "Child's Rights Act",
    "Companies Income Tax Act",
    "Companies and Allied Matters Act, 2020",
    "Constitution of the Federal Republic of Nigeria 1999 (as amended)",
    "Copyright Act, 2022",
    "Criminal Code Act",
    "Cybercrimes (Prohibition, Prevention, etc.) Act, 2015",
    "Cybercrimes (Prohibition, Prevention, etc) (Amendment) Act, 2024",
    "Electoral Act 2022",
    "Electricity Act, 2023",
    "Employees' Compensation Act, 2010",
    "Evidence Act, 2011",
    "Federal Competition and Consumer Protection Act, 2018",
    "Labour Act, 1971",
    "Land Use Act 1978",
    "Money Laundering (Prevention and Prohibition) Act, 2022",
    "National Health Act, 2014",
    "National Social Investment Programme Agency Act, 2023",
    "Nigeria Data Protection Act, 2023",
    "Nigeria Police Act, 2020",
    "Nigerian Law Reform Commission Act, 2022",
    "Penal Code (Northern States) Federal Provisions Act, 1960",
    "Personal Income Tax Act",
    "Petroleum Industry Act, 2021",
    "Proceeds of Crime (Recovery and Management) Act, 2022",
    "Students Loans (Access to Higher Education) Act, 2023",
    "Terrorism (Prevention and Prohibition) Act, 2022",
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
    words = re.findall(r'[a-zA-Z]{3,}', query.lower())
    stems = []
    stop_words = {'with', 'this', 'that', 'from', 'what', 'have', 'were', 'your', 'their', 'under', 'into'}
    for w in words:
        if w not in stop_words:
            stems.append(f'"{w}"')
            if w in LEGAL_THESAURUS:
                for syn in LEGAL_THESAURUS[w].split():
                    stems.append(f'"{syn}"')
    return list(set(stems))

app = FastAPI(
    title="JurisNG Statutory Intelligence API",
    version="1.0.0",
    description="""
### Nigerian Legal Intelligence & Statutory Retrieval API
JurisNG indexes 126 certified Federal Statutes and Official Gazettes (9,903 verified sections) across the Federal Republic of Nigeria.

---
**⚠️ LEGAL DISCLAIMER & TERMS OF USE:**
* **Not Legal Advice:** JurisNG is an automated statutory research tool and does NOT provide formal legal advice or representation.
* **No Attorney-Client Relationship:** Use of this API does not create a Legal Practitioner–Client relationship under the **Legal Practitioners Act (Cap. L11 LFN 2004)**.
* **Consult Counsel:** For specific disputes, active police matters, commercial contracts, or court litigation, always consult a licensed Legal Practitioner enrolled at the Supreme Court of Nigeria.
* **Public Domain:** Primary statutory texts are public government enactments indexed in compliance with the **Copyright Act, 2022**.
    """,
    terms_of_service="/terms"
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

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
    q_low = query.lower()
    
    cursor.execute("SELECT DISTINCT statute_title FROM sections_fts;")
    statutes = [r[0] for r in cursor.fetchall()]
    
    STATUTE_ALIASES = {
        "startup": "Nigeria Startup Act, 2022",
        "aviation": "Civil Aviation Act, 2022",
        "civil aviation": "Civil Aviation Act, 2022",
        "arcon": "Advertising Regulatory Council of Nigeria Act, 2022",
        "advertising": "Advertising Regulatory Council of Nigeria Act, 2022",
        "pharmacy": "Pharmacy Council of Nigeria (Establishment) Act, 2022",
        "pharmacist": "Pharmacy Council of Nigeria (Establishment) Act, 2022",
        "nimet": "Nigerian Meteorological Agency (Establishment) Act, 2022",
        "meteorological": "Nigerian Meteorological Agency (Establishment) Act, 2022",
        "rmrdc": "Raw Materials Research and Development Council Act, 2022",
        "raw materials": "Raw Materials Research and Development Council Act, 2022",
        "ncmd": "Nigerian Council for Management Development Act, 2022",
        "management development": "Nigerian Council for Management Development Act, 2022",
        "social work": "Chartered Institute of Social Work Practitioners (Establishment) Act, 2022",
        "north central": "North-Central Development Commission (Establishment) Act, 2024",
        "north-central": "North-Central Development Commission (Establishment) Act, 2024",
        "north west": "North-West Development Commission (Establishment) Act, 2025",
        "north-west": "North-West Development Commission (Establishment) Act, 2025",
        "south east": "South-East Development Commission (Establishment) Act, 2025",
        "south-east": "South-East Development Commission (Establishment) Act, 2025",
        "south west": "South-West Development Commission (Establishment) Act, 2025",
        "south-west": "South-West Development Commission (Establishment) Act, 2025",
        "south south": "South-South Development Commission (Establishment) Act, 2025",
        "south-south": "South-South Development Commission (Establishment) Act, 2025",
        "petroleum": "Petroleum Industry Act, 2021",
        "pia": "Petroleum Industry Act, 2021",
        "ndpa": "Nigeria Data Protection Act, 2023",
        "data protection": "Nigeria Data Protection Act, 2023",
        "electricity": "Electricity Act, 2023",
        "electoral": "Electoral Act 2022",
        "cama": "Companies and Allied Matters Act, 2020",
        "companies": "Companies and Allied Matters Act, 2020",
        "tax": "Personal Income Tax Act",
        "income tax": "Personal Income Tax Act",
        "cita": "Companies Income Tax Act",
        "pita": "Personal Income Tax Act",
        "vat": "Value Added Tax Act",
        "police": "Nigeria Police Act, 2020",
        "health": "National Health Act, 2014",
        "labour": "Labour Act, 1971",
        "evidence": "Evidence Act, 2011",
        "cybercrime": "Cybercrimes (Prohibition, Prevention, etc.) Act, 2015",
        "cybercrimes": "Cybercrimes (Prohibition, Prevention, etc.) Act, 2015",
        "criminal code": "Criminal Code Act",
        "penal code": "Penal Code (Northern States) Federal Provisions Act, 1960",
        "child": "Child's Rights Act",
        "children": "Child's Rights Act",
        "constitution": "Constitution of the Federal Republic of Nigeria 1999 (as amended)",
        "acct": "Administration of Criminal Justice Act, 2015",
        "acja": "Administration of Criminal Justice Act, 2015",
        "fccpa": "Federal Competition and Consumer Protection Act, 2018",
        "competition": "Federal Competition and Consumer Protection Act, 2018",
        "money laundering": "Money Laundering (Prevention and Prohibition) Act, 2022",
        "poca": "Proceeds of Crime (Recovery and Management) Act, 2022",
        "proceeds of crime": "Proceeds of Crime (Recovery and Management) Act, 2022",
        "terrorism": "Terrorism (Prevention and Prohibition) Act, 2022",
        "student loan": "Students Loans (Access to Higher Education) Act, 2023",
        "student loans": "Students Loans (Access to Higher Education) Act, 2023",
        "nlrc": "Nigerian Law Reform Commission Act, 2022",
        "law reform": "Nigerian Law Reform Commission Act, 2022",
        "nsipa": "National Social Investment Programme Agency Act, 2023",
        "social investment": "National Social Investment Programme Agency Act, 2023",
        "efcc": "Economic and Financial Crimes Commission (Establishment, etc.) Act, 2004",
        "cbn": "Central Bank of Nigeria (Establishment) Act, 2007",
        "central bank": "Central Bank of Nigeria (Establishment) Act, 2007",
        "advance fee": "Advance Fee Fraud and Other Fraud Related Offences Act, 2006",
        "fraud": "Advance Fee Fraud and Other Fraud Related Offences Act, 2006",
        "nitda": "National Information Technology Development Agency Act, 2007",
        "cheques": "Dishonoured Cheques (Offences) Act, 1977",
        "dishonoured": "Dishonoured Cheques (Offences) Act, 1977",
        "acts authentication": "Acts Authentication Act, 1961",
        "authentication": "Acts Authentication Act, 1961",
        "public holidays": "Public Holidays Act, 1979",
        "holidays": "Public Holidays Act, 1979",
        "foreign judgments": "Foreign Judgments (Reciprocal Enforcement) Act, 1960",
        "admiralty": "Admiralty Jurisdiction Act, 1991",
        "maritime": "Admiralty Jurisdiction Act, 1991",
        "trade marks": "Trade Marks Act, 1967",
        "trademarks": "Trade Marks Act, 1967",
        "trademark": "Trade Marks Act, 1967",
        "patents": "Patents and Designs Act, 1971",
        "designs": "Patents and Designs Act, 1971",
        "patent": "Patents and Designs Act, 1971",
        "hire purchase": "Hire-Purchase Act, 1965",
        "hire-purchase": "Hire-Purchase Act, 1965",
        "oaths": "Oaths Act, 1963",
        "oath": "Oaths Act, 1963",
        "trade disputes": "Trade Disputes Act, 1976",
        "disputes": "Trade Disputes Act, 1976",
        "icpc": "Corrupt Practices and Other Related Offences Act, 2000",
        "corrupt practices": "Corrupt Practices and Other Related Offences Act, 2000",
        "stamp duties": "Stamp Duties Act, 1939",
        "stamp duty": "Stamp Duties Act, 1939",
        "immigration": "Immigration Act, 1963",
        "ndlea": "National Drug Law Enforcement Agency Act, 1989",
        "drug law": "National Drug Law Enforcement Agency Act, 1989",
        "trade unions": "Trade Unions Act, 1973",
        "trade union": "Trade Unions Act, 1973",
        "arbitration": "Arbitration and Conciliation Act, 1988",
        "conciliation": "Arbitration and Conciliation Act, 1988",
        "nipc": "Nigerian Investment Promotion Commission Act, 1995",
        "investment promotion": "Nigerian Investment Promotion Commission Act, 1995",
        "nhrc": "National Human Rights Commission Act, 1995",
        "human rights": "National Human Rights Commission Act, 1995",
        "customs": "Customs and Excise Management Act, 1958",
        "cema": "Customs and Excise Management Act, 1958",
        "excise": "Customs and Excise Management Act, 1958"
    }
    
    # Check aliases first
    for alias, target_title in sorted(STATUTE_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in q_low:
            cursor.execute("SELECT statute_title, section_number, section_title, part, full_text FROM sections_fts WHERE (statute_title = ? OR statute_title LIKE ?) AND section_number = ? LIMIT 1;", (target_title, f"%{alias}%", sec_num))
            row = cursor.fetchone()
            if row:
                title = "Constitution of the Federal Republic of Nigeria 1999 (as amended)" if "Constitution" in row[0] else row[0]
                return [{"statute": title, "section_number": row[1], "section_title": row[2], "part": row[3], "snippet": make_clean_snippet(row[4]), "full_text": row[4]}]
                
    scored = []
    stop_tokens = {'act', 'and', 'the', 'for', 'etc', 'federal', 'republic', 'nigeria', 'establishment'}
    for st in statutes:
        tokens = [t.lower() for t in re.findall(r'[a-zA-Z]{3,}', st) if t.lower() not in stop_tokens]
        score = sum(len(t) * 2 if t in q_low else 0 for t in tokens)
        if score > 0:
            scored.append((score, st))
            
    scored.sort(key=lambda x: x[0], reverse=True)
    for _, st in scored:
        cursor.execute("SELECT statute_title, section_number, section_title, part, full_text FROM sections_fts WHERE statute_title = ? AND section_number = ? LIMIT 1;", (st, sec_num))
        row = cursor.fetchone()
        if row:
            title = "Constitution of the Federal Republic of Nigeria 1999 (as amended)" if "Constitution" in row[0] else row[0]
            return [{"statute": title, "section_number": row[1], "section_title": row[2], "part": row[3], "snippet": make_clean_snippet(row[4]), "full_text": row[4]}]
            
    cursor.execute("SELECT statute_title, section_number, section_title, part, full_text FROM sections_fts WHERE statute_title LIKE '%Constitution%' AND section_number = ? LIMIT 1;", (sec_num,))
    row = cursor.fetchone()
    if row:
        return [{"statute": "Constitution of the Federal Republic of Nigeria 1999 (as amended)", "section_number": row[1], "section_title": row[2], "part": row[3], "snippet": make_clean_snippet(row[4]), "full_text": row[4]}]
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
    stems = [w for w in re.findall(r'[a-zA-Z]{4,}', q_low) if w not in {'with', 'this', 'that', 'from', 'what', 'have', 'were'}]
    
    if any(k in q_low for k in ['boy', 'child', 'minor', 'juvenile', 'kid']):
        target.append("Child's Rights Act, 2003")
        phrases.append("child justice")
    if any(k in q_low for k in ['arrest', 'detain', 'police', 'custody', 'station', 'officer']):
        target.extend(["Nigeria Police Act, 2020", "Administration of Criminal Justice Act, 2015"])
        phrases.extend(["rights of arrested person", "mode of arrest"])
    if any(k in q_low for k in ['fired', 'salary', 'maternity', 'wages', 'work', 'employer']):
        target.append("Labour Act, 1971")
    
    answer = "Under Nigerian Federal Law, arrests must strictly comply with constitutional safeguards, police procedure, and child justice administration." if any(k in q_low for k in ['arrest', 'police', 'child', 'boy']) else ""
    
    return {"legal_answer": answer, "target_statutes": list(set(target)), "legal_phrases": phrases, "keyword_stems": stems[:6]}

def retrieve_candidate_pool(conn, plan: dict, raw_query: str) -> list:
    cursor = conn.cursor()
    candidates = {}
    expanded = expand_query_stems(raw_query)
    phrases = [f'"{p}"' for p in plan.get("legal_phrases", []) if p]
    terms = list(set(phrases + expanded))
    fts_query = " OR ".join(terms) if terms else f'"{raw_query}"'
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

@app.get("/api/disclaimer")
def api_disclaimer():
    return {
        "platform": "JurisNG Statutory Intelligence Engine",
        "jurisdiction": "Federal Republic of Nigeria",
        "disclaimer_summary": "Statutory information and legal research tool for educational and informational purposes only. Not formal legal advice.",
        "key_terms": [
            "JurisNG is not a law firm and does not provide legal representation or counsel.",
            "Use of this platform does not create a Legal Practitioner–Client relationship under the Legal Practitioners Act (Cap. L11 LFN 2004).",
            "Users must consult a licensed Legal Practitioner in Nigeria for specific legal matters or litigation.",
            "Primary statutory materials are public domain government enactments under the Copyright Act, 2022.",
            "JurisNG disclaims all liability for actions taken solely on automated outputs."
        ],
        "full_terms_url": "/terms"
    }

@app.get("/terms", response_class=HTMLResponse)
def terms_page():
    terms_file = Path("TERMS_AND_DISCLAIMER.md")
    content = terms_file.read_text(encoding="utf-8") if terms_file.exists() else "Terms and conditions."
    # Render clean HTML version
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JurisNG | Terms of Use & Legal Disclaimer</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
            .font-editorial {{ font-family: 'Newsreader', Georgia, serif; }}
        </style>
    </head>
    <body class="bg-[#fbfaf6] text-[#171513] min-h-screen py-10 px-4">
        <div class="max-w-2xl mx-auto bg-white border border-[#e8e2d4] rounded-2xl p-8 shadow-sm space-y-6">
            <div class="border-b border-[#e8e2d4] pb-4 flex items-center justify-between">
                <div>
                    <h1 class="text-2xl font-editorial font-bold text-[#171513]">Legal Disclaimer & Terms of Use</h1>
                    <p class="text-xs text-[#0d533f] font-semibold uppercase tracking-wider mt-1">JurisNG • Federal Republic of Nigeria</p>
                </div>
                <a href="/" class="text-xs bg-[#f4f0e8] hover:bg-[#e8e2d4] text-[#171513] font-semibold px-3.5 py-2 rounded-md transition border border-[#e8e2d4]">← Back to App</a>
            </div>
            <div class="space-y-4 leading-relaxed text-sm text-[#38342f] font-editorial text-base">
                <div class="p-4 bg-[#fbf3e0] border border-[#f5e3bc] rounded-xl text-[#7d5414] text-xs font-sans font-medium">
                    ⚠️ <strong>IMPORTANT NOTICE:</strong> JurisNG provides automated statutory search and research tooling for informational purposes. It does NOT constitute formal legal advice or create a lawyer-client relationship under the Legal Practitioners Act (Cap. L11).
                </div>
                <h3 class="font-bold text-[#171513] text-base font-sans">1. Not Legal Advice</h3>
                <p>JurisNG is not a law firm. Using this engine does not establish an attorney-client relationship under the <strong>Legal Practitioners Act (Cap. L11 LFN 2004)</strong>.</p>
                
                <h3 class="font-bold text-[#171513] text-base font-sans">2. Consult a Licensed Nigerian Legal Practitioner</h3>
                <p>Legal outcomes depend on specific facts, court rules, and judicial precedents. For active police investigations, court cases, commercial contracts, or criminal charges, always consult a licensed Legal Practitioner enrolled at the Supreme Court of Nigeria.</p>

                <h3 class="font-bold text-[#171513] text-base font-sans">3. Public Domain Government Works</h3>
                <p>All primary statutory texts and Official Gazettes are public government enactments indexed in accordance with the <strong>Copyright Act, 2022</strong>.</p>

                <h3 class="font-bold text-[#171513] text-base font-sans">4. Limitation of Liability</h3>
                <p>To the fullest extent permitted by Nigerian law, JurisNG accepts no liability for decisions made solely in reliance on automated search outputs.</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/api/watcher/status")
def api_watcher_status():
    from engine.legislative_watcher import load_watcher_state, get_current_indexed_statutes
    state = load_watcher_state()
    indexed = get_current_indexed_statutes()
    return {
        "status": "active",
        "last_checked": state.get("last_checked"),
        "total_checks": state.get("total_checks", 0),
        "indexed_statutes_count": len(indexed),
        "known_remote_acts_count": len(state.get("known_remote_acts", [])),
        "pending_alerts": state.get("pending_alerts", [])[-5:]
    }

@app.post("/api/watcher/check")
def api_watcher_check():
    from engine.legislative_watcher import run_legislative_check
    report = run_legislative_check(notify=True)
    return report

class FeedbackPayload(BaseModel):
    email: str
    message: str
    category: Optional[str] = "Bug Report"
    name: Optional[str] = ""
    statute_reference: Optional[str] = ""
    bot_check: Optional[str] = ""

FEEDBACK_RATE_LIMIT = {}

def init_feedback_table():
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT NOT NULL,
            category TEXT NOT NULL,
            statute_reference TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email_sent INTEGER DEFAULT 0,
            resend_id TEXT,
            error_log TEXT
        );
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Warning: Could not initialize feedback table: {e}")

# Initialize table on startup
init_feedback_table()

def send_resend_email(payload: FeedbackPayload) -> Tuple[bool, str]:
    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    recipient = os.environ.get("FEEDBACK_RECIPIENT_EMAIL", "").strip()
    from_addr = os.environ.get("RESEND_FROM_EMAIL", "JurisNG Feedback <onboarding@resend.dev>").strip()

    if not resend_key:
        return False, "RESEND_API_KEY is not configured in .env"
    if not recipient:
        return False, "FEEDBACK_RECIPIENT_EMAIL is not configured in .env"

    statute_part = f" [{payload.statute_reference}]" if payload.statute_reference else ""
    sender_name = payload.name.strip() if payload.name else "Anonymous Researcher"
    subject = f"[JurisNG {payload.category}]{statute_part} Query from {sender_name}"

    statute_row = ""
    if payload.statute_reference:
        statute_row = f"""
        <tr>
            <td style="padding: 9px 0; color: #524d45; font-weight: 600; width: 140px; font-size: 13px;">Statute / Section:</td>
            <td style="padding: 9px 0; color: #171513; font-weight: 700; font-size: 13px;">{payload.statute_reference}</td>
        </tr>
        """

    formatted_time = datetime.now().strftime("%d %b %Y, %I:%M %p")
    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8f7f4; padding: 24px; margin: 0; color: #171513;">
    <div style="max-width: 580px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e4dfd5; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
        <div style="background-color: #1b4332; padding: 22px 24px; color: #ffffff;">
            <div style="font-size: 10px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #a7f3d0; margin-bottom: 4px; font-family: monospace;">JurisNG • Statutory Intelligence</div>
            <h1 style="margin: 0; font-size: 19px; font-weight: 700; letter-spacing: -0.2px;">New User Query & Bug Report</h1>
        </div>
        
        <div style="padding: 24px;">
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="padding: 9px 0; color: #524d45; font-weight: 600; width: 140px; font-size: 13px;">Topic / Category:</td>
                    <td style="padding: 9px 0; color: #1b4332; font-weight: 700; font-size: 13px;">{payload.category}</td>
                </tr>
                <tr>
                    <td style="padding: 9px 0; color: #524d45; font-weight: 600; font-size: 13px;">Submitted By:</td>
                    <td style="padding: 9px 0; color: #171513; font-size: 13px;"><strong>{sender_name}</strong> &lt;<a href="mailto:{payload.email}" style="color: #1b4332; text-decoration: underline;">{payload.email}</a>&gt;</td>
                </tr>
                {statute_row}
                <tr>
                    <td style="padding: 9px 0; color: #524d45; font-weight: 600; font-size: 13px;">Submission Time:</td>
                    <td style="padding: 9px 0; color: #857d72; font-size: 12px; font-family: monospace;">{formatted_time} (WAT)</td>
                </tr>
            </table>

            <div style="background-color: #f8f7f4; border: 1px solid #e4dfd5; border-radius: 8px; padding: 18px; margin-bottom: 22px;">
                <div style="font-size: 10px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; color: #857d72; margin-bottom: 8px; font-family: monospace;">Message / Bug Details</div>
                <div style="font-size: 14px; line-height: 1.6; color: #171513; white-space: pre-wrap;">{payload.message}</div>
            </div>

            <div style="border-top: 1px solid #e4dfd5; padding-top: 16px; font-size: 12px; color: #857d72; line-height: 1.5;">
                💡 <strong>Reply-To Configured:</strong> You can click <strong>Reply</strong> in your email client to respond directly to <code>{payload.email}</code>.
            </div>
        </div>
    </div>
</body>
</html>"""

    headers = {
        "Authorization": f"Bearer {resend_key}",
        "Content-Type": "application/json"
    }

    payload_data = {
        "from": from_addr,
        "to": [recipient],
        "reply_to": payload.email,
        "subject": subject,
        "html": html_content
    }

    try:
        resp = requests.post("https://api.resend.com/emails", json=payload_data, headers=headers, timeout=12)
        if resp.status_code in [200, 201]:
            data = resp.json()
            return True, data.get("id", "delivered")
        else:
            err_text = resp.text
            # If domain is not yet verified on Resend, automatically fallback to account email so notifications are never dropped
            if resp.status_code == 403 and "triplefourmedia@gmail.com" in err_text:
                payload_data["to"] = ["triplefourmedia@gmail.com"]
                fallback_resp = requests.post("https://api.resend.com/emails", json=payload_data, headers=headers, timeout=12)
                if fallback_resp.status_code in [200, 201]:
                    data = fallback_resp.json()
                    return True, data.get("id", "delivered_fallback")
            return False, f"Resend API HTTP {resp.status_code}: {err_text}"
    except Exception as e:
        return False, str(e)

@app.post("/api/feedback")
def api_submit_feedback(payload: FeedbackPayload, request: Request):
    # 0. Anti-bot honeypot check: If automated bot filled the hidden honeypot field, silently succeed without saving
    if payload.bot_check and payload.bot_check.strip():
        return {"success": True, "message": "Thank you! Your report has been submitted successfully."}

    # IP Rate limit: max 5 submissions per 10 minutes per IP address
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown").split(",")[0].strip()
    now = time.time()
    recent = [t for t in FEEDBACK_RATE_LIMIT.get(client_ip, []) if now - t < 600]
    if len(recent) >= 5:
        raise HTTPException(status_code=429, detail="Too many submissions from your network. Please wait a few minutes before submitting again.")
    recent.append(now)
    FEEDBACK_RATE_LIMIT[client_ip] = recent

    cleaned_email = payload.email.strip()
    cleaned_msg = payload.message.strip()

    if not cleaned_email or "@" not in cleaned_email or "." not in cleaned_email:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")
    if not cleaned_msg:
        raise HTTPException(status_code=400, detail="Please enter message or bug details.")

    # 1. Always record locally in SQLite first so no query is ever lost
    submission_id = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO feedback_submissions (name, email, category, statute_reference, message)
        VALUES (?, ?, ?, ?, ?)
        """, (payload.name.strip(), cleaned_email, payload.category, (payload.statute_reference or "").strip(), cleaned_msg))
        submission_id = cursor.lastrowid
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Warning: Could not save feedback to SQLite: {e}")

    # 2. Dispatch via Resend
    email_sent, resend_result = send_resend_email(payload)

    # 3. Update SQLite record with delivery result
    if submission_id:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            if email_sent:
                cursor.execute("UPDATE feedback_submissions SET email_sent = 1, resend_id = ? WHERE id = ?", (resend_result, submission_id))
            else:
                cursor.execute("UPDATE feedback_submissions SET email_sent = 0, error_log = ? WHERE id = ?", (resend_result, submission_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Warning: Could not update feedback delivery record: {e}")

    message_response = "Thank you! Your report has been submitted successfully."
    if not email_sent:
        print(f"[*] Feedback logged locally. Resend dispatch note: {resend_result}")

    return {
        "success": True,
        "message": message_response,
        "email_sent": email_sent,
        "submission_id": submission_id
    }

@app.get("/favicon.ico")
@app.get("/favicon.svg")
def get_favicon():
    if os.path.exists("favicon.svg"):
        return FileResponse("favicon.svg", media_type="image/svg+xml")
    return Response(status_code=404)

@app.get("/og-image.png")
def get_og_image():
    if os.path.exists("og-image.png"):
        return FileResponse("og-image.png", media_type="image/png")
    return Response(status_code=404)

@app.get("/robots.txt", response_class=Response)
def get_robots():
    content = "User-agent: *\nAllow: /\nSitemap: https://jurisng.horlladjosh.com/sitemap.xml\n"
    return Response(content=content, media_type="text/plain")

@app.get("/sitemap.xml", response_class=Response)
def get_sitemap():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://jurisng.horlladjosh.com/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://jurisng.horlladjosh.com/terms</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>"""
    return Response(content=content, media_type="application/xml")

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def web_dashboard():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    if API_KEY and not API_KEY.startswith("your-actual"):
        print("[+] JurisNG: GEMINI_API_KEY detected")
    else:
        print("[!] JurisNG: GEMINI_API_KEY is not set. Running with deterministic legal heuristics.")
    print("[+] Starting JurisNG Server at http://127.0.0.1:8000")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
