# JurisNG Engineering Timeline & Development History

This document provides a comprehensive, date-stamped chronological history of the **JurisNG** platform (formerly *Nigerian Law Engine / NaijaLex*), tracing the journey from the early experiments with isolated scripts and 10–12 statutes to a production-grade statutory intelligence engine indexing 128 federal enactments (9,959 verified sections).

---

## 📅 Chronological Milestones & Engineering Log

### Milestone 1: The Genesis & "The Perfect Ten" (August 17, 2026)
* **Date:** 17 August 2026
* **Corpus Size:** 10 Core Federal Acts
* **What Happened:**
  * **Individual Custom Parsers:** Started by writing dedicated regex parsers for the most critical Nigerian laws:
    * `archive/parsers/parse_cfrn.py` (Constitution of the Federal Republic of Nigeria 1999)
    * `archive/parsers/parse_police_act.py` (Nigeria Police Act 2020)
    * `archive/parsers/parse_labour_act.py` (Labour Act 1971)
    * `archive/parsers/parse_child_rights.py` (Child's Rights Act 2003)
  * **The "TOC Leakage" Battle:** Discovered that raw PDF conversions were dragging Tables of Contents into substantive section bodies (`audit_toc_leakage.py`).
  * **Building "The Perfect Ten":** Iterated through `audit_all_ten.py` and `build_perfect_ten.py` to achieve pristine extraction across the core 10 acts (CFRN, Police Act, Labour Act, Evidence Act, ACJA, CAMA, Cybercrimes, CRA, CITA, PITA).
  * **Early Search Experiment:** Built the initial retrieval and indexing prototypes (`archive/indexing/build_index.py`, `archive/legacy_scripts/advanced_retriever.py`).

---

### Milestone 2: Expansion to 20 Acts & Batch LLM Ingestion (August 18 – 25, 2026)
* **Date:** 18 – 25 August 2026
* **Corpus Size:** ~12 to 20 Statutes
* **What Happened:**
  * **Batch Extraction Pipelines:** Developed `batch_llm_ingest.py` and `batch_digital_ingest.py` to test scaling beyond the initial 10 laws.
  * **Benchmarking & Missing Section Audits:**
    * Tested extraction fidelity against tricky formatting in the Cybercrimes Act (`compare_cybercrimes.py`), Electoral Act 2022, and FCCPA 2018.
    * Built debugging scripts (`debug_missing_sections.py`, `audit_completeness.py`) to detect skipped clauses or collapsed subsections.
  * **Vector & Embedding Experiments:** Experimented with vector embeddings (`vector_db/`) alongside full-text inverted indexes.

---

### Milestone 3: Early Web Interface & Layout Prototyping (September 4 – 16, 2026)
* **Date:** 4 – 16 September 2026
* **What Happened:**
  * **First Web Prototype:** Created the initial web dashboard combining FastAPI and vanilla HTML/JS.
  * **User Experience Iterations:** Iterated on search input states, response cards, and direct statutory preview modals.
  * **Direct Scenario Matching:** Introduced initial heuristic rules for common Nigerian legal queries (e.g., landlord-tenant disputes, police bail conditions, fundamental human rights).

---

### Milestone 4: Architectural Snapshot & Modular Reorganization (October 7, 2026)
* **Date:** 7 October 2026
* **What Happened:**
  * **Pre-Engine Snapshot:** Archived the monolithic early scripts into `backups/snapshot_pre_engine/` and consolidated the messy root directory into `archive/legacy_scripts/`.
  * **Transition to Engine Architecture:** Established the clean `engine/` package directory for parsers, cleaners, and watchers.
  * **Standardized JSON Schema:** Standardized statutory documents into a single JSON format (`title`, `year`, `jurisdiction`, `sections` array with `section_number`, `section_title`, `part`, `full_text`).

---

### Milestone 5: The 126 Statute Expansion & Gazette Watcher (October 8 – 10, 2026)
* **Date:** 8 – 10 October 2026
* **Corpus Size:** 126 Federal Statutes (9,903 sections)
* **What Happened:**
  * **Full Corpus Scaling:** Ingested the entire library of 126 certified Nigerian Federal Acts, growing the database to 44 MB.
  * **Automated Legislative Watcher (`engine/legislative_watcher.py`):**
    * Built an automated service to scan remote official gazette feeds and legislative trees.
    * Detects newly assented Acts and statutory amendments, generating automated Markdown alerts.

---

### Milestone 6: Verbatim Fidelity Cleaning & Quality Audit (October 11, 2026)
* **Date:** 11 October 2026
* **What Happened:**
  * **Loose-Leaf Header Cleanup:** Identified and eliminated historic loose-leaf running headers (`CAP. Ll`, `Ll-XX`) and OCR page debris across all files.
  * **First-Line Title Leakage Fix:** Sanitized 1,218 section titles across 126 statutes where statute titles had leaked into Section 1 (e.g. Labour Act Section 56 header fix).
  * **Automated Fidelity Verification Suite (`verify_extraction_fidelity.py`):** Built a verification script confirming 100% data integrity and zero empty or untitled sections across all 9,903 sections.

---

### Milestone 7: Direct Support Pipe & Resend / Zoho DNS Setup (October 12, 2026)
* **Date:** 12 October 2026
* **What Happened:**
  * **Local Database Intake:** Created the persistent SQLite `feedback_submissions` audit table so user bug reports and queries are never lost.
  * **Subdomain DNS Isolation:** Verified `mail.horlladjosh.com` on Resend using Cloudflare DNS without touching primary MX records on Zoho Mail (`contact@horlladjosh.com`).
  * **Live Delivery Verification:** Verified live HTML transactional email delivery directly into Zoho Mail with automatic fallback mechanisms.

---

### Milestone 8: UI Streamlining, Market Intelligence & Rebranding to JurisNG (October 12 – 13, 2026)
* **Date:** 12 – 13 October 2026
* **What Happened:**
  * **Modal Modernization:** Replaced emoji-heavy radio cards with a clean `<select>` dropdown and eliminated third-party Resend attribution.
  * **Competitive Intelligence Discovery:** Discovered the existing `naijalex.com` platform (registered March 2026 on Vercel/Supabase). Proactively averted brand confusion, trademark friction, and SEO overlap.
  * **Rebranding to JurisNG:** Renamed platform, logos, disclaimers, OpenAPI documentation, and email pipes to **JurisNG** (`jurisng.horlladjosh.com`).
  * **Security Hardening:** Implemented HTTP security headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`), an invisible anti-bot honeypot, and IP rate limiting on feedback endpoints.

---

### Milestone 9: The 128 Statute Milestone — Federal Highways Act & Marriage Act Ingestion (October 14, 2026)
* **Date:** 14 October 2026
* **Corpus Size:** 128 Federal Statutes (9,959 sections)
* **What Happened:**
  * **Federal Highways Act Ingestion:** Downloaded official Gazette PDF (`data/raw_pdfs/federal_highways_act.pdf`), cleanly extracted all 29 substantive sections with 100% valid titles, zero placeholders, and strict fidelity.
  * **Marriage Act Ingestion:** Downloaded official Gazette PDF (`data/raw_pdfs/marriage_act.pdf`), cleanly extracted all 55 sections with 100% valid titles and complete statutory text covering celebration of marriage, certificates, caveats, and bigamy offences.
  * **Zero-Defect Verification:** Audited entire 128-statute library via `verify_extraction_fidelity.py` with 100% precision across all 9,959 sections in both SQLite and FTS5.
  * **Domain Ontology & Query Expansion:** Enhanced family law ontology (`family_divorce_custody`) and road traffic ontology (`traffic_road_safety_pedestrian`) in `server.py` with colloquialisms (`court wedding`, `road accident`, `hit and run`).
  * **UI Library Expansion:** Added dedicated "Family & Marriage" category filter pill in `index.html` and synchronized all counters.

