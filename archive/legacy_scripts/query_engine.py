import sys
import chromadb
from chromadb.utils import embedding_functions

def query_legal_engine(prompt: str, top_k: int = 4):
    db_path = "data/vector_db"
    client = chromadb.PersistentClient(path=db_path)
    embed_fn = embedding_functions.DefaultEmbeddingFunction()
    
    collection = client.get_collection(
        name="nigerian_statutes",
        embedding_function=embed_fn
    )
    
    results = collection.query(
        query_texts=[prompt],
        n_results=top_k
    )
    
    print(f"\n" + "=" * 60)
    print(f"QUERY: \"{prompt}\"")
    print("=" * 60)
    
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0]*len(docs)
    
    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
        print(f"\n[Result #{rank}] — Relevance Distance: {dist:.4f}")
        print(f"Statute: {meta['statute_title']} (Section {meta['section_number']})")
        print(f"Title:   {meta['section_title']}")
        print(f"Content:\n{doc[:350]}...\n")
        print("-" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_str = " ".join(sys.argv[1:])
    else:
        query_str = "Can a police officer arrest someone for a civil wrong or breach of contract?"
    
    query_legal_engine(query_str)
