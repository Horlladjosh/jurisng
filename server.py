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
JurisNG indexes 128 certified Federal Statutes and Official Gazettes (9,959 verified sections) across the Federal Republic of Nigeria.

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

QUERY_CACHE = {}
QUOTA_COOLDOWN_UNTIL = 0.0

def call_gemini(prompt: str, response_json: bool = False) -> str:
    global QUOTA_COOLDOWN_UNTIL
    if not API_KEY or API_KEY.startswith("your-actual"): return ""
    if time.time() < QUOTA_COOLDOWN_UNTIL:
        return ""
        
    cache_key = f"{response_json}:{prompt.strip()}"
    if cache_key in QUERY_CACHE:
        return QUERY_CACHE[cache_key]
        
    headers = {"Content-Type": "application/json", "x-goog-api-key": API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048
        }
    }
    if response_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"
        
    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=6)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        ans = parts[0]["text"].strip()
                        if ans:
                            QUERY_CACHE[cache_key] = ans
                            return ans
            elif res.status_code == 429:
                QUOTA_COOLDOWN_UNTIL = time.time() + 60.0
                break
            elif res.status_code == 503:
                continue
        except Exception:
            continue
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

STOP_WORDS = {
    'can', 'could', 'what', 'is', 'are', 'the', 'for', 'in', 'to', 'my', 'without', 
    'under', 'law', 'nigeria', 'nigerian', 'does', 'have', 'has', 'please', 'tell', 
    'me', 'about', 'and', 'with', 'from', 'a', 'an', 'that', 'this', 'there', 'who', 
    'whom', 'whose', 'why', 'when', 'where', 'how', 'any', 'all', 'you', 'your', 'be',
    'which', 'should', 'would', 'will', 'say', 'says', 'into', 'over', 'been'
}

PERIPHERAL_STATUTES = {
    'South-East Dev Comm Act', 'South-West Dev Comm Act', 'North-Central Dev Comm Act', 
    'North-West Dev Comm Act', 'South-South Dev Comm Act', 'NIMET Act', 'RMRDC Act', 
    'NCMD Act', 'Social Work Practitioners Act', 'Acts Authentication Act', 'Treaties Procedure Act'
}

LEGAL_DOMAINS = [
    {
        'id': 'banking_finance_freezing',
        'keywords': ['freeze', 'freezing', 'frozen', 'bank account', 'post no debit', 'pnd', 'bvn', 'bank', 'banks', 'bofia', 'financial institution', 'cbn'],
        'target_statutes': ['EFCC Act', 'Money Laundering (Prevention and Prohibition) Act, 2022', 'BOFIA', 'Constitution of the Federal Republic of Nigeria 1999 (as amended)'],
        'primary_terms': ['freezing order', 'bank account', 'freeze', 'surveillance of bank accounts', 'freezing order on banks'],
        'determination': "Under Nigerian law, law enforcement agencies (such as the Police, EFCC, or ICPC) lack legal authority to unilaterally freeze a citizen's bank account or place a 'Post-No-Debit' (PND) without a valid ex-parte order granted by a court of competent jurisdiction upon sworn affidavit showing reasonable suspicion of financial crimes (EFCC Act s. 34; Money Laundering Act s. 15). Unlawful account freezing violates the constitutional right to property under Section 44 of the 1999 Constitution."
    },
    {
        'id': 'theft_stealing_robbery',
        'keywords': ['steal', 'stealing', 'stole', 'theft', 'thief', 'robbery', 'shoplifting', 'pickpocket', 'penalty for stealing', 'punishment for stealing', 'stolen property'],
        'target_statutes': ['Criminal Code Act', 'Penal Code (Northern States) Federal Provisions Act, 1960'],
        'primary_terms': ['punishment of stealing', 'definition of stealing', 'stealing', 'theft', 'stolen'],
        'determination': "Under Nigerian criminal jurisprudence (Criminal Code Act ss. 383 & 390 in Southern States, and Penal Code in Northern States), a person who fraudulently takes or converts another person's property commits the offence of stealing. The general punishment for stealing under Section 390 of the Criminal Code is imprisonment for three years, with aggravated penalties (up to 7 or 14 years) where the theft involves employers, public servants, or high-value testamentary assets."
    },
    {
        'id': 'family_divorce_custody',
        'keywords': [
            'divorce', 'custody', 'child custody', 'dissolution of marriage', 'maintenance', 
            'alimony', 'matrimonial', 'separation', 'child support', 'wife custody', 
            'father custody', 'marriage', 'marry', 'marriage registry', 'marriage certificate', 
            'celebration of marriage', 'licensed place of worship', 'court wedding', 'bigamy', 
            'caveat', 'banns of marriage', 'special licence'
        ],
        'target_statutes': ['Marriage Act', 'Matrimonial Causes Act', "Child's Rights Act"],
        'primary_terms': [
            'celebration of marriage', 'marriage in place of worship', 'caveat', 
            'marriage certificate', 'bigamy', 'powers of court in custody', 
            'ground for dissolution of marriage', 'custody', 'dissolution of marriage', 
            'welfare of children', 'paramount consideration'
        ],
        'determination': "Under the Marriage Act (Cap. M6 LFN 2004), a statutory marriage in Nigeria must be celebrated in a registered registrar's office or a licensed place of worship after due notice or grant of special licence, with issuance of a certified certificate of marriage; contracting a second marriage while married under the Act constitutes criminal bigamy. For dissolution of marriage, Section 15 of the Matrimonial Causes Act requires establishing that the marriage has broken down irretrievably. In all proceedings concerning child custody, guardianship, or maintenance (Section 71 of the Matrimonial Causes Act and Section 1 of the Child's Rights Act), Nigerian courts are statutorily mandated to treat the best interests and welfare of the child as the paramount consideration."
    },
    {
        'id': 'labour_employment_wages',
        'keywords': ['boss', 'sack', 'sacked', 'fire', 'fired', 'dismiss', 'dismissal', 'salary', 'wages', 'unpaid', 'employment', 'severance', 'resignation', 'redundancy', 'worker', 'contract of employment'],
        'target_statutes': ['Labour Act, 1971', "Employees' Compensation Act, 2010"],
        'primary_terms': ['termination of contracts by notice', 'contracts general', 'written particulars of terms of employment', 'wages', 'redundancy', 'maternity leave'],
        'determination': "Under Section 11 of the Labour Act 1971, contracts of employment may only be terminated by giving statutory notice or payment in lieu of notice proportional to tenure. Furthermore, Section 5 strictly prohibits arbitrary salary deductions without formal consent or statutory authorization, and Section 54 renders dismissal during maternity leave null and void."
    },
    {
        'id': 'landlord_tenant_premises',
        'keywords': ['landlord', 'tenant', 'evict', 'eviction', 'quit notice', 'notice to quit', 'rent', 'tenant rent', 'premises', 'pack out', 'throw out belongings', 'lock tenant'],
        'target_statutes': ['Constitution of the Federal Republic of Nigeria 1999 (as amended)', 'Land Use Act 1978', 'Sheriffs and Civil Process Act'],
        'primary_terms': ['notice to quit', 'recovery of premises', 'possession', 'execution of warrants of possession', 'right to property'],
        'determination': "Under Nigerian law, self-help by a landlord (including changing door locks, disconnecting utilities, or forcibly ejecting a tenant) is illegal and constitutes a civil wrong and trespass. A landlord must strictly follow due process: serving a statutory Notice to Quit, followed by a 7-day Notice of Owner's Intention to Apply to Recover Possession, and securing a formal Judgment and Warrant of Possession executed only by court bailiffs/sheriffs."
    },
    {
        'id': 'police_powers_arrest_search',
        'keywords': ['police arrest', 'arrested without warrant', 'search phone', 'search without warrant', 'illegal arrest', 'station bail', 'bail is free', 'detained more than', 'detention without court', 'handcuff', 'torture', 'police officer', 'police station', 'suspect'],
        'target_statutes': ['Nigeria Police Act, 2020', 'Administration of Criminal Justice Act, 2015', 'Constitution of the Federal Republic of Nigeria 1999 (as amended)'],
        'primary_terms': ['rights of arrested person', 'mode of arrest', 'release on bail', 'search of arrested suspect', 'right to personal liberty'],
        'determination': "Under Section 35 of the 1999 Constitution, Section 6 of ACJA 2015, and Section 35 of the Nigeria Police Act 2020, an arrested citizen has the constitutional right to remain silent, consult legal counsel immediately, and receive free bail where the offence is bailable. Section 32 of the Police Act expressly prohibits arrests in civil or contractual debt disputes, and searches of personal phones or premises require lawful reasonable suspicion or a valid search warrant."
    },
    {
        'id': 'corporate_cac_registration',
        'keywords': ['register company', 'register a company', 'register business', 'cac', 'incorporation', 'form a company', 'share capital', 'directors', 'shareholders', 'annual returns', 'company formation', 'company', 'companies', 'register'],
        'target_statutes': ['Companies and Allied Matters Act, 2020'],
        'primary_terms': ['right to form a company', 'registration documents', 'registration', 'incorporation', 'formation of company'],
        'determination': "Under Section 18 of the Companies and Allied Matters Act (CAMA) 2020, one or more persons may form and incorporate a private company with the Corporate Affairs Commission (CAC). CAMA 2020 permits single-member companies and removes mandatory common seals, requiring electronic submission of articles, identity particulars of directors, and compliance verification under Section 36."
    },
    {
        'id': 'intellectual_property_copyright',
        'keywords': ['copyright', 'song', 'music', 'album', 'pirated', 'infringement', 'film', 'plagiarism', 'trademark', 'patent', 'counterfeit', 'intellectual property'],
        'target_statutes': ['Copyright Act, 2022', 'Trade Marks Act', 'Patents and Designs Act'],
        'primary_terms': ['infringement of copyright', 'action for infringement', 'criminal liability', 'works eligible for copyright'],
        'determination': "Under Sections 36 and 37 of the Copyright Act 2022, unauthorized reproduction, distribution, broadcast, or commercial exploitation of eligible artistic, musical, or audiovisual works constitutes actionable infringement. The copyright owner is entitled to damages, injunctions, and accounting for profits, while commercial piracy carries severe criminal liability under Section 44."
    },
    {
        'id': 'cybercrime_fraud_data',
        'keywords': ['cybercrime', 'hack', 'hacking', 'online fraud', 'phishing', 'scam', 'impersonation', 'cyberstalking', 'data protection', 'privacy breach', 'defraud'],
        'target_statutes': ['Cybercrimes (Prohibition, Prevention, etc.) Act, 2015', 'Cybercrimes (Prohibition, Prevention, etc) (Amendment) Act, 2024', 'Nigeria Data Protection Act, 2023', 'Advance Fee Fraud Act'],
        'primary_terms': ['identity theft', 'cyberstalking', 'computer systems', 'data subject rights', 'advance fee fraud'],
        'determination': "Under Section 22 and Section 24 of the Cybercrimes Act 2015 (as amended 2024), cyber harassment, unauthorized computer system access, identity theft, and fraudulent electronic transmissions carry stringent terms of imprisonment. Furthermore, the Nigeria Data Protection Act 2023 imposes civil and regulatory penalties for unlawful processing of citizen personal data."
    },
    {
        'id': 'corruption_bribery_extortion',
        'keywords': ['bribe', 'bribery', 'extortion', 'checkpoint bribe', 'kickback', 'corrupt officer', 'gratification', 'corrupt practice', 'demand money officer', 'icpc'],
        'target_statutes': ['Corrupt Practices (ICPC) Act', 'Nigeria Police Act, 2020', 'Code of Conduct Act', 'Criminal Code Act'],
        'primary_terms': ['gratification by an official', 'corrupt demand', 'bribery of public officer', 'extortion'],
        'determination': "Under Sections 12, 14, and 21 of the Corrupt Practices and Other Related Offences Act (ICPC Act) and Section 98 of the Criminal Code, demanding or accepting bribes or gratification by a public or police officer is a corrupt felony punishable by up to 7 years imprisonment. Section 91 of the Police Act 2020 additionally provides for summary disciplinary dismissal and criminal prosecution."
    },
    {
        'id': 'consumer_protection',
        'keywords': ['fake product', 'damaged goods', 'refuse refund', 'consumer rights', 'fccpc', 'misleading advertisement', 'expired food', 'substandard goods', 'consumer protection'],
        'target_statutes': ['Federal Competition and Consumer Protection Act, 2018'],
        'primary_terms': ['consumer rights', 'misleading representations', 'liability for defective goods', 'refund', 'unfair trade'],
        'determination': "Under the Federal Competition and Consumer Protection Act (FCCPA) 2018, consumers possess an enforceable statutory right to goods of merchantable quality, honest labeling, and immediate refund or replacement for defective products. Sections 130 and 136 strictly prohibit unfair trade practices and misleading representations."
    },
    {
        'id': 'taxation_revenue',
        'keywords': ['tax', 'taxes', 'personal income tax', 'paye', 'company income tax', 'vat', 'tax evasion', 'firs', 'withholding tax', 'stamp duty'],
        'target_statutes': ['Personal Income Tax Act', 'Companies Income Tax Act', 'Value Added Tax Act', 'Stamp Duties Act'],
        'primary_terms': ['charge of tax', 'deduction of tax', 'payment of tax', 'penalties'],
        'determination': "Federal and State tax administration in Nigeria is governed by the Personal Income Tax Act (PITA for individuals/PAYE), Companies Income Tax Act (CITA for corporate profits), and the Value Added Tax Act. Arbitrary or double taxation is prohibited, and tax assessments must strictly adhere to statutory notices and appeal tribunals."
    },
    {
        'id': 'electoral_law',
        'keywords': ['election', 'vote', 'voters card', 'bvas', 'inec', 'rigging', 'polling unit', 'electoral offence', 'presidential election', 'gubernatorial election'],
        'target_statutes': ['Electoral Act 2022'],
        'primary_terms': ['voters card', 'accreditation of voters', 'counting of votes', 'offences in relation to voting'],
        'determination': "Electoral administration and voting procedures in Nigeria are governed by the Electoral Act 2022. Section 47 mandates electronic voter accreditation (BVAS), and Part VII establishes severe criminal penalties (fines and imprisonment) for electoral offences, vote buying, tampering with ballot boxes, or falsification of results."
    },
    {
        'id': 'fundamental_human_rights',
        'keywords': ['human rights', 'fundamental rights', 'freedom of speech', 'freedom of expression', 'protest', 'peaceful assembly', 'freedom of religion', 'discrimination', 'right to life', 'unlawful detention'],
        'target_statutes': ['Constitution of the Federal Republic of Nigeria 1999 (as amended)', 'National Human Rights Commission Act'],
        'primary_terms': ['right to personal liberty', 'right to fair hearing', 'right to freedom of expression and the press', 'right to peaceful assembly and association', 'right to freedom of thought, conscience and religion'],
        'determination': "Chapter IV (Sections 33 to 46) of the 1999 Constitution of the Federal Republic of Nigeria guarantees the fundamental human rights of every citizen, including personal liberty (s. 35), fair hearing (s. 36), privacy (s. 37), freedom of expression (s. 39), and peaceful assembly (s. 40). Any infringement is directly actionable before the High Court under the Fundamental Rights (Enforcement Procedure) Rules."
    },
    {
        'id': 'pension_retirement',
        'keywords': ['pension', 'rsa', 'retirement savings', 'pencom', 'pension withdrawal', 'lose job before 50', 'lost job before 50', 'retirement benefits'],
        'target_statutes': ['Pension Reform Act'],
        'primary_terms': ['withdrawal from retirement savings account', 'retirement benefits', 'retirement savings account and remittance', 'supervision of retirement benefits'],
        'determination': "Under Section 7(2) and Section 16 of the Pension Reform Act 2014, an employee under the age of 50 who is disengaged from employment and remains unemployed after four months is statutorily entitled to withdraw up to 25% of the balance in their Retirement Savings Account (RSA)."
    },
    {
        'id': 'dishonoured_cheques',
        'keywords': ['bounced cheque', 'dishonoured cheque', 'bad cheque', 'dud cheque', 'cheque bounced', 'bounced check', 'dishonoured check'],
        'target_statutes': ['Dishonoured Cheques Act', 'Bills of Exchange Act'],
        'primary_terms': ['offences in relation to dishonoured cheques', 'cheque defined', 'liability of drawer', 'notice of dishonour'],
        'determination': "Under Section 1 of the Dishonoured Cheques (Offences) Act, issuing a dud or bounced cheque without sufficient credit or an agreed overdraft is a strict criminal offence punishable by up to two years imprisonment for individuals, or substantial fines for corporations. Additionally, the holder in due course may enforce civil debt recovery under the Bills of Exchange Act."
    },
    {
        'id': 'defamation_online_cyberstalking',
        'keywords': ['defamation', 'defamed', 'slander', 'libel', 'cyberstalking', 'online insult', 'twitter defamation', 'instagram insult', 'character assassination', 'insulting online', 'insulting a politician'],
        'target_statutes': ['Cybercrimes (Prohibition, Prevention, etc.) Act, 2015', 'Criminal Code Act'],
        'primary_terms': ['cyberstalking', 'definition of defamatory matter', 'publication of defamatory matter', 'punishment for defamation'],
        'determination': "Under Section 24 of the Cybercrimes Act 2015 (as amended 2024), transmitting or publishing electronic messages that are grossly offensive or intended to harass, intimidate, or assassinate another person's character constitutes cyberstalking, punishable by fine or imprisonment. Furthermore, Section 373 of the Criminal Code Act provides for criminal prosecution and civil damages for defamation."
    },
    {
        'id': 'criminal_bail_capital_offences',
        'keywords': ['grant bail', 'bail on armed robbery', 'bail for armed robbery', 'bail for murder', 'capital offence', 'bail conditions', 'admitted to bail', 'remand in custody', 'bail armed robbery'],
        'target_statutes': ['Administration of Criminal Justice Act, 2015', 'Constitution of the Federal Republic of Nigeria 1999 (as amended)'],
        'primary_terms': ['bail where a suspect is charged with capital offence', 'general entitlement to bail', 'release on bail of a suspect arrested without warrant', 'conditions of recognizance'],
        'determination': "Under Section 161 of the Administration of Criminal Justice Act (ACJA) 2015, a court generally lacks jurisdiction to grant bail to persons charged with capital offences (such as armed robbery or murder), except under extraordinary circumstances such as documented life-threatening ill-health or unreasonable delay in trial. In non-capital matters, bail is a constitutional right under Section 35 of the 1999 Constitution and Section 158 of ACJA."
    },
    {
        'id': 'domestic_violence_gender',
        'keywords': ['domestic violence', 'husband beating wife', 'beating wife', 'wife beating', 'marital assault', 'battered wife', 'gender violence', 'assault wife', 'assault husband'],
        'target_statutes': ['Criminal Code Act', 'Constitution of the Federal Republic of Nigeria 1999 (as amended)', "Child's Rights Act"],
        'primary_terms': ['punishment of assault', 'assault occasioning harm', 'dignity of human person', 'protection against violence'],
        'determination': "Under Nigerian law, physical abuse or battery of a spouse constitutes a criminal offence of assault occasioning actual bodily harm under Sections 351 and 355 of the Criminal Code Act. Any custom or traditional belief that permits physical chastisement is unconstitutional and void under Section 34 of the 1999 Constitution guaranteeing the right to dignity of the human person."
    },
    {
        'id': 'digital_privacy_phone_search',
        'keywords': ['search phone', 'police took my iphone', 'unlocked my phone', 'police unlocked', 'searched my phone', 'phone at checkpoint', 'laptop search', 'phone at tollgate'],
        'target_statutes': ['Constitution of the Federal Republic of Nigeria 1999 (as amended)', 'Nigeria Police Act, 2020', 'Cybercrimes (Prohibition, Prevention, etc.) Act, 2015'],
        'primary_terms': ['right to private and family life', 'privacy of citizens', 'search of arrested suspect', 'unlawful seizure'],
        'determination': "Under Section 37 of the 1999 Constitution, the privacy of citizens, their homes, correspondence, telephone conversations, and digital data is inviolable. Law enforcement officers have no statutory authority to stop citizens at checkpoints and demand access to their personal smartphones, laptops, or biometric locks without a valid search warrant issued by a court of competent jurisdiction upon reasonable suspicion of crime."
    },
    {
        'id': 'minerals_mining',
        'keywords': ['mining', 'illegal mining', 'gold mining', 'minerals', 'mineral resources', 'cadastre', 'zamfara gold'],
        'target_statutes': ['Minerals and Mining Act'],
        'primary_terms': ['illegal mining', 'possession and ownership of minerals', 'prohibition of exploration without licence'],
        'determination': "Under Section 1 of the Nigerian Minerals and Mining Act, the entire property in and control of all mineral resources in Nigeria is vested exclusively in the Federal Government. Conducting exploration or mining activities without a valid lease or licence from the Federal Ministry of Solid Minerals is an offence punishable by severe fines, forfeiture, and imprisonment under Section 131."
    },
    {
        'id': 'admiralty_shipping',
        'keywords': ['admiralty', 'ship arrested', 'vessel arrested', 'maritime', 'cargo damage', 'cabotage', 'lagos port', 'seaman'],
        'target_statutes': ['Admiralty Jurisdiction Act', 'Cabotage Act'],
        'primary_terms': ['extent of the admiralty jurisdiction', 'mode of exercise of admiralty jurisdiction', 'arrest of ship'],
        'determination': "The Federal High Court exercises exclusive admiralty jurisdiction over maritime claims, ship mortgages, carriage of goods by sea, and arrest of vessels in rem under Section 1 and Section 5 of the Admiralty Jurisdiction Act."
    },
    {
        'id': 'witchcraft_juju_charms',
        'keywords': ['juju', 'witchcraft', 'voodoo', 'trial by ordeal', 'charm', 'charms', 'native medicine', 'black magic'],
        'target_statutes': ['Criminal Code Act', 'Penal Code (Northern States) Federal Provisions Act, 1960'],
        'primary_terms': ['offences in relation to witchcraft and juju', 'directing etc unlawful trial by ordeal', 'unlawful trial by ordeal'],
        'determination': "Under Section 210 of the Criminal Code Act (and Section 216 of the Penal Code), representing oneself to be a witch, accusing or threatening to accuse any person of witchcraft, or making, selling, using, or possessing any juju, drug, or charm intended to compel or prevent any person from acting lawfully is a criminal misdemeanour punishable by two years imprisonment. Furthermore, directing or participating in an unlawful trial by ordeal is a felony punishable by up to ten years imprisonment, or the death penalty where death results under Section 208."
    },
    {
        'id': 'traffic_road_safety_pedestrian',
        'keywords': [
            'crossing the road', 'crossing road', 'crossing expressway', 'cross the road', 
            'cross expressway', 'pedestrian', 'pedestrian bridge', 'footbridge', 'jaywalking', 
            'traffic light', 'traffic offence', 'traffic offense', 'frsc', 'road safety', 
            'road marshal', 'speed limit', 'driving without licence', 'driving without license', 
            'highway safety', 'obstruction of highway', 'federal highway', 'lastma', 'vio',
            'causing death by dangerous driving', 'reckless driving', 'dangerous driving',
            'highway obstruction', 'damage to federal highway', 'traffic on federal highway'
        ],
        'target_statutes': ['Federal Highways Act', 'FRSC Act', 'Constitution of the Federal Republic of Nigeria 1999 (as amended)'],
        'primary_terms': [
            'causing death by dangerous driving on federal highway', 'reckless driving on federal highway', 
            'power to regulate traffic', 'highways safe', 'powers of the Corps', 
            'right to personal liberty', 'freedom of movement', 'written law', 'pedestrian'
        ],
        'determination': "Under the Federal Highways Act (Cap. F13 LFN 2004) and Section 11 of the Federal Road Safety Commission (FRSC) Act, the regulation and safety of federal highways are strictly overseen by designated authorities. Causing death or bodily injury by dangerous, reckless, or negligent driving on a federal highway is a serious criminal offence (Sections 5 and 6 of the Federal Highways Act). While traffic laws and regulations mandate designated lane usage and pedestrian overhead bridges, Section 36(12) and Section 35 of the 1999 Constitution guarantee that no citizen may be arrested, penalised, or extorted without formal written legal authority."
    }
]

import difflib

LEGAL_VOCABULARY = [
    'police', 'arrest', 'detain', 'warrant', 'bail', 'freeze', 'freezing', 
    'bank', 'account', 'divorce', 'custody', 'marriage', 'steal', 'stealing', 
    'theft', 'employer', 'salary', 'wages', 'dismissal', 'termination', 
    'landlord', 'tenant', 'evict', 'eviction', 'premises', 'copyright', 
    'infringement', 'trademark', 'patent', 'counterfeit', 'pension', 'cheque', 
    'bounced', 'defamation', 'cyberstalking', 'extortion', 'bribe', 'bribery', 
    'gratification', 'kidnapping', 'assault', 'admiralty', 'mining', 'witchcraft', 'juju',
    'pedestrian', 'highway', 'traffic', 'bridge', 'wedding', 'bigamy', 'registry'
]

NIGERIAN_COLLOQUIALISMS = {
    'juju': 'witchcraft juju',
    'voodoo': 'witchcraft juju',
    'native doctor': 'witchcraft juju trial by ordeal',
    'yahoo': 'cybercrime advance fee fraud online scam',
    'yahoo boy': 'cybercrime advance fee fraud online scam',
    '419': 'advance fee fraud obtaining false pretences',
    'throw my load': 'landlord evict recovery of premises notice to quit',
    'pack my load': 'landlord evict recovery of premises notice to quit',
    'throw my things': 'landlord evict recovery of premises notice to quit',
    'oga': 'employer boss labour act',
    'feeding money': 'maintenance child support child rights matrimonial causes',
    'school fees': 'maintenance child welfare child rights',
    'dud cheque': 'dishonoured cheque bounced cheque',
    'dud check': 'dishonoured cheque bounced cheque',
    'pnd': 'post no debit freezing order bank account',
    'tollgate': 'checkpoint police stop and search',
    'pos failed': 'consumer protection refund electronic fund transfer',
    'atm ate': 'consumer protection refund electronic fund transfer',
    'agbero': 'tout extortion demand with menaces thuggery',
    'area boys': 'extortion breach of peace touts',
    'one chance': 'robbery transit theft armed robbery',
    'ajagungbale': 'land grabber forcible entry trespass malicious damage',
    'land grabbers': 'forcible entry trespass recovery of possession',
    'cultist': 'unlawful society confraternity felony',
    'cultism': 'unlawful society confraternity',
    'ritual killing': 'murder homicide human parts criminal charms',
    'blood money': 'murder human parts criminal charms',
    'japa scam': 'advance fee fraud travel scam visa fraud',
    'japa agent': 'advance fee fraud travel scam visa fraud',
    'crossing the road': 'pedestrian highway safety pedestrian bridge FRSC Act',
    'crossing road': 'pedestrian highway safety pedestrian bridge FRSC Act',
    'crossing expressway': 'pedestrian highway safety pedestrian bridge FRSC Act',
    'pedestrian bridge': 'pedestrian footbridge highway crossing FRSC Act',
    'jaywalking': 'pedestrian crossing highway traffic FRSC Act',
    'kai': 'task force environmental sanitation arbitrary arrest personal liberty',
    'lastma': 'traffic enforcement road safety personal liberty',
    'vio': 'vehicle inspection road safety',
    'court wedding': 'marriage act celebration of marriage registrar certificate',
    'registry wedding': 'marriage act registrar celebration certificate',
    'road accident': 'federal highways dangerous driving frsc',
    'hit and run': 'federal highways dangerous reckless driving accident frsc'
}

def normalize_query(query: str) -> str:
    q_low = query.lower()
    expanded = []
    for col, repl in NIGERIAN_COLLOQUIALISMS.items():
        if col in q_low:
            expanded.extend(repl.split())
            
    words = re.findall(r'[a-zA-Z]{4,}', q_low)
    corrected = []
    for w in words:
        if w in LEGAL_VOCABULARY:
            corrected.append(w)
        else:
            close = difflib.get_close_matches(w, LEGAL_VOCABULARY, n=1, cutoff=0.75)
            corrected.append(close[0] if close else w)
            
    norm_q = ' '.join(corrected)
    if expanded:
        norm_q += ' ' + ' '.join(expanded)
    return norm_q

def classify_legal_intent(scenario: str) -> Optional[dict]:
    q_low = scenario.lower()
    norm_q = normalize_query(scenario)
    search_text = f"{q_low} {norm_q}"
    best_dom = None
    best_score = 0
    for dom in LEGAL_DOMAINS:
        score = 0
        for kw in dom['keywords']:
            if ' ' in kw:
                if kw in search_text:
                    score += 6
            else:
                if re.search(r'\b' + re.escape(kw) + r'\b', search_text):
                    if kw in ['bribe', 'bribery', 'extortion', 'gratification', 'steal', 'stealing', 'theft', 'divorce', 'custody', 'freeze', 'pnd', 'evict', 'landlord', 'tenant', 'copyright', 'juju', 'witchcraft', 'cheque', 'pension', 'pedestrian', 'frsc', 'highway']:
                        score += 8
                    else:
                        score += 3
        if score > best_score and score >= 3:
            best_score = score
            best_dom = dom
    return best_dom

def analyze_and_route(scenario: str) -> dict:
    baseline = classify_legal_intent(scenario)
    target_stats = list(baseline['target_statutes']) if baseline else []
    phrases = list(baseline['primary_terms']) if baseline else []
    answer = baseline['determination'] if baseline else ""
    
    if API_KEY and not API_KEY.startswith("your-actual"):
        prompt = (
            f"You are an expert Nigerian legal scholar. Analyze this scenario: '{scenario}'. "
            f"Select from certified Nigerian Federal enactments (such as: CFRN 1999, Criminal Code Act, Penal Code, "
            f"Administration of Criminal Justice Act, Nigeria Police Act 2020, CAMA 2020, Labour Act, "
            f"Matrimonial Causes Act, Child's Rights Act, EFCC Act, Cybercrimes Act, FRSC Act, BOFIA, "
            f"Copyright Act, FCCPA, Pension Reform Act, Land Use Act, Dishonoured Cheques Act, etc.).\n"
            f"Return JSON ONLY with keys:\n"
            f"- 'legal_answer': (authoritative 2-3 sentence legal determination under Nigerian Federal Law)\n"
            f"- 'target_statutes': (list of exact Nigerian Federal Acts from the above corpus governing this matter)\n"
            f"- 'legal_phrases': (list of key statutory phrases to locate operative sections)"
        )
        raw = call_gemini(prompt, response_json=True)
        if raw:
            try:
                parsed = json.loads(raw)
                gemini_ans = parsed.get("legal_answer", "").strip()
                if gemini_ans:
                    answer = gemini_ans
                gemini_stats = parsed.get("target_statutes", [])
                if isinstance(gemini_stats, list) and gemini_stats:
                    target_stats = list(dict.fromkeys(target_stats + gemini_stats))
                gemini_phrases = parsed.get("legal_phrases", [])
                if isinstance(gemini_phrases, list) and gemini_phrases:
                    phrases = list(dict.fromkeys(phrases + gemini_phrases))
            except Exception:
                pass
                
    if not answer:
        answer = "Governing statutory provisions retrieved across certified Federal Republic of Nigeria enactments."
        
    return {
        "legal_answer": answer,
        "target_statutes": target_stats,
        "legal_phrases": phrases
    }

def retrieve_candidate_pool(conn, plan: dict, raw_query: str) -> list:
    cursor = conn.cursor()
    tokens = [w for w in re.findall(r'[a-zA-Z]{3,}', raw_query.lower()) if w not in STOP_WORDS]
    target_stats = plan.get("target_statutes", [])
    primary_terms = plan.get("legal_phrases", []) or tokens
    scored = {}
    
    # 1. Search within target statutes if identified
    if target_stats:
        for stat in target_stats:
            short = stat.split(',')[0].split('(')[0].strip()
            cursor.execute(
                "SELECT statute_title, section_number, section_title, full_text FROM sections_fts WHERE statute_title LIKE ?;", 
                (f"%{short}%",)
            )
            for r in cursor.fetchall():
                title_low = r[2].lower()
                text_low = r[3].lower()
                score = 0
                
                # Penalize administrative sections
                if title_low in ['interpretation', 'short title', 'citation', 'repeals', 'regulations', 'savings']:
                    score -= 40
                if 're-registration' in title_low and not any('re-registration' in tk for tk in tokens):
                    score -= 25
                    
                # High boost for exact key phrases in section title
                for pt in primary_terms:
                    pt_low = pt.lower()
                    if pt_low in title_low:
                        score += 70
                    elif pt_low in text_low:
                        score += 15
                        
                # Boost for query tokens in section title
                for tk in tokens:
                    tk_low = tk.lower()
                    if tk_low in title_low:
                        score += 30
                    elif tk_low in text_low:
                        score += 4
                        
                if score > 15:
                    title = "Constitution of the Federal Republic of Nigeria 1999 (as amended)" if "Constitution" in r[0] else r[0]
                    clean_snip = make_clean_snippet(r[3], 260)
                    scored[(title, str(r[1]))] = (score, title, r[1], r[2], clean_snip, r[3])
                    
    # 2. Search title matches across all non-peripheral statutes if needed
    if len(scored) < 3 and tokens:
        for tk in tokens[:3]:
            cursor.execute(
                "SELECT statute_title, section_number, section_title, full_text FROM sections_fts WHERE section_title LIKE ? LIMIT 15;",
                (f"%{tk}%",)
            )
            for r in cursor.fetchall():
                if r[0] in PERIPHERAL_STATUTES:
                    continue
                title_low = r[2].lower()
                text_low = r[3].lower()
                if title_low in ['interpretation', 'short title', 'citation', 'repeals', 'regulations']:
                    continue
                # Systemic homonym barrier: if query contains 2+ keywords, a match on an isolated word
                # in a section title MUST have at least one other query keyword in the section text or title
                if len(tokens) >= 2:
                    other_tokens = [ot for ot in tokens if ot != tk]
                    if not any(ot in title_low or ot in text_low for ot in other_tokens):
                        continue
                # Disambiguate financial cheque crossings from pedestrian/physical road crossings
                if ('crossing' in title_low or 'crossings' in title_low) and (r[0] == 'Bills of Exchange Act' or 'cheque' in title_low or 'check' in title_low):
                    financial_terms = {'cheque', 'check', 'bank', 'banking', 'bill', 'drawer', 'payee', 'account', 'finance', 'payment', 'endorse', 'negotiable', 'funds', 'credit'}
                    if not any(ft in raw_query.lower() for ft in financial_terms):
                        continue
                score = 35 + sum(15 for other in tokens if other in title_low)
                title = "Constitution of the Federal Republic of Nigeria 1999 (as amended)" if "Constitution" in r[0] else r[0]
                key = (title, str(r[1]))
                if key not in scored or scored[key][0] < score:
                    clean_snip = make_clean_snippet(r[3], 260)
                    scored[key] = (score, title, r[1], r[2], clean_snip, r[3])
                    
    # 3. FTS fallback if still under 3 results
    if len(scored) < 3 and tokens:
        fts_query = " AND ".join(tokens[:2]) if len(tokens) >= 2 else (tokens[0] if tokens else f'"{raw_query}"')
        try:
            cursor.execute(
                "SELECT statute_title, section_number, section_title, full_text FROM sections_fts WHERE sections_fts MATCH ? ORDER BY rank LIMIT 10;",
                (fts_query,)
            )
            for r in cursor.fetchall():
                if r[0] in PERIPHERAL_STATUTES:
                    continue
                title_low = r[2].lower()
                # Disambiguate financial cheque crossings from pedestrian/physical road crossings
                if ('crossing' in title_low or 'crossings' in title_low) and (r[0] == 'Bills of Exchange Act' or 'cheque' in title_low or 'check' in title_low):
                    financial_terms = {'cheque', 'check', 'bank', 'banking', 'bill', 'drawer', 'payee', 'account', 'finance', 'payment', 'endorse', 'negotiable', 'funds', 'credit'}
                    if not any(ft in raw_query.lower() for ft in financial_terms):
                        continue
                title = "Constitution of the Federal Republic of Nigeria 1999 (as amended)" if "Constitution" in r[0] else r[0]
                key = (title, str(r[1]))
                if key not in scored:
                    clean_snip = make_clean_snippet(r[3], 260)
                    scored[key] = (10, title, r[1], r[2], clean_snip, r[3])
        except Exception:
            pass
            
    ranked = sorted(scored.values(), key=lambda x: x[0], reverse=True)
    return [
        {
            "statute": item[1],
            "section_number": item[2],
            "section_title": item[3],
            "part": "",
            "snippet": item[4],
            "full_text": item[5]
        }
        for item in ranked[:3]
    ]

@app.get("/api/search")
def api_search(q: str = Query(...)):
    if not DB_PATH.exists(): raise HTTPException(status_code=500, detail="Database not found")
    conn = sqlite3.connect(DB_PATH)
    norm_q = normalize_query(q)
    if direct := (check_direct_citation(q, conn) or check_direct_citation(norm_q, conn)):
        conn.close()
        return {"query": q, "legal_issue": f"Direct statutory match verified for Section {direct[0]['section_number']} of {direct[0]['statute']}.", "results": direct}
    if rule := (check_deterministic_heuristics(q, conn) or check_deterministic_heuristics(norm_q, conn)):
        conn.close()
        return rule
    plan = analyze_and_route(q)
    combined_query = f"{q} {norm_q}"
    candidates = retrieve_candidate_pool(conn, plan, combined_query)
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
