import re
from dataclasses import dataclass

from app.rag.embeddings import Embedder
from app.rag.store import VectorStore

_WORD = re.compile(r"\w+", re.UNICODE)
_STOP = {"the", "a", "an", "of", "for", "to", "and", "in", "is", "are", "what", "how", "do",
         "i", "my", "me", "can", "this", "that", "it", "on", "with", "be", "or", "as", "by"}


@dataclass
class Evidence:
    text: str
    scheme_id: str
    source_url: str
    title: str
    page: int | None
    verified_date: str
    version: int
    score: float
    is_context: bool = False  # adjacent chunk added for continuity, not a direct match
    scheme_ids: list[str] | None = None  # every scheme this same passage was filed under


# Official documents say "ceiling", users say "limit". Small domain synonym map used to
# widen both the lexical match and the embedded query.
_SYNONYMS = {
    "limit": ["ceiling", "maximum", "exceed"],
    "income": ["income", "annual"],
    "documents": ["certificate", "documents"],
    "document": ["certificate", "documents"],
    "apply": ["application", "portal"],
    "eligible": ["eligibility", "eligible", "conditions"],
    "eligibility": ["conditions", "eligible"],
    "amount": ["rs", "rupees", "per month", "per annum"],
    "money": ["rs", "rupees", "allowance"],
    "free": ["free", "concession"],
}


def expand_query(query: str) -> str:
    extra: list[str] = []
    for w in _WORD.findall(query.lower()):
        extra.extend(_SYNONYMS.get(w, []))
    return query if not extra else f"{query} {' '.join(dict.fromkeys(extra))}"


def _terms(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 1}


def _lexical(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0.0
    return len(query_terms & _terms(text)) / len(query_terms)


def build_where(scheme_ids: list[str] | None, state: str | None, jurisdiction: str | None) -> dict:
    clauses: list[dict] = [{"is_outdated": False}, {"suspicious": False}, {"boilerplate": False}]
    if scheme_ids:
        clauses.append({"scheme_id": {"$in": list(scheme_ids)}})
    if jurisdiction:
        clauses.append({"jurisdiction": jurisdiction})
    if state:
        clauses.append({"state": {"$in": ["ALL", state]}})
    return {"$and": clauses}


def retrieve(store: VectorStore, embedder: Embedder, query: str, *,
             scheme_ids: list[str] | None = None, state: str | None = None,
             jurisdiction: str | None = None, k: int = 5, min_score: float = 0.25,
             candidates: int = 30, expand_neighbors: int = 1) -> list[Evidence]:
    """Hybrid retrieval: vector similarity re-ranked with keyword overlap.

    Returns [] when nothing clears `min_score`, so callers can say "no evidence" instead
    of guessing.
    """
    if not query.strip():
        return []
    query = expand_query(query)
    qvec = embedder.embed([query])[0]
    hits = store.query(qvec, candidates, build_where(scheme_ids, state, jurisdiction))
    qt = _terms(query)
    scored: list[Evidence] = []
    hit_by_id = {}
    for h in hits:
        score = 0.7 * max(h.similarity, 0.0) + 0.3 * _lexical(qt, h.text)
        if score < min_score:
            continue
        scored.append(_evidence(h.text, h.metadata, score))
        hit_by_id[h.id] = h
    scored.sort(key=lambda e: e.score, reverse=True)
    scored = _dedupe(scored)
    top = scored[:k]
    if expand_neighbors <= 0 or not top:
        return top

    # Tables and numbered rules often split across chunks/pages; bring in the neighbours of
    # the best few hits (same document, so same scheme/state/version) as marked context.
    have = {(e.scheme_id, e.source_url, e.text) for e in top}
    best = {(e.scheme_id, e.text): e.score for e in top[:3]}
    wanted: dict[str, float] = {}
    for h in hit_by_id.values():
        base = best.get((h.metadata["scheme_id"], h.text))
        if base is None:
            continue
        doc, idx = h.metadata["document_id"], h.metadata["chunk_index"]
        for d in range(1, expand_neighbors + 1):
            for j in (idx - d, idx + d):
                if j >= 0:
                    wanted.setdefault(f"{doc}-{j}", base * 0.9)
    extra = []
    for n in store.get_many(list(wanted)):
        m = n.metadata
        if m.get("is_outdated") or m.get("suspicious") or m.get("boilerplate"):
            continue
        ev = _evidence(n.text, m, wanted[n.id])
        if (ev.scheme_id, ev.source_url, ev.text) not in have:
            ev.is_context = True
            extra.append(ev)
    extra.sort(key=lambda e: e.score, reverse=True)
    return top + _dedupe(extra)[:3]


def _dedupe(items: list[Evidence]) -> list[Evidence]:
    """One shared document is filed under several schemes; show each passage once."""
    seen: dict[tuple[str, str], Evidence] = {}
    for e in items:  # items arrive best-first
        key = (e.source_url, e.text)
        if key in seen:
            if e.scheme_id not in seen[key].scheme_ids:
                seen[key].scheme_ids.append(e.scheme_id)
        else:
            e.scheme_ids = [e.scheme_id]
            seen[key] = e
    return list(seen.values())


def _evidence(text: str, m: dict, score: float) -> Evidence:
    return Evidence(
        text=text, scheme_id=m["scheme_id"], source_url=m["source_url"], title=m["title"],
        page=m.get("page") or None, verified_date=m.get("verified_date", ""),
        version=m.get("version", 1), score=round(score, 4))
