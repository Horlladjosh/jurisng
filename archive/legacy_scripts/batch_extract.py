import sys
from pathlib import Path
sys.path.append(".")

from utils.extractor_engine import UniversalGazetteExtractor

STATUTE_CONFIGS = [
    {
        "statute_id": "acja_2015",
        "statute_title": "Administration of Criminal Justice Act 2015",
        "short_title": "ACJA 2015",
        "year": 2015,
        "total_sections": 495,
        "pdf_path": "data/raw_pdfs/acja-2015.pdf",
        "output_path": "data/json_laws/acja_2015.json"
    },
    {
        "statute_id": "child_rights_act_2003",
        "statute_title": "Child's Right Act 2003",
        "short_title": "Child Rights Act 2003",
        "year": 2003,
        "total_sections": 278,
        "pdf_path": "data/raw_pdfs/child-rights-act.pdf",
        "output_path": "data/json_laws/child_rights_act_2003.json"
    },
    {
        "statute_id": "cybercrimes_act_2015",
        "statute_title": "Cybercrimes (Prohibition, Prevention, etc.) Act 2015",
        "short_title": "Cybercrimes Act 2015",
        "year": 2015,
        "total_sections": 59,
        "pdf_path": "data/raw_pdfs/cybercrimes-act-2015.pdf",
        "output_path": "data/json_laws/cybercrimes_act_2015.json"
    },
    {
        "statute_id": "evidence_act_2011",
        "statute_title": "Evidence Act 2011",
        "short_title": "Evidence Act 2011",
        "year": 2011,
        "total_sections": 259,
        "pdf_path": "data/raw_pdfs/evidence-act-2011.pdf",
        "output_path": "data/json_laws/evidence_act_2011.json"
    },
    {
        "statute_id": "labour_act",
        "statute_title": "Labour Act (Chapter L1, Laws of the Federation of Nigeria 2004)",
        "short_title": "Labour Act",
        "year": 2004,
        "total_sections": 92,
        "pdf_path": "data/raw_pdfs/labour-act.pdf",
        "output_path": "data/json_laws/labour_act.json"
    },
    {
        "statute_id": "land_use_act_1978",
        "statute_title": "Land Use Act 1978 (Chapter L5, Laws of the Federation of Nigeria 2004)",
        "short_title": "Land Use Act 1978",
        "year": 1978,
        "total_sections": 51,
        "pdf_path": "data/raw_pdfs/land-use-act.pdf",
        "output_path": "data/json_laws/land_use_act_1978.json"
    },
    {
        "statute_id": "fccpa_2018",
        "statute_title": "Federal Competition and Consumer Protection Act 2018",
        "short_title": "FCCPA 2018",
        "year": 2018,
        "total_sections": 168,
        "pdf_path": "data/raw_pdfs/fccpa-2018.pdf",
        "output_path": "data/json_laws/fccpa_2018.json"
    },
    {
        "statute_id": "employee_compensation_act_2010",
        "statute_title": "Employees' Compensation Act 2010",
        "short_title": "Employees Compensation Act 2010",
        "year": 2010,
        "total_sections": 74,
        "pdf_path": "data/raw_pdfs/employee-compensation-act-2010.pdf",
        "output_path": "data/json_laws/employee_compensation_act_2010.json"
    },
    {
        "statute_id": "money_laundering_act_2011",
        "statute_title": "Money Laundering (Prohibition) Act 2011",
        "short_title": "Money Laundering Act 2011",
        "year": 2011,
        "total_sections": 25,
        "pdf_path": "data/raw_pdfs/money-laundering-act-2011.pdf",
        "output_path": "data/json_laws/money_laundering_act_2011.json"
    },
    {
        "statute_id": "national_health_act_2014",
        "statute_title": "National Health Act 2014",
        "short_title": "National Health Act 2014",
        "year": 2014,
        "total_sections": 65,
        "pdf_path": "data/raw_pdfs/national-health-act-2014.pdf",
        "output_path": "data/json_laws/national_health_act_2014.json"
    },
    {
        "statute_id": "penal_code_act_1960",
        "statute_title": "Penal Code (Northern States) Federal Provisions Act",
        "short_title": "Penal Code Act",
        "year": 1960,
        "total_sections": 74,  # Sections 1-6 + Schedule Offenses 410-477
        "pdf_path": "data/raw_pdfs/penal-code-northern-states-1960.pdf",
        "output_path": "data/json_laws/penal_code_act_1960.json"
    }
]

def run_batch():
    print("=" * 65)
    print("STARTING BATCH EXTRACTION OF 11 STATUTES")
    print("=" * 65)
    
    for cfg in STATUTE_CONFIGS:
        pdf_file = Path(cfg["pdf_path"])
        if not pdf_file.exists():
            print(f"\n[!] SKIPPING {cfg['short_title']} -> PDF not found at {pdf_file}")
            continue
            
        extractor = UniversalGazetteExtractor(**cfg)
        try:
            extractor.run()
        except Exception as e:
            print(f"[X] Extraction failed for {cfg['short_title']}: {e}")

if __name__ == "__main__":
    run_batch()
