import json
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

def index_statutes():
    # 1. Initialize persistent ChromaDB client
    db_path = "data/vector_db"
    client = chromadb.PersistentClient(path=db_path)
    
    # Use standard default sentence-transformer embedding model
    embed_fn = embedding_functions.DefaultEmbeddingFunction()
    
    collection = client.get_or_create_collection(
        name="nigerian_statutes",
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}
    )
    
    statute_files = [
        Path("data/json_laws/cfrn_1999.json"),
        Path("data/json_laws/police_act_2020.json")
    ]
    
    documents = []
    metadatas = []
    ids = []
    
    for fpath in statute_files:
        if not fpath.exists():
            print(f"Skipping {fpath.name} (not found)")
            continue
            
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        statute_id = data["statute_id"]
        short_title = data["short_title"]
        year = data.get("year", 0)
        
        for sec in data["sections"]:
            sec_num = sec["section_number"]
            doc_id = f"{statute_id}_sec_{sec_num}"
            chunk_text = sec["searchable_chunk"]
            
            documents.append(chunk_text)
            metadatas.append({
                "statute_id": statute_id,
                "statute_title": short_title,
                "section_number": sec_num,
                "section_title": sec["section_title"],
                "year": year
            })
            ids.append(doc_id)
            
    print(f"Total sections loaded for indexing: {len(documents)}")
    
    # Chroma allows batch upserts
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        collection.upsert(
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
        print(f" Indexed {end_idx}/{len(documents)} items...")
        
    print(f"\nVector Database successfully built at '{db_path}' with {collection.count()} vectors.")

if __name__ == "__main__":
    index_statutes()
