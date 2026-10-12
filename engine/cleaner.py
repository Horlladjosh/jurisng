"""
Nigerian Law Engine - Statutory Text Sanitation & Cleaning Engine
Option A: Pure Enactment Extraction.

Strips:
1. Web scraping provenance links and watermarks (e.g., LawNigeria, PLAC footer tags).
2. End-of-act subsidiary legislation placeholder blocks.
3. Post-enactment attestation/certification formulas under the Acts Authentication Act.
4. Clerk to the National Assembly signature and date lines at the tail of sections.
5. Presidential assent blocks (e.g., "I Assent...", President signatures).
6. Explanatory Memoranda and Notes appended to citations/tail sections.
"""

import re
import difflib
from typing import Tuple, Dict, Any

def _norm_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())

def clean_section_text(text: str, sec_title: str = "") -> str:
    """
    Sanitizes raw statutory section text to remove non-enactment PDF/web artifacts:
    - Scrape provenance watermarks and links (LawNigeria, PLAC).
    - End-of-act subsidiary legislation placeholder blocks.
    - Post-enactment attestation/certification under Acts Authentication Act.
    - Clerk to the National Assembly signature and date lines.
    - Presidential assent blocks.
    - Explanatory Memoranda and Notes.
    - LFN loose-leaf running page headers (e.g., [Issue 1], Ll-30 CAP.Ll, CAP.Ll stamps).
    - Glued OCR page numbers (e.g. sectionLl-4 -> section).
    - Redundant section title prefixes/headers duplicating the card header.
    - Common OCR glued words & typos (e.g., Subjection (1) -> Subsection (1), ofthis -> of this, to( a) -> to (a)).
    Guarantees that legitimate statutory text (like CFRN Sec 51 establishing the Clerk) is preserved.
    """
    if not text:
        return ""

    # 1. Scrape provenance footers (e.g., ## Reference ... Law Nigeria web page ...)
    text = re.sub(
        r"\n*##\s*Reference\s*\n+This document was obtained from.*$",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(
        r"\n*This document was obtained from \[this Law Nigeria.*$",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(
        r"\n*Source:\s*Policy and Legal Advocacy Centre.*$",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # 2. Subsidiary legislation placeholder at end of Acts
    text = re.sub(
        r"\n+_{0,}\s*SUBSIDIARY\s+LEGISLATION[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 3. Explanatory Note / Memorandum at the tail of sections
    text = re.sub(
        r"\n*#{1,4}\s*Explanatory\s+(?:Note|Memorandum)[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\n+(?:####\s*)?EXPLANATORY\s+MEMORANDUM[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 4. Evidence Act OCR variation ("Citation I CEIUIFY...")
    text = re.sub(
        r"\s*Citation\s+I\s+CEIUIFY[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 5. Acts Authentication certification blocks at the tail
    text = re.sub(
        r"\n+>\s*I\s+[Cc]ertify[\s\S]*?(?:Acts Authentication Act|Clerk to the National Assembly)[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\n+I\s+[Cc]ertify,?\s+in\s+[Aa]ccordance\s+with\s+[Ss]ection\s+2[\s\S]*?Acts\s+Authentication\s+Act[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 6. Clerk signature lines at tail
    text = re.sub(
        r"\n+(?:[A-Z][a-zA-Z\.\,\s\-]+(?:\n|\r\n))?Clerk\s+to\s+the\s+National\s+Assembly[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\n+CLERK\s+TO\s+THE\s+NATIONAL\s+ASSEMBL\s*Y[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 7. Presidential assent at tail
    text = re.sub(
        r"\n+I\s+Assent[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 8. Schedule / Parliamentary dates table at tail (e.g. Money Laundering Act Sec 31)
    text = re.sub(
        r"\n+\(4\)\s+Date\s+Passed\s+by\s+the\s+Senate[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\n+Date\s+passed\s+by\s+(?:Senate|House\s+of\s+Representatives)[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 9. LFN loose-leaf running page headers & loose-leaf artifacts
    # Glued page numbers like 'sectionLl-4'
    text = re.sub(r"(?<=[a-z])(?:Ll|LI|L1|LJ|L!|T14|Tl4|E14|El4)\s*[-–—~]\s*\d{1,3}", "", text)

    # Full running headers with CAP.<Code>
    page_code = r"(?:[A-Za-z0-9!]{1,4}\s*[\-–—~]\s*\d{1,3}\b)"
    issue_code = r"(?:[\(\[]?\s*(?:Issue|lssue|lssuc|1ssue)\s*[^\]\)\n\r]{0,12}[\]\)]?)"
    decor = r"[\-–—~_·\s]+"
    act_suffix = r"(?:\s+(?:National Drug Law Enforcement Agency|Trade Unions|Trude Unions|Labour|Trade Marks|Evidence|Personal Income Tax)\s*(?:Act)?)?"

    combined_header = re.compile(
        rf"(?:{page_code}\s*)?(?:{issue_code}\s*)?(?:{page_code}\s*)?"
        rf"(?:{decor})?"
        rf"\bCAP\.?\s*[A-Za-z0-9]{{1,4}}\b"
        rf"{act_suffix}",
        re.IGNORECASE,
    )

    def header_repl(m):
        span_end = m.end()
        after = text[span_end:span_end+40]
        # Preserve genuine statutory cross-references (e.g. Cap. A2, Laws of the Federation)
        if re.match(r"^\s*(?:,\s*)?(?:Laws\s+of|LFN|L\.F\.N|Edition|of\s+19\d\d|of\s+20\d\d)", after, re.IGNORECASE):
            return m.group(0)
        span_start = m.start()
        before = text[max(0, span_start-5):span_start]
        if "[" in before and "]" in after:
            return m.group(0)
        return " "

    text = combined_header.sub(header_repl, text)

    # Standalone loose-leaf CAP.<Code> at line end, sentence end, or before subsection
    # e.g., 'mine. CAP.Ll\n(2)' or '[Cap. 91 of 1958 Edition.] CAP.Ll'
    standalone_cap = re.compile(
        r"\s*\bCAP\.?(?:Ll|L1|LI|T14|Tl4|P8)\b(?=\s*(?:[\r\n]|\([0-9a-zA-Z]+\)|$))",
        re.IGNORECASE,
    )
    text = standalone_cap.sub("", text)

    # Clean orphan loose-leaf page numbers (like 'Ll-50', 'Ll-10', 'Tl4 -29')
    text = re.sub(
        r"\b(?:Ll|LI|L1|LJ|L!|T14|Tl4|E14|El4)\s*[-–—~]\s*\d{1,3}\b",
        "",
        text,
    )
    # Clean loose-leaf binding margins & excessive decorative dashes/dots
    text = re.sub(r"[\-–—~_·\.]{4,}", "", text)

    # 10. High-fidelity OCR repairs
    text = re.sub(r"\bSubjection\s*\((?=\d+\))", "Subsection (", text, flags=re.IGNORECASE)
    text = re.sub(r"\bofthis\b", "of this", text)
    text = re.sub(r"\bofthat\b", "of that", text)
    text = re.sub(r"\b(to|or|and|under|in|of)\(\s*([a-zA-Z0-9]+)\s*\)", r"\1 (\2)", text)
    text = re.sub(r"\(\s+([a-zA-Z0-9]+)\s*\)", r"(\1)", text)
    text = re.sub(r"\(\s*([a-zA-Z0-9]+)\s+\)", r"(\1)", text)

    # 11. Redundant section title stripping
    if sec_title:
        clean_title = sec_title.strip().rstrip(".").strip()
        n_title = _norm_title(clean_title)
        # Never strip if enactment itself starts with subsection in parentheses (e.g. '(1) There shall be...')
        if len(n_title) >= 3 and not re.match(r"^\s*\(", text):
            lines = text.split("\n")
            first_line = lines[0].strip()
            clean_first = re.sub(r"^[0-9]+[A-Za-z]?[\.\:\-\s]+", "", first_line).strip()
            if clean_first.startswith("(") and not clean_first.startswith("(1)") and not clean_first.startswith("(I)"):
                clean_first_stripped = clean_first.lstrip("(").rstrip(")").strip()
            else:
                clean_first_stripped = clean_first

            n_first = _norm_title(clean_first_stripped)
            # Case A: First line is solely the title (or minor OCR typo e.g. 'Undergronnd work')
            if n_first and len(lines) > 1 and difflib.SequenceMatcher(None, n_title, n_first).ratio() >= 0.8:
                text = "\n".join(lines[1:]).strip()
            else:
                # Case B: Title is prefixed on the same line before statutory text or subsection
                for split_len in range(max(3, len(clean_title) - 4), min(len(clean_first_stripped), len(clean_title) + 8)):
                    prefix = clean_first_stripped[:split_len].strip()
                    n_prefix = _norm_title(prefix)
                    if difflib.SequenceMatcher(None, n_title, n_prefix).ratio() >= 0.85:
                        remainder = clean_first[split_len:].strip()
                        m_sub = re.match(
                            r"^(?:[\(\[]\s*([0-9a-zA-Z!]+)\s*[\)\]]|\b(?:The|Where|Subject|In|Every|No|Any|A|An|All|Upon|Until|When|If|Unless|Except|Notwithstanding|It|There|Whoever|Nothing)\b)",
                            remainder,
                        )
                        if m_sub:
                            if remainder.startswith("(!)"):
                                remainder = "(1)" + remainder[3:]
                            elif remainder.startswith("( !)"):
                                remainder = "(1)" + remainder[4:]
                            rest_lines = ("\n" + "\n".join(lines[1:])) if len(lines) > 1 else ""
                            text = (remainder + rest_lines).strip()
                            break

    # 12. Spacing & trailing cleanup
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" \n", "\n", text)
    text = re.sub(r"\n+_{3,}\s*$", "", text)
    return text.strip()


def clean_statute_dict(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Cleans all sections in a statute dictionary.
    Returns: (cleaned_dict, number_of_modified_sections)
    """
    modified_count = 0
    short_title = data.get("short_title", data.get("statute_title", ""))

    sections = data.get("sections", [])
    for sec in sections:
        raw_text = sec.get("full_text", "")
        sec_title = sec.get("section_title", sec.get("title", ""))
        cleaned = clean_section_text(raw_text, sec_title=sec_title)
        if cleaned != raw_text:
            sec["full_text"] = cleaned
            sec_num = str(sec.get("section_number", ""))
            sec["searchable_chunk"] = f"{short_title} Sec {sec_num}: {sec_title}. {cleaned[:200]}"
            modified_count += 1

    return data, modified_count
