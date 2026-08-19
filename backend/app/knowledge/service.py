from sqlalchemy.orm import Session

from app.knowledge.embeddings import cosine_similarity, embed
from app.models.knowledge import KnowledgeChunk, KnowledgeSource

_CHUNK_SIZE_CHARS = 800


def _chunk_text(text: str, size: int = _CHUNK_SIZE_CHARS) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > size:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)
    return chunks or [text]


def ingest_source(db: Session, *, key: str, title: str, owner: str, content: str) -> KnowledgeSource:
    source = KnowledgeSource(key=key, title=title, owner=owner)
    db.add(source)
    db.flush()

    for index, chunk_text in enumerate(_chunk_text(content)):
        db.add(
            KnowledgeChunk(
                source_id=source.id,
                chunk_index=index,
                content=chunk_text,
                embedding=embed(chunk_text),
            )
        )
    db.flush()
    return source


def search(db: Session, *, query: str, top_k: int = 5) -> list[tuple[KnowledgeChunk, float]]:
    query_vector = embed(query)
    chunks = db.query(KnowledgeChunk).all()
    scored = [(chunk, cosine_similarity(query_vector, chunk.embedding)) for chunk in chunks]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]
