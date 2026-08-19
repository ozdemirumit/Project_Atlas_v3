import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.schemas import CurrentSubject
from app.core.database import get_db
from app.knowledge.service import ingest_source, search
from app.models.knowledge import KnowledgeSource
from app.rbac.permissions import KNOWLEDGE_ADMIN, KNOWLEDGE_READ

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class IngestRequest(BaseModel):
    key: str
    title: str
    content: str
    model_config = {"extra": "forbid"}


class KnowledgeSourceResponse(BaseModel):
    id: uuid.UUID
    key: str
    title: str
    owner: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchResultItem(BaseModel):
    chunk_id: uuid.UUID
    source_key: str
    source_title: str
    content: str
    score: float


@router.post("/sources", response_model=KnowledgeSourceResponse, status_code=201)
def create_source(
    payload: IngestRequest,
    db: Session = Depends(get_db),
    current: CurrentSubject = Depends(require_permission(KNOWLEDGE_ADMIN)),
) -> KnowledgeSource:
    try:
        source = ingest_source(
            db, key=payload.key, title=payload.title, owner=current.subject_id, content=payload.content
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A knowledge source with this key already exists.") from exc
    return source


@router.get("/search", response_model=list[SearchResultItem])
def search_knowledge(
    q: str = Query(min_length=1),
    top_k: int = Query(default=5, le=20),
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(KNOWLEDGE_READ)),
) -> list[SearchResultItem]:
    results = search(db, query=q, top_k=top_k)
    return [
        SearchResultItem(
            chunk_id=chunk.id,
            source_key=chunk.source.key,
            source_title=chunk.source.title,
            content=chunk.content,
            score=score,
        )
        for chunk, score in results
    ]
