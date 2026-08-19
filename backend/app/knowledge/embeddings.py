"""A deterministic, dependency-free placeholder embedding.

MVP-002 requires "local embeddings" but Project Atlas has not yet selected a
local/private embedding model (open question in
`docs/002_Product_Requirements.md` Section 16). Rather than block the
ingest → chunk → embed → retrieve pipeline on that decision, this uses the
hashing trick: each lowercased word token is hashed into one of
`DIMENSIONS` buckets, and the resulting bag-of-words vector is L2-normalized.
It is directionally meaningful (shared vocabulary between texts increases
cosine similarity) but has none of a real embedding model's semantic
generalization — synonyms or rephrasings will not match well. Swapping in a
real model later only requires replacing `embed()`; callers and the stored
vector shape (a plain list[float] of length DIMENSIONS) do not change.
"""
import math
import re
from hashlib import blake2b

DIMENSIONS = 256

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


def embed(text: str) -> list[float]:
    vector = [0.0] * DIMENSIONS
    for token in _tokenize(text):
        bucket = int(blake2b(token.encode("utf-8"), digest_size=4).hexdigest(), 16) % DIMENSIONS
        vector[bucket] += 1.0

    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0.0:
        return vector
    return [v / norm for v in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))
