import json
import re
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

class NigerianLegalHybridRetriever:
    def __init__(self):
        # 1. Initialize Vector DB
        self.client = chromadb.PersistentClient(path="data/vector_db")
        self.embed_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_collection(
            name="nigerian_statutes",
            embedding_function=self.embed_fn
        )
        
        # 2. Build In-Memory BM25 Index for exact legal phrasing
        statute_files = [
            Path("data/json_laws/cfrn_1999.json"),
            Path("data/json_laws/police_act_2020.json")
        ]
        
        self.docs = []
        self.metas = []
        self.tokenized_corpus = []
        
        for fpath in statute_files:
            if not fpath.exists():
                continue
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for sec in data["sections"]:
                chunk = sec["searchable_chunk"]
                self.docs.append(chunk)
                self.metas.append({
                    "statute_title": data["short_title"],
                    "section_number": sec["section_number"],
                    "section_title": sec["section_title"],
                    "full_text": sec["full_text"]
                })
                tokens = re.findall(r'\w+', chunk.lower())
                self.tokenized_corpus.append(tokens)
                
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def search(self, query: str, top_k: int = 3, vector_weight: float = 0.5):
        # Dense Vector Search (Fetch top 10 candidates)
        vec_results = self.collection.query(
            query_texts=[query],
            n_results=15
        )
        
        vec_scores = {}
        for rank, (meta, dist) in enumerate(zip(vec_results["metadatas"][0], vec_results["distances"][0])):
            doc_key = f"{meta['statute_title']}_sec_{meta['section_number']}"
            # Convert cosine distance to similarity score
            vec_scores[doc_key] = 1.0 / (1.0 + dist)
            
        # BM25 Keyword Search
        query_tokens = re.findall(r'\w+', query.lower())
        bm25_scores_raw = self.bm25.get_scores(query_tokens)
        
        # Normalize BM25 scores
        max_bm25 = max(bm25_scores_raw) if len(bm25_scores_raw) > 0 and max(bm25_scores_raw) > 0 else 1.0
        
        combined = []
        for idx, meta in enumerate(self.metas):
            doc_key = f"{meta['statute_title']}_sec_{meta['section_number']}"
            v_score = vec_scores.get(doc_key, 0.0)
            b_score = bm25_scores_raw[idx] / max_bm25
            
            final_score = (vector_weight * v_score) + ((1.0 - vector_weight) * b_score)
            combined.append({
                "meta": meta,
                "score": final_score,
                "vector_score": v_score,
                "bm25_score": b_score,
                "text": self.docs[idx]
            })
            
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:top_k]

if __name__ == "__main__":
    retriever = NigerianLegalHybridRetriever()
    
    test_queries = [
        "My landlord called police over unpaid rent debt and breach of contract.",
        "Police arrested a mother in place of her brother who was suspected.",
        "How long can police detain a suspect before court or bail?",
        "Police stopped and searched me because of my dreadlocks, tattoos and dressing."
    ]
    
    for q in test_queries:
        print(f"\nQUERY: \"{q}\"")
        print("=" * 65)
        top_matches = retriever.search(q, top_k=2)
        for i, m in enumerate(top_matches, 1):
            meta = m["meta"]
            print(f"[{i}] {meta['statute_title']} | Section {meta['section_number']}: {meta['section_title']}")
            print(f"    Score: {m['score']:.3f} (Vector: {m['vector_score']:.3f}, BM25: {m['bm25_score']:.3f})")
            print(f"    Snippet: {meta['full_text'][:160]}...\n")
