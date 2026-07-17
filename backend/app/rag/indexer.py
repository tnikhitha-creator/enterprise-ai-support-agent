from __future__ import annotations

from pathlib import Path

import chromadb


PROJECT_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "data" / "knowledge_base"
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"


def rebuild_knowledge_index() -> dict:
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    try:
        client.delete_collection("knowledge_base")
    except Exception:
        pass

    collection = client.create_collection("knowledge_base")

    indexed = 0

    for file in sorted(KNOWLEDGE_BASE_DIR.glob("*.txt")):
        text = file.read_text(encoding="utf-8").strip()

        collection.add(
            documents=[text],
            ids=[file.stem],
            metadatas=[
                {
                    "source": file.name
                }
            ],
        )

        indexed += 1

    return {
        "indexed_documents": indexed,
        "status": "completed",
    }