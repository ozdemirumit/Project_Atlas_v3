import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeSource(Base):
    """A governed internal knowledge source (ATLAS-015 / ATLAS-027).

    MVP-002 requires "one governed vendor or internal knowledge source and
    local embeddings." This is intentionally a simplified slice of the full
    ATLAS-053 through ATLAS-058 governed knowledge pipeline (materialization,
    review, chunking, embedding generation, index staging/publication) — one
    directly-ingested source, not yet gated by the human-review workflow
    those ADRs define.
    """

    __tablename__ = "knowledge_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    """One embedded, retrievable passage of a knowledge source.

    `embedding` uses a deterministic local hashing-trick vectorizer
    (`app.knowledge.embeddings`), not a real language model — MVP-002 has no
    local/private embedding model configured yet (open in
    `docs/002_Product_Requirements.md` Section 16 / `docs/014_AI_Architecture.md`).
    It exists to prove the ingest → chunk → embed → retrieve pipeline shape;
    swapping in a real embedding model later only requires replacing
    `app.knowledge.embeddings.embed`, not this schema or the retrieval query.
    """

    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    source: Mapped[KnowledgeSource] = relationship(back_populates="chunks")
