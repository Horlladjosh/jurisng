import os
import warnings
import sys

# Silence OpenSSL and deprecation warnings
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from advanced_retriever import ProductionLegalRetriever

def run_chat():
    print("=" * 65)
    print("NIGERIAN LEGAL RETRIEVAL & ADVISORY ENGINE (CLI)")
    print("Statutes Indexed: CFRN 1999 (320 Secs), Police Act 2020 (142 Secs)")
    print("Type your legal question below. Type 'exit' or 'quit' to end.")
    print("=" * 65 + "\n")

    retriever = ProductionLegalRetriever()
    print("\nEngine ready! Ask a scenario question:\n")

    while True:
        try:
            query = input("\033[1;34mLegal Question > \033[0m").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("\nExiting Nigerian Law Engine. Goodbye!")
                break

            print("\nSearching statutory corpus...")
            results = retriever.search(query, top_k=2)

            print("\n" + "=" * 65)
            print(f"RELEVANT STATUTORY PROVISIONS:")
            print("=" * 65)

            for idx, item in enumerate(results, 1):
                statute = item["statute_title"]
                sec_num = item["section_number"]
                title = item["section_title"]
                text = item["full_text"].strip()
                score = item["rerank_score"]

                print(f"\n\033[1;32m[{idx}] {statute} — Section {sec_num}: {title}\033[0m (Score: {score:.2f})")
                print(f"\"\"\"\n{text[:400]}...\n\"\"\"")

            print("\n" + "-" * 65 + "\n")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

if __name__ == "__main__":
    run_chat()
