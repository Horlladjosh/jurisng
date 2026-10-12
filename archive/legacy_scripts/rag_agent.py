import sys
from advanced_retriever import ProductionLegalRetriever

class LegalRAGAdvisor:
    def __init__(self):
        self.retriever = ProductionLegalRetriever()

    def format_legal_advice(self, query: str, top_k: int = 2) -> str:
        results = self.retriever.search(query, top_k=top_k)
        if not results:
            return "No relevant statutory provisions found."

        output = []
        output.append(f"\n=======================================================")
        output.append(f"LEGAL INQUIRY: \"{query}\"")
        output.append(f"=======================================================\n")
        output.append("### APPLICABLE NIGERIAN STATUTORY PROVISIONS\n")

        for idx, item in enumerate(results, 1):
            statute = item["statute_title"]
            sec_num = item["section_number"]
            title = item["section_title"]
            text = item["full_text"].strip()
            
            output.append(f"**{idx}. {statute} — Section {sec_num}: {title}**")
            output.append(f"> {text}\n")

        output.append("### SUMMARY OF LEGAL POSITION")
        
        # Scenario synthesis based on retrieved top match
        top_match = results[0]
        sec_num = str(top_match["section_number"])
        stat_title = top_match["statute_title"]

        if sec_num == "32":
            summary = (
                "Under Section 32(2) of the Nigeria Police Act 2020, the police are expressly "
                "prohibited from arresting any person for a civil wrong or breach of contract (such as unpaid rent or civil debts). "
                "Debt recovery is strictly a civil matter within the jurisdiction of the civil courts."
            )
        elif sec_num == "36":
            summary = (
                "Under Section 36 of the Nigeria Police Act 2020, 'arrest in lieu' (substitute arrest) is strictly illegal. "
                "Police officers cannot arrest a relative, friend, or proxy in place of a suspect."
            )
        elif sec_num in ["62", "64"]:
            summary = (
                "Under Sections 62 and 64 of the Nigeria Police Act 2020 (and Section 35 CFRN 1999), a suspect arrested without a warrant "
                "for a non-capital offence must be granted administrative bail within 24 hours, or brought before a court of competent jurisdiction."
            )
        elif sec_num == "54":
            summary = (
                "Under Section 54 of the Nigeria Police Act 2020, personal attributes including hairstyle (such as dreadlocks), "
                "tattoos, or manner of dress do not constitute reasonable suspicion for a stop-and-search."
            )
        else:
            summary = f"Refer directly to {stat_title}, Section {sec_num} for the governing procedural requirements."

        output.append(summary)
        output.append("\n" + "=" * 55)
        return "\n".join(output)

if __name__ == "__main__":
    advisor = LegalRAGAdvisor()
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "My landlord brought police to arrest me for 3 months unpaid rent."
    print(advisor.format_legal_advice(query))
