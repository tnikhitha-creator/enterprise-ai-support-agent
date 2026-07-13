import os
import chromadb


DB_PATH = "chroma_db"
COLLECTION_NAME = "support_knowledge"


def load_documents():
    docs = []
    folder = "data/knowledge_base"

    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            path = os.path.join(folder, filename)
            with open(path, "r") as file:
                docs.append({
                    "id": filename,
                    "text": file.read(),
                    "source": filename
                })

    return docs


def build_knowledge_base():
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    docs = load_documents()

    for doc in docs:
        collection.upsert(
            ids=[doc["id"]],
            documents=[doc["text"]],
            metadatas=[{"source": doc["source"]}]
        )

    return {"status": "Knowledge base indexed", "documents": len(docs)}


def search_knowledge_base(query: str):
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    results = collection.query(
        query_texts=[query],
        n_results=1
    )

    if not results["documents"] or not results["documents"][0]:
        return {
            "answer_context": "No relevant knowledge base article found.",
            "source": None
        }

    return {
        "answer_context": results["documents"][0][0],
        "source": results["metadatas"][0][0]["source"]
    }
