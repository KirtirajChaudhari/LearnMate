"""Hybrid retrieval with Reciprocal Rank Fusion and cross-encoder reranking (spec C4, C5)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .index import Embedder, HybridIndex


def rrf_fuse(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion (Cormack et al., 2009): score(d) = sum_r 1 / (k + rank_r(d)), rank from 1."""
    scores: dict[str, float] = {}
    first_seen: dict[str, int] = {}
    order = 0
    for ranking in rankings:
        for rank, cid in enumerate(ranking, start=1):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
            if cid not in first_seen:
                first_seen[cid] = order
                order += 1
    return sorted(scores.items(), key=lambda kv: (-kv[1], first_seen[kv[0]]))


@dataclass
class Retrieved:
    chunk_id: str
    text: str
    rrf_score: float = 0.0
    bm25_rank: int | None = None
    dense_rank: int | None = None
    dense_score: float | None = None
    ce_logit: float | None = None
    ce_prob: float | None = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class CrossEncoderReranker:
    def __init__(self, model_id: str, revision: str | None = None, device: str | None = None, max_length: int = 512):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_id, revision=revision, device=device, max_length=max_length)
        self.model_id = model_id

    def score(self, query: str, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros(0, dtype="float32")
        import torch
        # raw logits (activation = identity) so that ce_prob = sigmoid(logit) is explicit
        logits = self.model.predict([(query, t) for t in texts], activation_fn=torch.nn.Identity(),
                                    convert_to_numpy=True, show_progress_bar=False)
        return np.asarray(logits, dtype="float32").reshape(-1)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


class Retriever:
    """Dense-only (B1) or hybrid+rerank (B0/B2/G) retrieval over one HybridIndex."""

    def __init__(self, index: HybridIndex, embedder: Embedder, reranker: CrossEncoderReranker | None,
                 bm25_k: int = 20, dense_k: int = 20, rrf_k: int = 60, top: int = 5):
        self.index, self.embedder, self.reranker = index, embedder, reranker
        self.bm25_k, self.dense_k, self.rrf_k, self.top = bm25_k, dense_k, rrf_k, top

    def _passage(self, cid: str):
        return self.index.passages[self.index.pos[cid]]

    def dense(self, query: str, k: int | None = None, exclude=frozenset()) -> list[Retrieved]:
        q = self.embedder.encode_queries([query])[0]
        hits = self.index.search_dense(q, k or self.top, set(exclude))
        return [Retrieved(cid, self._passage(cid).text, dense_rank=r, dense_score=s)
                for r, (cid, s) in enumerate(hits, start=1)]

    def candidates(self, query: str, exclude=frozenset()) -> list[Retrieved]:
        exclude = set(exclude)
        bm = self.index.search_bm25(query, self.bm25_k, exclude)
        q = self.embedder.encode_queries([query])[0]
        dn = self.index.search_dense(q, self.dense_k, exclude)
        bm_rank = {cid: r for r, (cid, _) in enumerate(bm, start=1)}
        dn_rank = {cid: r for r, (cid, _) in enumerate(dn, start=1)}
        dn_score = dict(dn)
        fused = rrf_fuse([[c for c, _ in bm], [c for c, _ in dn]], k=self.rrf_k)
        return [Retrieved(cid, self._passage(cid).text, rrf_score=s, bm25_rank=bm_rank.get(cid),
                          dense_rank=dn_rank.get(cid), dense_score=dn_score.get(cid)) for cid, s in fused]

    def hybrid(self, query: str, exclude=frozenset(), rerank: bool = True) -> tuple[list[Retrieved], list[Retrieved]]:
        """Return (top-k reranked passages, all fused candidates)."""
        cands = self.candidates(query, exclude)
        if not rerank or self.reranker is None:
            return cands[: self.top], cands
        idx_texts = [self.index.passages[self.index.pos[c.chunk_id]].index_text for c in cands]
        logits = self.reranker.score(query, idx_texts)
        probs = _sigmoid(logits)
        for c, lg, pr in zip(cands, logits, probs):
            c.ce_logit, c.ce_prob = float(lg), float(pr)
        ranked = sorted(cands, key=lambda c: (-c.ce_logit, -c.rrf_score))
        return ranked[: self.top], cands


def ce_features(top: list[Retrieved]) -> dict[str, float]:
    """B2 decision score and fusion features: top-1 CE probability and top1-top2 logit margin."""
    if not top or top[0].ce_logit is None:
        return {"ce_top1": 0.0, "ce_margin": 0.0}
    l1 = top[0].ce_logit
    l2 = top[1].ce_logit if len(top) > 1 and top[1].ce_logit is not None else l1 - 10.0
    return {"ce_top1": float(top[0].ce_prob), "ce_margin": float(l1 - l2)}
