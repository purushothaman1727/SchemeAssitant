from dataclasses import dataclass
from typing import Any

import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

COLLECTION = "scheme_chunks"

# chromadb 0.5.x logs an error per call from its (disabled) telemetry client on newer posthog.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)


@dataclass
class StoredChunk:
    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any]


@dataclass
class RawHit:
    id: str
    text: str
    metadata: dict[str, Any]
    similarity: float  # cosine similarity in [-1, 1]


class VectorStore:
    def __init__(self, path: str):
        self._client = chromadb.PersistentClient(
            path=path, settings=ChromaSettings(anonymized_telemetry=False)
        )
        self._col = self._client.get_or_create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, chunks: list[StoredChunk]) -> None:
        if not chunks:
            return
        self._col.upsert(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=[c.embedding for c in chunks],
            metadatas=[c.metadata for c in chunks],
        )

    def delete_document(self, document_id: int) -> None:
        self._col.delete(where={"document_id": document_id})

    def count(self) -> int:
        return self._col.count()

    def get_many(self, ids: list[str]) -> list[RawHit]:
        if not ids:
            return []
        res = self._col.get(ids=ids)
        return [
            RawHit(id=i, text=t, metadata=m, similarity=0.0)
            for i, t, m in zip(res["ids"], res["documents"], res["metadatas"])
        ]

    def query(self, embedding: list[float], n: int, where: dict | None) -> list[RawHit]:
        total = self._col.count()
        if total == 0:
            return []
        res = self._col.query(
            query_embeddings=[embedding], n_results=min(n, total), where=where or None
        )
        hits = []
        for i, cid in enumerate(res["ids"][0]):
            hits.append(
                RawHit(
                    id=cid,
                    text=res["documents"][0][i],
                    metadata=res["metadatas"][0][i],
                    similarity=1.0 - float(res["distances"][0][i]),
                )
            )
        return hits
