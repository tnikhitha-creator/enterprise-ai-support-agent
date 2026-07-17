from __future__ import annotations

import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "data" / "knowledge_base"


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip().lower())
    cleaned = cleaned.strip("_")

    if not cleaned:
        raise ValueError("Document name must contain valid characters.")

    return f"{cleaned}.txt"


def list_knowledge_documents() -> list[dict[str, Any]]:
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

    documents: list[dict[str, Any]] = []

    for file_path in sorted(KNOWLEDGE_BASE_DIR.glob("*.txt")):
        content = file_path.read_text(encoding="utf-8").strip()

        documents.append(
            {
                "filename": file_path.name,
                "title": file_path.stem.replace("_", " ").title(),
                "content": content,
                "character_count": len(content),
            }
        )

    return documents


def get_knowledge_document(filename: str) -> dict[str, Any] | None:
    safe_name = Path(filename).name

    if not safe_name.endswith(".txt"):
        safe_name = f"{safe_name}.txt"

    file_path = KNOWLEDGE_BASE_DIR / safe_name

    if not file_path.exists():
        return None

    content = file_path.read_text(encoding="utf-8").strip()

    return {
        "filename": file_path.name,
        "title": file_path.stem.replace("_", " ").title(),
        "content": content,
        "character_count": len(content),
    }


def create_knowledge_document(
    name: str,
    content: str,
) -> dict[str, Any]:
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

    filename = _safe_filename(name)
    file_path = KNOWLEDGE_BASE_DIR / filename

    if file_path.exists():
        raise FileExistsError(
            f"Knowledge document '{filename}' already exists."
        )

    cleaned_content = content.strip()

    if not cleaned_content:
        raise ValueError("Document content cannot be empty.")

    file_path.write_text(cleaned_content, encoding="utf-8")

    return get_knowledge_document(filename) or {}


def update_knowledge_document(
    filename: str,
    content: str,
) -> dict[str, Any]:
    safe_name = Path(filename).name

    if not safe_name.endswith(".txt"):
        safe_name = f"{safe_name}.txt"

    file_path = KNOWLEDGE_BASE_DIR / safe_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Knowledge document '{safe_name}' was not found."
        )

    cleaned_content = content.strip()

    if not cleaned_content:
        raise ValueError("Document content cannot be empty.")

    file_path.write_text(cleaned_content, encoding="utf-8")

    return get_knowledge_document(safe_name) or {}


def delete_knowledge_document(filename: str) -> bool:
    safe_name = Path(filename).name

    if not safe_name.endswith(".txt"):
        safe_name = f"{safe_name}.txt"

    file_path = KNOWLEDGE_BASE_DIR / safe_name

    if not file_path.exists():
        return False

    file_path.unlink()
    return True
