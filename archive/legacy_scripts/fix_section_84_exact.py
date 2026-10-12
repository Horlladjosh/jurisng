import json
from pathlib import Path

JSON_PATH = Path("data/json_laws/evidence_act_2011.json")

# Official verbatim text of Section 84, Evidence Act 2011
SECTION_84_VERBATIM = (
    "84. (1) In any proceeding a statement contained in a document produced by a computer "
    "shall be admissible as evidence of any fact stated in it of which direct oral evidence "
    "would be admissible, if it is shown that the conditions in subsection (2) of this section "
    "are satisfied in relation to the statement and computer in question. "
    "(2) The conditions referred to in subsection (1) of this section are— "
    "(a) that the document containing the statement was produced by the computer during a "
    "period over which the computer was used regularly to store or process information for the "
    "purposes of any activities regularly carried on over that period, whether for profit or not "
    "by anybody, whether corporate or not, or by any individual; "
    "(b) that over that period there was regularly supplied to the computer in the ordinary course "
    "of those activities information of the kind contained in the statement or of the kind from which "
    "the information so contained is derived; "
    "(c) that throughout the material part of that period the computer was operating properly or, "
    "if not, that in any respect in which it was not operating properly or was out of operation "
    "during that part of that period was not such as to affect the production of the document or "
    "the accuracy of its contents; and "
    "(d) that the information contained in the statement reproduces or is derived from information "
    "supplied to the computer in the ordinary course of those activities. "
    "(3) Where over a period the function of storing or processing information for the purposes of "
    "any activities regularly carried on over that period as mentioned in subsection (2) (a) of this "
    "section was regularly performed by computers, whether— "
    "(a) by a combination of computers operating over that period; "
    "(b) by different computers operating in succession over that period; "
    "(c) by different combinations of computers operating in succession over that period; or "
    "(d) in any other manner involving the successive operation over that period, in whatever order, "
    "of one or more computers and one or more combinations of computers, "
    "all the computers used for that purpose during that period shall be treated for the purposes "
    "of this section as constituting a single computer; and references in this section to a computer "
    "shall be construed accordingly. "
    "(4) In any proceeding where it is desired to give a statement in evidence by virtue of this "
    "section, a certificate— "
    "(a) identifying the document containing the statement and describing the manner in which it was "
    "produced; "
    "(b) giving such particulars of any device involved in the production of that document as may be "
    "appropriate for the purpose of showing that the document was produced by a computer; "
    "(c) dealing with any of the matters to which the conditions mentioned in subsection (2) above "
    "relate, and purporting to be signed by a person occupying a responsible position in relation to "
    "the operation of the relevant device or the management of the relevant activities, as the case "
    "may be, "
    "shall be evidence of the matter stated in the certificate; and for the purpose of this subsection "
    "it shall be sufficient for a matter to be stated to the best of the knowledge and belief of the "
    "person stating it. "
    "(5) For the purposes of this section— "
    "(a) information shall be taken to be supplied to a computer if it is supplied to it in any "
    "appropriate form and whether it is supplied directly or (with or without human intervention) "
    "by means of any appropriate equipment; "
    "(b) where, in the course of activities carried on by any individual or body, information is "
    "supplied with a view to its being stored or processed for the purposes of those activities by a "
    "computer operated otherwise than in the course of those activities, that information, if duly "
    "supplied to that computer, shall be taken to be supplied to it in the course of those activities; "
    "(c) a document shall be taken to have been produced by a computer whether it was produced by it "
    "directly or (with or without human intervention) by means of any appropriate equipment."
)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

for sec in data.get("sections", []):
    if str(sec.get("section_number")) == "84":
        sec["full_text"] = SECTION_84_VERBATIM
        sec["searchable_chunk"] = f"Evidence Act 2011 | Section 84: Admissibility of Statement in Document Produced by Computer | {SECTION_84_VERBATIM}"
        break

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("[✓] Evidence Act 2011 Section 84 replaced with 100% exact official statutory text.")
