from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb


PROJECT_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "data" / "knowledge_base"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "enterprise_knowledge"


def _load_documents() -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []

    for file_path in sorted(KNOWLEDGE_BASE_DIR.glob("*.txt")):
        content = file_path.read_text(encoding="utf-8").strip()

        if content:
            documents.append(
                {
                    "id": file_path.stem,
                    "content": content,
                    "source": file_path.name,
                }
            )

    return documents


def _build_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    documents = _load_documents()

    if not documents:
        return collection

    collection.add(
        ids=[document["id"] for document in documents],
        documents=[document["content"] for document in documents],
        metadatas=[
            {"source": document["source"]}
            for document in documents
        ],
    )

    return collection


collection = _build_collection()


def search_knowledge_base(
    query: str,
    top_k: int = 3,
) -> dict[str, Any]:
    if not query.strip():
        return {
            "answer_context": "No search query was provided.",
            "source": None,
            "sources": [],
            "confidence": 0,
        }

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return {
            "answer_context": "No relevant knowledge base article found.",
            "source": None,
            "sources": [],
            "confidence": 0,
        }

    best_document = documents[0]
    best_metadata = metadatas[0] if metadatas else {}
    best_distance = distances[0] if distances else 1.0

    confidence = max(
        0,
        min(100, round((1 - float(best_distance)) * 100)),
    )

    sources = [
        {
            "source": metadata.get("source"),
            "distance": round(float(distance), 4),
        }
        for metadata, distance in zip(metadatas, distances)
    ]

    return {
        "answer_context": best_document,
        "source": best_metadata.get("source"),
        "sources": sources,
        "confidence": confidence,
    }
