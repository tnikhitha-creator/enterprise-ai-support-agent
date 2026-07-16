from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.core.security import verify_admin_api_key
from backend.app.admin.audit import read_audit_events
from backend.app.admin.incidents import get_incident_history
from backend.app.admin.knowledge import (
    create_knowledge_document,
    delete_knowledge_document,
    get_knowledge_document,
    list_knowledge_documents,
    update_knowledge_document,
)
from backend.app.admin.metrics import build_admin_metrics
from backend.app.admin.security_events import get_security_events
from backend.app.rag.indexer import rebuild_knowledge_index
from backend.app.admin.knowledge_stats import build_knowledge_stats
from backend.app.admin.dashboard import build_admin_dashboard
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_admin_api_key)],
)


class KnowledgeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)


class KnowledgeUpdateRequest(BaseModel):
    content: str = Field(min_length=1)


@router.get("/metrics")
def get_admin_metrics():
    return build_admin_metrics()
@router.get("/dashboard")
def get_admin_dashboard():
    return build_admin_dashboard()

@router.get("/audit-events")
def get_audit_events(
    limit: int = Query(default=100, ge=1, le=500),
):
    return {
        "events": read_audit_events(limit=limit),
    }


@router.get("/security-events")
def get_admin_security_events(
    limit: int = Query(default=100, ge=1, le=500),
):
    return {
        "events": get_security_events(limit=limit),
    }


@router.get("/incidents")
def get_admin_incidents(
    limit: int = Query(default=100, ge=1, le=500),
):
    return {
        "incidents": get_incident_history(limit=limit),
    }


@router.get("/knowledge")
def get_knowledge_documents():
    return {
        "documents": list_knowledge_documents(),
    }
@router.get("/knowledge/stats")
def get_knowledge_stats():
    return build_knowledge_stats()

@router.get("/knowledge/{filename}")
def get_knowledge_document_by_filename(filename: str):
    document = get_knowledge_document(filename)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found.",
        )

    return document


@router.post("/knowledge", status_code=201)
def create_admin_knowledge_document(
    request: KnowledgeCreateRequest,
):
    try:
        return create_knowledge_document(
            name=request.name,
            content=request.content,
        )
    except FileExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.put("/knowledge/{filename}")
def update_admin_knowledge_document(
    filename: str,
    request: KnowledgeUpdateRequest,
):
    try:
        return update_knowledge_document(
            filename=filename,
            content=request.content,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.delete("/knowledge/{filename}")
def delete_admin_knowledge_document(filename: str):
    deleted = delete_knowledge_document(filename)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found.",
        )

    return {
        "deleted": True,
        "filename": filename,
    }
@router.post("/knowledge/reindex")
def reindex_knowledge_base():
    return rebuild_knowledge_index()