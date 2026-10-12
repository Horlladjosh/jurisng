import chromadb
from chromadb.utils import embedding_functions

def run_case_studies():
    client = chromadb.PersistentClient(path="data/vector_db")
    embed_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_collection(
        name="nigerian_statutes",
        embedding_function=embed_fn
    )

    test_scenarios = [
        {
            "scenario": "Case Study 1: Debt Collection & Civil Wrongs",
            "query": "My landlord called the police because I owe 3 months rent, and officers are threatening to arrest and lock me up.",
            "target_keywords": ["civil wrong", "breach of contract", "Section 32", "debt"]
        },
        {
            "scenario": "Case Study 2: Arrest in Lieu / Substitute Arrest",
            "query": "The police came looking for my brother. When they didn't find him, they arrested our mother instead to force him to show up.",
            "target_keywords": ["place of a suspect", "Section 36", "proxy", "lieu"]
        },
        {
            "scenario": "Case Study 3: Maximum Detention Period Before Court/Bail",
            "query": "How long can police officers hold a suspect in custody before bringing them to court or granting bail?",
            "target_keywords": ["twenty-four hours", "Section 35", "Section 62", "detention", "reasonable time"]
        },
        {
            "scenario": "Case Study 4: Profiling & Stop-and-Search on Physical Appearance",
            "query": "Can police officers stop and search my car, phone, and bag just because of my dreadlocks, tattoos, and casual dressing?",
            "target_keywords": ["personal attributes", "Section 54", "search", "hairstyle", "dressing"]
        }
    ]

    print("\n" + "#" * 70)
    print("RUNNING BATCH LEGAL RETRIEVAL TEST ON 4 PRACTICAL CASE STUDIES")
    print("#" * 70)

    for i, test in enumerate(test_scenarios, 1):
        print(f"\n[{test['scenario']}]")
        print(f"User Query: \"{test['query']}\"")
        print("-" * 70)

        results = collection.query(
            query_texts=[test["query"]],
            n_results=2
        )

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)

        for rank, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
            statute_title = meta["statute_title"]
            sec_num = meta["section_number"]
            sec_title = meta["section_title"]
            preview = doc.replace("\n", " ")[:200]

            print(f"  Top Match #{rank} (Distance: {dist:.4f}):")
            print(f"  Statute:  {statute_title} | Section {sec_num}: {sec_title}")
            print(f"  Snippet:  {preview}...")
            print()

        print("=" * 70)

if __name__ == "__main__":
    run_case_studies()
