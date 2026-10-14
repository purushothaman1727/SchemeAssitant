"""Embedding backends.

`fastembed` runs the multilingual MiniLM sentence-transformers model through ONNX
Runtime (no PyTorch), which keeps the install small. `HashingEmbedder` is a
dependency-free lexical fallback used for offline runs and unit tests.
"""
import hashlib
import math
import re
from typing import Protocol

_TOKEN = re.compile(r"\w+", re.UNICODE)


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Signed feature-hashing bag-of-words. Deterministic; no model download."""

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.name = f"hashing-{dim}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            vec = [0.0] * self.dim
            for tok in _TOKEN.findall(text.lower()):
                h = int.from_bytes(hashlib.blake2b(tok.encode(), digest_size=8).digest(), "big")
                vec[h % self.dim] += 1.0 if (h >> 63) & 1 else -1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            out.append([v / norm for v in vec])
        return out


class FastEmbedEmbedder:
    def __init__(self, model_name: str, cache_dir: str | None = None):
        from fastembed import TextEmbedding  # imported lazily: heavy

        self.name = model_name
        self._model = TextEmbedding(model_name, cache_dir=cache_dir)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._model.embed(texts)]


def build_embedder(backend: str, model_name: str, cache_dir: str | None = None) -> Embedder:
    if backend == "hashing":
        return HashingEmbedder()
    return FastEmbedEmbedder(model_name, cache_dir)
