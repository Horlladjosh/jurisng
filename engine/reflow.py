import re
import unicodedata

STRUCTURAL_PATTERN = r'^(\(\d+\)|\([a-z]\)|\([ivx]+\)|\([A-Z]\)|\[[A-Z0-9]|Provided\s+that|Provided\s+further|Provided\s+always|"[^"]+"\s+(?:means|includes|refers)|FIRST\s+SCHEDULE|SECOND\s+SCHEDULE|THIRD\s+SCHEDULE|FOURTH\s+SCHEDULE|FIFTH\s+SCHEDULE|SIXTH\s+SCHEDULE|SEVENTH\s+SCHEDULE|TABLE\s+[I|V|X]+|PART\s+[I|V|X]+|CHAPTER\s+\d+)'

OCR_REPLACEMENTS = [
    (r'\bNigena\b', 'Nigeria'),
    (r'\bNi\s*[-‐‑]\s*gena\b', 'Nigeria'),
    (r'\bNi\s*[-‐‑]\s*geria\b', 'Nigeria'),
    (r'\bNi\s*[-‐‑]\s+geria\b', 'Nigeria'),
    (r'\brvith\b', 'with'),
    (r'\btbe\b', 'the'),
    (r'\bsec- tion\b', 'section'),
    (r'\bsub- section\b', 'subsection'),
    (r'\bpara- graph\b', 'paragraph'),
]

def normalize_unicode(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text)
    # Replace weird unicode spaces, tabs, carriage returns, and hyphens
    text = re.sub(r'[\u00a0\u200b\u200c\u200d\u2011\u2012\u2013\u2014\u2015\u2212\xad\t\r]', ' ', text)
    return text

def reflow_statutory_text(raw_text: str) -> str:
    if not raw_text:
        return ""

    text = normalize_unicode(raw_text)

    # 1. Clean digit OCR space artifacts: "section 4 50" -> "section 450"
    def fix_digit_space(m):
        return f"{m.group(1)}{m.group(2)}{m.group(3)}"

    text = re.sub(r'\b(section\s+)(\d{1,3})\s+(\d{1,2})\b', fix_digit_space, text, flags=re.I)
    text = re.sub(r'\b(sections\s+)(\d{1,3})\s+(\d{1,2})\b', fix_digit_space, text, flags=re.I)

    # Clean orphan dots / punctuation from stripped marginal titles: e.g. "of . corporate" -> "of corporate"
    text = re.sub(r'\s+[\.|\,]\s+', ' ', text)
    text = re.sub(r';\s*or\s*\.\s*', '; or\n\n', text, flags=re.I)

    # 2. Normalize linebreaks and structural paragraphs
    raw_lines = text.split('\n')
    lines = []
    for l in raw_lines:
        clean_line = re.sub(r'[ \t]{2,}', ' ', l).strip()
        if clean_line:
            lines.append(clean_line)

    refined_paragraphs = []
    current_para = ''

    for line in lines:
        is_new_block = bool(re.match(STRUCTURAL_PATTERN, line, re.I))

        if is_new_block:
            if current_para:
                refined_paragraphs.append(current_para)
            current_para = line
        else:
            if current_para:
                if current_para.endswith('-') or current_para.endswith('‐'):
                    current_para = current_para[:-1] + line
                else:
                    current_para += ' ' + line
            else:
                current_para = line

    if current_para:
        refined_paragraphs.append(current_para)

    text = '\n\n'.join(refined_paragraphs)

    # 3. Apply OCR typos correction
    for pattern, repl in OCR_REPLACEMENTS:
        text = re.sub(pattern, repl, text, flags=re.I)

    # Clean multi-spaces inside paragraphs
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()
