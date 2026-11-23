"""Sparse (BM25) + dense (FAISS, bge) indices over a passage collection (spec C3).

Works for any collection of ``{"chunk_id", "text"}`` dicts (d2l chunks or SQuAD paragraphs), so the
same retrieval code serves the course corpus and SQuAD-RAG.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .io_utils import read_jsonl, sha256_text, write_json, write_jsonl

TOKEN_RE = re.compile(r"\\[a-zA-Z]+|[a-zA-Z]+(?:'[a-z]+)?|\d+(?:\.\d+)?")
STOP = frozenset(
    "a an the of to in on for and or is are was were be been by with as at from that this these those it its "
    "which we our you your can will would should could may might not no do does did has have had than then "
    "there their them they he she his her what when where who whom how why if so such into about over".split()
)


def bm25_tokenize(text: str) -> list[str]:
    return [t for t in (m.group(0).lower() for m in TOKEN_RE.finditer(text)) if t not in STOP]


@dataclass
class Passage:
    chunk_id: str
    text: str          # text shown to models / users
    index_text: str    # text that was indexed (may include a title line)


class Embedder:
    def __init__(self, model_id: str, revision: str | None = None, query_prefix: str = "", device: str | None = None,
                 batch_size: int = 32):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_id, revision=revision, device=device)
        self.query_prefix = query_prefix
        self.batch_size = batch_size
        self.model_id = model_id

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=len(texts) > 500).astype("float32")

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        return self.model.encode([self.query_prefix + t for t in texts], batch_size=self.batch_size,
                                 normalize_embeddings=True, convert_to_numpy=True).astype("float32")


class HybridIndex:
    """BM25Okapi + FAISS IndexFlatIP (exact cosine on L2-normalized vectors)."""

    def __init__(self, passages: list[Passage], bm25, faiss_index, vectors: np.ndarray):
        self.passages = passages
        self.ids = [p.chunk_id for p in passages]
        self.pos = {cid: i for i, cid in enumerate(self.ids)}
        self.bm25 = bm25
        self.faiss = faiss_index
        self.vectors = vectors

    @classmethod
    def build(cls, passages: list[Passage], embedder: Embedder) -> "HybridIndex":
        import faiss
        from rank_bm25 import BM25Okapi

        bm25 = BM25Okapi([bm25_tokenize(p.index_text) for p in passages])
        vecs = embedder.encode_passages([p.index_text for p in passages])
        idx = faiss.IndexFlatIP(vecs.shape[1])
        idx.add(vecs)
        return cls(passages, bm25, idx, vecs)

    def save(self, out_dir: str | Path, meta: dict | None = None) -> None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        np.save(out_dir / "vectors.npy", self.vectors)  # plain float32 array (no pickle)
        write_jsonl(out_dir / "passages.jsonl", (p.__dict__ for p in self.passages))
        write_json(out_dir / "index_meta.json", {
            **(meta or {}),
            "n": len(self.passages),
            "dim": int(self.vectors.shape[1]),
            "ids_sha256": sha256_text("\n".join(self.ids)),
            "vectors_checksum": float(np.round(self.vectors.astype("float64").sum(), 4)),
        })

    @classmethod
    def load(cls, out_dir: str | Path) -> "HybridIndex":
        import faiss
        out_dir = Path(out_dir)
        from rank_bm25 import BM25Okapi

        vecs = np.load(out_dir / "vectors.npy", allow_pickle=False)
        passages = [Passage(**r) for r in read_jsonl(out_dir / "passages.jsonl")]
        # BM25 is rebuilt deterministically from text (cheap; avoids pickle deserialization)
        bm25 = BM25Okapi([bm25_tokenize(p.index_text) for p in passages])
        idx = faiss.IndexFlatIP(vecs.shape[1])
        idx.add(vecs)
        return cls(passages, bm25, idx, vecs)

    # ---- search (exclusion-aware, for stress test S1) -------------------------------
    def search_bm25(self, query: str, k: int, exclude: set[str] | frozenset = frozenset()) -> list[tuple[str, float]]:
        scores = self.bm25.get_scores(bm25_tokenize(query))
        order = np.argsort(-scores, kind="stable")
        out = []
        for i in order:
            cid = self.ids[i]
            if cid in exclude:
                continue
            out.append((cid, float(scores[i])))
            if len(out) == k:
                break
        return out

    def search_dense(self, qvec: np.ndarray, k: int, exclude: set[str] | frozenset = frozenset()) -> list[tuple[str, float]]:
        kk = min(len(self.ids), k + len(exclude))
        D, I = self.faiss.search(qvec.reshape(1, -1), kk)
        out = []
        for d, i in zip(D[0], I[0]):
            if i < 0:
                continue
            cid = self.ids[i]
            if cid in exclude:
                continue
            out.append((cid, float(d)))
            if len(out) == k:
                break
        return out
