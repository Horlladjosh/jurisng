import json
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

def build_complete_index():
    print("=" * 65)
    print("BUILDING MASTER NIGERIAN STATUTORY VECTOR DATABASE")
    print("=" * 65)

    client = chromadb.PersistentClient(path="data/vector_db")
    embed_fn = embedding_functions.DefaultEmbeddingFunction()

    # Reset collection to ingest master corpus cleanly
    try:
        client.delete_collection(name="nigerian_statutes")
        print("-> Cleaned prior collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name="nigerian_statutes",
        embedding_function=embed_fn,
        metadata={"description": "Master Nigerian Federal Enactments"}
    )

    json_dir = Path("data/json_laws")
    json_files = sorted(list(json_dir.glob("*.json")))

    total_chunks = 0
    
    for jfile in json_files:
        with open(jfile, "r", encoding="utf-8") as f:
            data = json.load(f)

        statute_id = data.get("statute_id", jfile.stem)
        statute_title = data.get("short_title", data.get("statute_title", statute_id))
        sections = data.get("sections", [])

        if not sections:
            continue

        ids = []
        documents = []
        metadatas = []

        for sec in sections:
            sec_num = str(sec["section_number"])
            doc_id = f"{statute_id}_sec_{sec_num}"
            chunk = sec["searchable_chunk"]

            ids.append(doc_id)
            documents.append(chunk)
            metadatas.append({
                "statute_id": statute_id,
                "statute_title": statute_title,
                "section_number": sec_num,
                "section_title": sec["section_title"]
            })

        # Batch insert into ChromaDB
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            collection.add(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )

        total_chunks += len(ids)
        print(f"  [✓] Indexed {len(ids):>4} sections from {statute_title}")

    print("\n" + "=" * 65)
    print(f"MASTER INDEX READY: {total_chunks:,} Sections Indexed Across All Statutes")
    print("=" * 65)

if __name__ == "__main__":
    build_complete_index()
