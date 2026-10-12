import json
import re
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

class ProductionLegalRetriever:
    def __init__(self):
        print("Initializing Production Legal Retriever...")
        self.client = chromadb.PersistentClient(path="data/vector_db")
        self.embed_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_collection(
            name="nigerian_statutes",
            embedding_function=self.embed_fn
        )
        
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        statute_files = [
            Path("data/json_laws/cfrn_1999.json"),
            Path("data/json_laws/police_act_2020.json")
        ]
        
        self.corpus = []
        tokenized_corpus = []
        
        for fpath in statute_files:
            if not fpath.exists():
                continue
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            statute_id = data["statute_id"]
            statute_title = data["short_title"]
            for sec in data["sections"]:
                doc_id = f"{statute_id}_sec_{sec['section_number']}"
                chunk = sec["searchable_chunk"]
                item = {
                    "doc_id": doc_id,
                    "statute_id": statute_id,
                    "statute_title": statute_title,
                    "section_number": sec["section_number"],
                    "section_title": sec["section_title"],
                    "full_text": sec["full_text"],
                    "searchable_chunk": chunk
                }
                self.corpus.append(item)
                # Tokenize title and chunk heavily
                tokens = re.findall(r'\w+', f"{statute_title} {sec['section_title']} {sec['full_text']}".lower())
                tokenized_corpus.append(tokens)
                
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"Loaded {len(self.corpus)} sections into Hybrid RRF Engine.")

    def _expand_intent(self, query: str) -> str:
        q = query.lower()
        terms = [query]
        if any(k in q for k in ["debt", "rent", "money", "owe", "landlord", "contract", "civil"]):
            terms.append("civil wrong breach of contract arrest recovery debt commercial")
        if any(k in q for k in ["instead", "in place of", "mother", "brother", "proxy", "lieu"]):
            terms.append("arrest in place of a suspect arrest in lieu proxy")
        if any(k in q for k in ["dreadlocks", "tattoo", "dressing", "appearance", "hair", "profile"]):
            terms.append("stop and search reasonable suspicion hairstyle personal attributes")
        if any(k in q for k in ["how long", "detain", "detention", "hours", "days", "bail", "custody"]):
            terms.append("release on bail 24 hours 48 hours court of competent jurisdiction")
        return " ".join(terms)

    def search(self, query: str, top_k: int = 2, candidate_pool: int = 50):
        search_query = self._expand_intent(query)
        
        # 1. Dense Vector Retrieval
        vec_res = self.collection.query(query_texts=[search_query], n_results=candidate_pool)
        vec_ids = vec_res["ids"][0]
        
        # 2. BM25 Sparse Retrieval
        tokens = re.findall(r'\w+', search_query.lower())
        bm25_scores = self.bm25.get_scores(tokens)
        bm25_top_idx = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:candidate_pool]
        
        # 3. Reciprocal Rank Fusion (RRF)
        rrf = {}
        k_const = 60
        for rank, doc_id in enumerate(vec_ids):
            rrf[doc_id] = rrf.get(doc_id, 0.0) + (1.0 / (k_const + rank + 1))
            
        for rank, idx in enumerate(bm25_top_idx):
            doc_id = self.corpus[idx]["doc_id"]
            rrf[doc_id] = rrf.get(doc_id, 0.0) + (1.0 / (k_const + rank + 1))
            
        # 4. Gather unique candidates
        candidate_ids = sorted(rrf.keys(), key=lambda x: rrf[x], reverse=True)[:candidate_pool]
        candidates = [item for item in self.corpus if item["doc_id"] in candidate_ids]
        
        # 5. Cross-Encoder Re-ranking on expanded context
        pairs = [[search_query, c["searchable_chunk"]] for c in candidates]
        scores = self.reranker.predict(pairs)
        
        for c, s in zip(candidates, scores):
            c["rerank_score"] = float(s)
            
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return candidates[:top_k]

if __name__ == "__main__":
    engine = ProductionLegalRetriever()
    
    test_queries = [
        "My landlord called police over unpaid rent debt and breach of contract.",
        "Police arrested a mother in place of her brother who was suspected.",
        "How long can police detain a suspect before court or bail?",
        "Police stopped and searched me because of my dreadlocks, tattoos and dressing."
    ]
    
    for q in test_queries:
        print(f"\nQUERY: \"{q}\"")
        print("=" * 68)
        top = engine.search(q, top_k=2)
        for i, m in enumerate(top, 1):
            print(f"[{i}] {m['statute_title']} | Section {m['section_number']}: {m['section_title']}")
            print(f"    Reranker Score: {m['rerank_score']:.4f}")
            print(f"    Snippet: {m['full_text'][:170]}...\n")
