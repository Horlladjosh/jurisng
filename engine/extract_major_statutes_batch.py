"""
Major Nigerian Federal Statutes Ingestion Pipeline.
Extracts, parses, reflows, and validates high-impact Nigerian commercial,
regulatory, financial, and judicial statutes into pristine JSON manifests.
"""

import urllib.request
import re
import json
import os
from engine.clean_and_reflow_corpus import clean_and_reflow_legal_text

STATUTE_MANIFESTS = [
    {
        "md_path": "2011/freedom-of-information-act-2011.md",
        "statute_id": "foia_2011",
        "title": "Freedom of Information Act, 2011",
        "short_title": "Freedom of Information Act",
        "year": 2011,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 6 of 2011",
        "description": "An Act to make public records and information more freely available, provide for public access to public records and information, protect public records and information to the extent consistent with the public interest and the protection of personal privacy.",
        "out_file": "freedom_of_information_act_2011.json"
    },
    {
        "md_path": "2007/public-procurement-act-no-14-2007.md",
        "statute_id": "public_procurement_act_2007",
        "title": "Public Procurement Act, 2007",
        "short_title": "Public Procurement Act",
        "year": 2007,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 14 of 2007",
        "description": "An Act to establish the National Council on Public Procurement and the Bureau of Public Procurement as regulatory authorities responsible for monitoring and oversight of public procurement.",
        "out_file": "public_procurement_act_2007.json"
    },
    {
        "md_path": "2007/fiscal-responsibility-act-no-31-2007.md",
        "statute_id": "fiscal_responsibility_act_2007",
        "title": "Fiscal Responsibility Act, 2007",
        "short_title": "Fiscal Responsibility Act",
        "year": 2007,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 31 of 2007",
        "description": "An Act to provide for prudent management of the Nation's resources, ensure long-term macro-economic stability of the national economy, and secure greater accountability and transparency in fiscal operations.",
        "out_file": "fiscal_responsibility_act_2007.json"
    },
    {
        "md_path": "2007/investments-and-securities-act-2007.md",
        "statute_id": "isa_2007",
        "title": "Investments and Securities Act, 2007",
        "short_title": "Investments and Securities Act",
        "year": 2007,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 29 of 2007",
        "description": "An Act to repeal the Investments and Securities Act 1999 and establish the Securities and Exchange Commission as the apex regulatory body for the Nigerian capital market.",
        "out_file": "investments_securities_act_2007.json"
    },
    {
        "md_path": "2010/nigerian-oil-and-gas-industry-content-development-act-2010.md",
        "statute_id": "nogicd_act_2010",
        "title": "Nigerian Oil and Gas Industry Content Development Act, 2010",
        "short_title": "NOGICD (Local Content) Act",
        "year": 2010,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 2 of 2010",
        "description": "An Act to provide for the development of Nigerian content in the Nigerian oil and gas industry, Nigeria content plan, supervision, coordination, monitoring and implementation of Nigerian content.",
        "out_file": "nogicd_local_content_act_2010.json"
    },
    {
        "md_path": "2007/nigerian-maritime-administration-and-safety-agency-act-2007-no-17-2007.md",
        "statute_id": "nimasa_act_2007",
        "title": "Nigerian Maritime Administration and Safety Agency Act, 2007",
        "short_title": "NIMASA Act",
        "year": 2007,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 17 of 2007",
        "description": "An Act to establish the Nigerian Maritime Administration and Safety Agency for the promotion of maritime safety and security, protection of the marine environment, and shipping administration.",
        "out_file": "nimasa_act_2007.json"
    },
    {
        "md_path": "2006/nigeria-deposit-insurance-corporation-act-2006.md",
        "statute_id": "ndic_act_2006",
        "title": "Nigeria Deposit Insurance Corporation Act, 2006",
        "short_title": "NDIC Act",
        "year": 2006,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 16 of 2006",
        "description": "An Act to repeal the Nigeria Deposit Insurance Corporation Act 1988 and re-enact the NDIC Act to insure deposit liabilities of licensed banks and other financial institutions.",
        "out_file": "ndic_act_2006.json"
    },
    {
        "md_path": "2007/national-identity-management-commission-act-2007-no-23-2007.md",
        "statute_id": "nimc_act_2007",
        "title": "National Identity Management Commission Act, 2007",
        "short_title": "NIMC Act",
        "year": 2007,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 23 of 2007",
        "description": "An Act to establish the National Identity Management Commission to provide for the establishment of a National Identity Database and the issuance of National Identity Smart Cards.",
        "out_file": "nimc_act_2007.json"
    },
    {
        "md_path": "2011/nigeria-sovereign-investment-authority-establishment-etc-act-2011.md",
        "statute_id": "nsia_act_2011",
        "title": "Nigeria Sovereign Investment Authority (Establishment, etc.) Act, 2011",
        "short_title": "NSIA (Sovereign Wealth) Act",
        "year": 2011,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 15 of 2011",
        "description": "An Act to establish the Nigeria Sovereign Investment Authority to build a savings base for the Nigerian people, enhance development of Nigerian infrastructure and provide stabilization support in times of economic stress.",
        "out_file": "nsia_sovereign_wealth_act_2011.json"
    },
    {
        "md_path": "2011/financial-reporting-council-of-nigeria-act-2011.md",
        "statute_id": "frcn_act_2011",
        "title": "Financial Reporting Council of Nigeria Act, 2011",
        "short_title": "FRCN Act",
        "year": 2011,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 6 of 2011",
        "description": "An Act to repeal the Nigerian Accounting Standards Board Act and enact the Financial Reporting Council of Nigeria Act to develop and promote compliance with accounting, auditing and corporate governance standards.",
        "out_file": "frcn_act_2011.json"
    },
    {
        "md_path": "2004/supreme-court-act-cap-s15-lfn-2004.md",
        "statute_id": "supreme_court_act",
        "title": "Supreme Court Act",
        "short_title": "Supreme Court Act",
        "year": 1960,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. S15, LFN 2004",
        "description": "An Act to make provision for the constitution, jurisdiction and procedure of the Supreme Court of Nigeria.",
        "out_file": "supreme_court_act.json"
    },
    {
        "md_path": "2004/court-of-appeal-act-cap-c36-lfn-2004.md",
        "statute_id": "court_of_appeal_act",
        "title": "Court of Appeal Act",
        "short_title": "Court of Appeal Act",
        "year": 1976,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. C36, LFN 2004",
        "description": "An Act to establish the Court of Appeal of Nigeria and make provision for the powers and procedure of the Court.",
        "out_file": "court_of_appeal_act.json"
    },
    {
        "md_path": "2004/federal-high-court-act-cap-f12-lfn-2004.md",
        "statute_id": "federal_high_court_act",
        "title": "Federal High Court Act",
        "short_title": "Federal High Court Act",
        "year": 1973,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. F12, LFN 2004",
        "description": "An Act to establish the Federal High Court and define its jurisdiction, powers and procedure.",
        "out_file": "federal_high_court_act.json"
    },
    {
        "md_path": "2004/legal-practitioners-act-cap-l11-lfn-2004.md",
        "statute_id": "legal_practitioners_act",
        "title": "Legal Practitioners Act",
        "short_title": "Legal Practitioners Act",
        "year": 1975,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. L11, LFN 2004",
        "description": "An Act to regulate the legal profession in Nigeria, the qualification and admission of legal practitioners, and discipline in the legal profession.",
        "out_file": "legal_practitioners_act.json"
    },
    {
        "md_path": "2004/code-of-conduct-bureau-and-tribunal-act-cap-c15-lfn-2004.md",
        "statute_id": "code_of_conduct_act",
        "title": "Code of Conduct Bureau and Tribunal Act",
        "short_title": "Code of Conduct Act",
        "year": 1989,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. C15, LFN 2004",
        "description": "An Act to establish the Code of Conduct Bureau and Code of Conduct Tribunal for the purpose of ensuring the observance of the Code of Conduct by public officers.",
        "out_file": "code_of_conduct_act.json"
    },
    {
        "md_path": "2003/coastal-and-inland-shipping-cabotage-act-no-5-2003.md",
        "statute_id": "cabotage_act",
        "title": "Coastal and Inland Shipping (Cabotage) Act, 2003",
        "short_title": "Cabotage Act",
        "year": 2003,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 5 of 2003",
        "description": "An Act to restrict the use of foreign vessels in domestic coastal trade to promote the development of indigenous tonnage.",
        "out_file": "cabotage_act.json"
    },
    {
        "md_path": "2004/capital-gains-tax-act-cap-c1-lfn-2004.md",
        "statute_id": "capital_gains_tax_act",
        "title": "Capital Gains Tax Act",
        "short_title": "Capital Gains Tax Act",
        "year": 1967,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. C1, LFN 2004",
        "description": "An Act to provide for the taxation of capital gains accruing on disposal of assets.",
        "out_file": "capital_gains_tax_act.json"
    },
    {
        "md_path": "2004/bills-of-exchange-act-cap-b8-lfn-2004.md",
        "statute_id": "bills_of_exchange_act",
        "title": "Bills of Exchange Act",
        "short_title": "Bills of Exchange Act",
        "year": 1917,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. B8, LFN 2004",
        "description": "An Act to codify the law relating to bills of exchange, cheques and promissory notes.",
        "out_file": "bills_of_exchange_act.json"
    },
    {
        "md_path": "2004/bankruptcy-act-cap-b2-lfn-2004.md",
        "statute_id": "bankruptcy_act",
        "title": "Bankruptcy Act",
        "short_title": "Bankruptcy Act",
        "year": 1979,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. B2, LFN 2004",
        "description": "An Act to make provision for declaring a person bankrupt and for matters connected therewith.",
        "out_file": "bankruptcy_act.json"
    },
    {
        "md_path": "2004/factories-act-cap-f1-lfn-2004.md",
        "statute_id": "factories_act",
        "title": "Factories Act",
        "short_title": "Factories Act",
        "year": 1987,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. F1, LFN 2004",
        "description": "An Act to provide for the registration and inspection of factories and the health, safety and welfare of persons employed in factories.",
        "out_file": "factories_act.json"
    },
    {
        "md_path": "2004/foreign-exchange-monitoring-and-miscellaneous-provisions-act-cap-f34-lfn-2004.md",
        "statute_id": "foreign_exchange_act",
        "title": "Foreign Exchange (Monitoring and Miscellaneous Provisions) Act",
        "short_title": "Foreign Exchange (FEMMPA) Act",
        "year": 1995,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. F34, LFN 2004",
        "description": "An Act to establish an Autonomous Foreign Exchange Market and provide for the monitoring and supervision of transactions conducted in the market.",
        "out_file": "foreign_exchange_femmpa_act.json"
    },
    {
        "md_path": "2004/national-insurance-commission-act-cap-n53-lfn-2004.md",
        "statute_id": "naicom_insurance_commission_act",
        "title": "National Insurance Commission Act",
        "short_title": "NAICOM Act",
        "year": 1997,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N53, LFN 2004",
        "description": "An Act to establish the National Insurance Commission to ensure the effective administration, supervision, regulation and control of insurance business in Nigeria.",
        "out_file": "naicom_insurance_commission_act.json"
    },
    {
        "md_path": "2004/marine-insurance-act-cap-m2-lfn-2004.md",
        "statute_id": "marine_insurance_act",
        "title": "Marine Insurance Act",
        "short_title": "Marine Insurance Act",
        "year": 1961,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. M2, LFN 2004",
        "description": "An Act to codify the law relating to marine insurance.",
        "out_file": "marine_insurance_act.json"
    },
    {
        "md_path": "2004/national-broadcasting-commission-act-cap-n11-lfn-20041.md",
        "statute_id": "national_broadcasting_commission_act",
        "title": "National Broadcasting Commission Act",
        "short_title": "NBC Act",
        "year": 1992,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N11, LFN 2004",
        "description": "An Act to establish the National Broadcasting Commission and regulate broadcasting activities in Nigeria.",
        "out_file": "national_broadcasting_commission_act.json"
    },
    {
        "md_path": "2004/niger-delta-development-commission-establishment-etc-act-cap-n86-lfn-2004.md",
        "statute_id": "nddc_act_2000",
        "title": "Niger Delta Development Commission (Establishment etc.) Act, 2000",
        "short_title": "NDDC Act",
        "year": 2000,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N86, LFN 2004 / Act No. 6 of 2000",
        "description": "An Act to establish the Niger Delta Development Commission for the development and rehabilitation of the oil producing areas of the Niger Delta.",
        "out_file": "nddc_act_2000.json"
    },
    {
        "md_path": "2004/armed-forces-act-cap-a20-lfn-2004.md",
        "statute_id": "armed_forces_act",
        "title": "Armed Forces Act",
        "short_title": "Armed Forces Act",
        "year": 1993,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. A20, LFN 2004",
        "description": "An Act to consolidate and amend the laws relating to the Armed Forces of the Federation.",
        "out_file": "armed_forces_act.json"
    },
    {
        "md_path": "2004/industrial-training-fund-act-cap-i9-lfn-2004.md",
        "statute_id": "industrial_training_fund_act",
        "title": "Industrial Training Fund Act",
        "short_title": "ITF Act",
        "year": 1971,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. I9, LFN 2004",
        "description": "An Act to establish the Industrial Training Fund to promote and encourage the acquisition of skills in industry and commerce.",
        "out_file": "industrial_training_fund_act.json"
    },
    {
        "md_path": "2004/nigeria-social-insurance-trust-fund-act-cap-n88-lfn-2004.md",
        "statute_id": "nsitf_act",
        "title": "Nigeria Social Insurance Trust Fund Act",
        "short_title": "NSITF Act",
        "year": 1993,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N88, LFN 2004",
        "description": "An Act to establish the Nigeria Social Insurance Trust Fund and provide a scheme for employees in the private sector.",
        "out_file": "nsitf_act.json"
    },
    {
        "md_path": "2007/nigerian-minerals-and-mining-act-2007.md",
        "statute_id": "minerals_mining_act_2007",
        "title": "Nigerian Minerals and Mining Act, 2007",
        "short_title": "Minerals and Mining Act",
        "year": 2007,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 20 of 2007",
        "description": "An Act to repeal the Minerals and Mining Act 1999 and regulate all mineral operations, exploration, and mining rights in Nigeria.",
        "out_file": "minerals_mining_act_2007.json"
    },
    {
        "md_path": "2005/national-lottery-act-2005-no-7-2005.md",
        "statute_id": "national_lottery_act_2005",
        "title": "National Lottery Act, 2005",
        "short_title": "National Lottery Act",
        "year": 2005,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 7 of 2005",
        "description": "An Act to regulate the operation of national lottery and create the National Lottery Regulatory Commission.",
        "out_file": "national_lottery_act_2005.json"
    },
    {
        "md_path": "2017/secured-transactions-in-movable-assets-act-2017-collateral-registry-act.md",
        "statute_id": "stma_act_2017",
        "title": "Secured Transactions in Movable Assets Act, 2017",
        "short_title": "STMA (Collateral Registry) Act",
        "year": 2017,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 3 of 2017",
        "description": "An Act to facilitate access to credit by creating a legal framework for the security interests in movable assets and the establishment of the National Collateral Registry.",
        "out_file": "stma_collateral_registry_act_2017.json"
    },
    {
        "md_path": "2004/banks-and-other-financial-institutions-act-cap-b-3-lfn-2004.md",
        "statute_id": "bofia_act",
        "title": "Banks and Other Financial Institutions Act",
        "short_title": "BOFIA",
        "year": 1991,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. B3, LFN 2004",
        "description": "An Act to regulate banking and other financial institutions and provide for matters connected therewith.",
        "out_file": "bofia_act.json"
    },
    {
        "md_path": "2007/chartered-institute-of-bankers-of-nigeria-act-2007-cap-c8-lfn-2004.md",
        "statute_id": "cibn_act",
        "title": "Chartered Institute of Bankers of Nigeria Act, 2007",
        "short_title": "CIBN Act",
        "year": 2007,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. C8, LFN 2004 / Act No. 5 of 2007",
        "description": "An Act to establish the Chartered Institute of Bankers of Nigeria to determine the standards of knowledge and skill to be attained by persons seeking to become members of the banking profession.",
        "out_file": "cibn_act.json"
    },
    {
        "md_path": "2004/sheriff-and-civil-process-act-cap-s6-lfn-2004.md",
        "statute_id": "sheriffs_civil_process_act",
        "title": "Sheriffs and Civil Process Act",
        "short_title": "Sheriffs and Civil Process Act",
        "year": 1945,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. S6, LFN 2004",
        "description": "An Act to make provision for the appointment and duties of sheriffs, the enforcement of judgments and orders, and the service and execution of civil process.",
        "out_file": "sheriffs_civil_process_act.json"
    },
    {
        "md_path": "2004/matrimonial-causes-act-cap-m7-lfn-2004.md",
        "statute_id": "matrimonial_causes_act",
        "title": "Matrimonial Causes Act",
        "short_title": "Matrimonial Causes Act",
        "year": 1970,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. M7, LFN 2004",
        "description": "An Act to make provision for matrimonial causes and other matrimonial proceedings.",
        "out_file": "matrimonial_causes_act.json"
    },
    {
        "md_path": "2004/pension-reform-act-no-2-2004.md",
        "statute_id": "pension_reform_act",
        "title": "Pension Reform Act",
        "short_title": "Pension Reform Act",
        "year": 2004,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. P4, LFN 2004 / Act No. 2 of 2004",
        "description": "An Act to establish a contributory pension scheme for employees in the public and private sectors in the Federal Republic of Nigeria.",
        "out_file": "pension_reform_act.json"
    },
    {
        "md_path": "2004/nigerian-ports-authority-act-cap-n126-lfn-2004.md",
        "statute_id": "npa_act",
        "title": "Nigerian Ports Authority Act",
        "short_title": "NPA Act",
        "year": 1999,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N126, LFN 2004",
        "description": "An Act to provide for the Nigerian Ports Authority and provide for the operation and management of ports in Nigeria.",
        "out_file": "nigerian_ports_authority_act.json"
    },
    {
        "md_path": "2004/federal-road-safety-commission-act-cap-f19-lfn-2004.md",
        "statute_id": "frsc_act",
        "title": "Federal Road Safety Commission Act",
        "short_title": "FRSC Act",
        "year": 1988,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. F19, LFN 2004",
        "description": "An Act to establish the Federal Road Safety Commission with functions relating to road traffic safety management and administration.",
        "out_file": "frsc_act.json"
    },
    {
        "md_path": "2004/failed-banks-recovery-of-debts-and-financial-malpractices-in-banks-act-cap-f2-lfn-2004.md",
        "statute_id": "failed_banks_act",
        "title": "Failed Banks (Recovery of Debts) and Financial Malpractices in Banks Act",
        "short_title": "Failed Banks Act",
        "year": 1994,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. F2, LFN 2004",
        "description": "An Act to establish a tribunal for the recovery of debts owed to failed banks and for the trial of offences relating to financial malpractices in banks.",
        "out_file": "failed_banks_act.json"
    },
    {
        "md_path": "2004/extradition-act-cap-e25-lfn-2004.md",
        "statute_id": "extradition_act",
        "title": "Extradition Act",
        "short_title": "Extradition Act",
        "year": 1966,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. E25, LFN 2004",
        "description": "An Act to repeal the Extradition Act 1962 and make more comprehensive provision for the extradition of fugitive offenders.",
        "out_file": "extradition_act.json"
    },
    {
        "md_path": "2004/legal-aid-act-cap-l9-lfn-2004.md",
        "statute_id": "legal_aid_act",
        "title": "Legal Aid Act",
        "short_title": "Legal Aid Act",
        "year": 1976,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. L9, LFN 2004",
        "description": "An Act to establish a Legal Aid Council to provide free legal representation and advice to persons with inadequate resources.",
        "out_file": "legal_aid_act.json"
    },
    {
        "md_path": "2004/public-complaints-commission-act-cap-p37-lfn-2004.md",
        "statute_id": "public_complaints_commission_act",
        "title": "Public Complaints Commission Act",
        "short_title": "Public Complaints Commission Act",
        "year": 1975,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. P37, LFN 2004",
        "description": "An Act to establish the Public Complaints Commission with powers to investigate administrative actions of government ministries and agencies.",
        "out_file": "public_complaints_commission_act.json"
    },
    {
        "md_path": "2004/mortgage-institutions-act-cap-m19-lfn-2004.md",
        "statute_id": "mortgage_institutions_act",
        "title": "Mortgage Institutions Act",
        "short_title": "Mortgage Institutions Act",
        "year": 1989,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. M19, LFN 2004",
        "description": "An Act to regulate the establishment and operation of mortgage institutions in Nigeria.",
        "out_file": "mortgage_institutions_act.json"
    },
    {
        "md_path": "2004/federal-mortgage-bank-of-nigeria-act-cap-f16-lfn-2004.md",
        "statute_id": "fmbn_act",
        "title": "Federal Mortgage Bank of Nigeria Act",
        "short_title": "FMBN Act",
        "year": 1993,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. F16, LFN 2004",
        "description": "An Act to establish the Federal Mortgage Bank of Nigeria and provide for its functions and powers.",
        "out_file": "fmbn_act.json"
    },
    {
        "md_path": "2004/national-health-insurance-scheme-act-cap-n42-lfn-2004.md",
        "statute_id": "nhis_act",
        "title": "National Health Insurance Scheme Act",
        "short_title": "NHIS Act",
        "year": 1999,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N42, LFN 2004",
        "description": "An Act to establish the National Health Insurance Scheme for the purpose of providing health insurance to all Nigerians.",
        "out_file": "nhis_act.json"
    },
    {
        "md_path": "2004/national-directorate-of-employment-act-cap-n28-lfn-2004.md",
        "statute_id": "nde_act",
        "title": "National Directorate of Employment Act",
        "short_title": "NDE Act",
        "year": 1989,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N28, LFN 2004",
        "description": "An Act to establish the National Directorate of Employment to combat unemployment in Nigeria.",
        "out_file": "nde_act.json"
    },
    {
        "md_path": "2004/quarantine-act-cap-q2-lfn-2004.md",
        "statute_id": "quarantine_act",
        "title": "Quarantine Act",
        "short_title": "Quarantine Act",
        "year": 1926,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. Q2, LFN 2004",
        "description": "An Act to provide for and regulate the imposition of quarantine and to make other provision for preventing the introduction and spread in Nigeria of dangerous infectious disease.",
        "out_file": "quarantine_act.json"
    },
    {
        "md_path": "2004/federal-airports-authority-of-nigeria-act-cap-f5-lfn-2004.md",
        "statute_id": "faan_act",
        "title": "Federal Airports Authority of Nigeria Act",
        "short_title": "FAAN Act",
        "year": 1996,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. F5, LFN 2004",
        "description": "An Act to establish the Federal Airports Authority of Nigeria for the operation and maintenance of all federal airports.",
        "out_file": "faan_act.json"
    },
    {
        "md_path": "2007/nigeria-security-and-civil-defense-corps-act-2007.md",
        "statute_id": "nscdc_act_2007",
        "title": "Nigeria Security and Civil Defence Corps Act, 2007",
        "short_title": "NSCDC Act",
        "year": 2007,
        "gazette_number": "Laws of the Federation of Nigeria / Act No. 6 of 2007",
        "description": "An Act to amend the Nigeria Security and Civil Defence Corps Act 2003 and confer additional powers and mandates on the Corps.",
        "out_file": "nscdc_act_2007.json"
    },
    {
        "md_path": "2006/national-oil-spill-detection-and-response-agency-establishment-act-2006-no-15-2006.md",
        "statute_id": "nosdra_act_2006",
        "title": "National Oil Spill Detection and Response Agency (Establishment) Act, 2006",
        "short_title": "NOSDRA Act",
        "year": 2006,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 15 of 2006",
        "description": "An Act to establish the National Oil Spill Detection and Response Agency to coordinate oil spill response and management.",
        "out_file": "nosdra_act_2006.json"
    },
    {
        "md_path": "2007/merchant-shipping-act-no-27-2007.md",
        "statute_id": "merchant_shipping_act_2007",
        "title": "Merchant Shipping Act, 2007",
        "short_title": "Merchant Shipping Act",
        "year": 2007,
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 27 of 2007",
        "description": "An Act to repeal the Merchant Shipping Act 1962 and provide for merchant shipping and maritime matters in Nigeria.",
        "out_file": "merchant_shipping_act_2007.json"
    },
    {
        "md_path": "2004/national-security-agencies-act-cap-n74-lfn-2004.md",
        "statute_id": "national_security_agencies_act",
        "title": "National Security Agencies Act",
        "short_title": "National Security Agencies Act",
        "year": 1986,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. N74, LFN 2004",
        "description": "An Act to establish three security agencies for the Federation: the Defence Intelligence Agency, the National Intelligence Agency, and the State Security Service (DSS).",
        "out_file": "national_security_agencies_act.json"
    },
    {
        "md_path": "2004/bank-employees-etc-declaration-of-assets-act-cap-b1-lfn-2004.md",
        "statute_id": "bank_employees_declaration_of_assets_act",
        "title": "Bank Employees, etc. (Declaration of Assets) Act",
        "short_title": "Bank Employees Declaration Act",
        "year": 1986,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. B1, LFN 2004",
        "description": "An Act to make provision for the declaration of assets by employees of banks and other financial institutions.",
        "out_file": "bank_employees_declaration_of_assets_act.json"
    },
    {
        "md_path": "2004/corrupt-practices-and-other-related-offences-act-cap-c31-lfn-2004.md",
        "statute_id": "corrupt_practices_act",
        "title": "Corrupt Practices and Other Related Offences Act",
        "short_title": "Corrupt Practices (ICPC) Act",
        "year": 2000,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. C31, LFN 2004 / Act No. 5 of 2000",
        "description": "An Act to prohibit and prescribe punishment for corrupt practices and other related offences and establish the Independent Corrupt Practices and Other Related Offences Commission.",
        "out_file": "corrupt_practices_icpc_act.json"
    },
    {
        "md_path": "2004/trustee-investments-act-cap-t22-lfn-2004.md",
        "statute_id": "trustee_investments_act",
        "title": "Trustee Investments Act",
        "short_title": "Trustee Investments Act",
        "year": 1957,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. T22, LFN 2004",
        "description": "An Act to facilitate the investment of trust and other funds in Nigeria in locally issued securities.",
        "out_file": "trustee_investments_act.json"
    },
    {
        "md_path": "2004/venture-capital-incentives-act-cap-v2-lfn-2004.md",
        "statute_id": "venture_capital_incentives_act",
        "title": "Venture Capital (Incentives) Act",
        "short_title": "Venture Capital Incentives Act",
        "year": 1993,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. V2, LFN 2004",
        "description": "An Act to provide for venture capital incentives and tax relief for venture capital companies.",
        "out_file": "venture_capital_incentives_act.json"
    },
    {
        "md_path": "2004/water-resources-act-cap-w2-lfn-2004.md",
        "statute_id": "water_resources_act",
        "title": "Water Resources Act",
        "short_title": "Water Resources Act",
        "year": 1993,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. W2, LFN 2004",
        "description": "An Act to promote the optimum planning, development and use of the Nigeria water resources.",
        "out_file": "water_resources_act.json"
    },
    {
        "md_path": "2004/tribunals-of-inquiry-act-cap-t21-lfn-2004.md",
        "statute_id": "tribunals_of_inquiry_act",
        "title": "Tribunals of Inquiry Act",
        "short_title": "Tribunals of Inquiry Act",
        "year": 1966,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. T21, LFN 2004",
        "description": "An Act to empower the President or Head of State to constitute a tribunal of inquiry into any matter in respect of which the National Assembly has power to make laws.",
        "out_file": "tribunals_of_inquiry_act.json"
    },
    {
        "md_path": "2004/treaties-making-procedure-etc-act-cap-t20-lfn-2004.md",
        "statute_id": "treaties_making_procedure_act",
        "title": "Treaties (Making Procedure, etc.) Act",
        "short_title": "Treaties Procedure Act",
        "year": 1993,
        "gazette_number": "Laws of the Federation of Nigeria, Cap. T20, LFN 2004",
        "description": "An Act to regulate the procedure for making treaties, ratification and incorporation of international agreements.",
        "out_file": "treaties_making_procedure_act.json"
    }
]

def parse_and_save_statute(manifest):
    md_path = manifest["md_path"]
    statute_id = manifest["statute_id"]
    title = manifest["title"]
    short_title = manifest["short_title"]
    year = manifest["year"]
    gazette_number = manifest["gazette_number"]
    description = manifest["description"]
    out_file = manifest["out_file"]
    
    url = f"https://raw.githubusercontent.com/mykeels/nigerian-laws/master/{md_path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw_md = urllib.request.urlopen(req, timeout=25).read().decode("utf-8")
    raw_md = raw_md.replace("\xa0", " ")
    
    # 1. Split TOC and Body using comprehensive enactment anchors
    enact_matches = list(re.finditer(r"\b(?:ENACTED by|Commencement\b\s*[\(\[]|An Act to|decrees as follows|hereby decrees|BE IT ENACTED)\b", raw_md, re.IGNORECASE))
    if len(enact_matches) > 1:
        enact_idx = enact_matches[-1].end()
    elif enact_matches:
        enact_idx = enact_matches[0].end()
    else:
        enact_idx = 0
        
    toc_text = raw_md[:enact_idx]
    body_text = raw_md[enact_idx:]
    
    # 2. Extract TOC titles (supports single-line and multiline)
    toc_matches = re.findall(r"^\s*(\d{1,3})\.\s*(?:\n+\s*)?([^\n\r]+)", toc_text, re.MULTILINE)
    titles_map = {}
    for s_num_str, s_title in toc_matches:
        s_num = int(s_num_str)
        cleaned_t = s_title.strip().rstrip(".")
        if s_num not in titles_map and not cleaned_t.startswith("There is") and not cleaned_t.startswith("(") and len(cleaned_t) < 120:
            titles_map[s_num] = cleaned_t
            
    # 3. Locate Section boundaries in Body
    body_lines = [l.strip() for l in body_text.splitlines()]
    
    sec_hits = []
    for line_idx, line in enumerate(body_lines):
        m_head = re.match(r"^###\s+(?:Section\s+)?(\d{1,3})\b|^###\s+(\d{1,3})\.\s*", line, re.IGNORECASE)
        m_line = re.match(r"^(\d{1,3})\s*[\.\(]", line)
        if m_head:
            s_num = int(m_head.group(1) or m_head.group(2))
            sec_hits.append((s_num, line_idx))
        elif m_line:
            s_num = int(m_line.group(1))
            sec_hits.append((s_num, line_idx))
            
    distinct_secs = {}
    max_expected = max(titles_map.keys()) if titles_map else 999
    for s_num, l_idx in sec_hits:
        if s_num not in distinct_secs:
            if not titles_map or s_num <= max_expected + 5:
                distinct_secs[s_num] = l_idx
            
    sorted_secs = sorted(distinct_secs.items(), key=lambda x: x[0])
    
    sections_json = []
    for i, (s_num, l_idx) in enumerate(sorted_secs):
        next_l_idx = sorted_secs[i+1][1] if i + 1 < len(sorted_secs) else len(body_lines)
        chunk_lines = body_lines[l_idx:next_l_idx]
        
        filtered_lines = []
        for l in chunk_lines:
            if re.match(r"^###\s+(?:Section\s+)?\d+\b", l, re.IGNORECASE):
                continue
            if re.match(r"^###\s+PART\s+[IVXLCDM\d]+", l, re.IGNORECASE):
                continue
            filtered_lines.append(l)
            
        raw_sec_text = "\n".join(filtered_lines).strip()
        
        f_lines = raw_sec_text.splitlines()
        if f_lines:
            first = f_lines[0].strip()
            sec_title = titles_map.get(s_num, "")
            if sec_title and re.match(rf"^{s_num}\.\s+{re.escape(sec_title)}", first, re.IGNORECASE):
                f_lines = f_lines[1:]
            elif re.match(rf"^{s_num}\s*\(\s*1\s*\)\s*\.?", first):
                f_lines[0] = "(1) " + first[re.match(rf"^{s_num}\s*\(\s*1\s*\)\s*\.?", first).end():].strip()
            elif re.match(rf"^{s_num}\s*[\.\(]\s*", first):
                remainder = first[re.match(rf"^{s_num}\s*[\.\(]\s*", first).end():].strip()
                if not remainder.startswith("(") and not remainder.startswith("The") and not remainder.startswith("A ") and not remainder.startswith("Subject"):
                    remainder = f"({remainder}" if not remainder.startswith("(") else remainder
                f_lines[0] = remainder
            raw_sec_text = "\n".join(f_lines).strip()
            
        cleaned_body = clean_and_reflow_legal_text(raw_sec_text)
        if not cleaned_body or len(cleaned_body) < 10:
            cleaned_body = f"Section {s_num} of the {title}."
            
        final_title = titles_map.get(s_num, f"Section {s_num}")
        
        sections_json.append({
            "section_number": str(s_num),
            "section_title": final_title,
            "part": "General Provisions",
            "full_text": cleaned_body,
            "searchable_chunk": f"{title} - Section {s_num}: {final_title}\nGeneral Provisions\n{cleaned_body}"
        })
        
    final_manifest = {
        "statute_id": statute_id,
        "title": title,
        "short_title": short_title,
        "year": year,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": gazette_number,
        "enactment_date": f"{year}",
        "description": description,
        "total_sections": len(sections_json),
        "sections": sections_json
    }
    
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "json_laws", out_file)
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(final_manifest, fp, indent=2, ensure_ascii=False)
        
    return len(sections_json), max(titles_map.keys()) if titles_map else len(sections_json)


def run_batch_ingestion():
    print(f"[*] Beginning Ingestion of {len(STATUTE_MANIFESTS)} Landmark Nigerian Statutes...")
    total_added_sections = 0
    statutes_added = 0
    
    for m in STATUTE_MANIFESTS:
        try:
            count, expected = parse_and_save_statute(m)
            if count > 0:
                statutes_added += 1
                total_added_sections += count
                print(f"    [✓] Ingested: {m['short_title']:35s} | {count:3d}/{expected:3d} sections saved")
            else:
                print(f"    [!] Warning: {m['short_title']} returned 0 sections")
        except Exception as e:
            print(f"    [✗] Error processing {m['short_title']}: {e}")
            
    print(f"\n[✓] INGESTION COMPLETE! Successfully ingested {total_added_sections} sections across {statutes_added} statutes.")


if __name__ == "__main__":
    run_batch_ingestion()
