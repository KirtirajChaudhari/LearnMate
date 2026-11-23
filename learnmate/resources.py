"""Construct shared model/index resources from config (lazy, cached per process)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .chunking import index_text
from .config import load_config, repo_path
from .index import Embedder, HybridIndex, Passage
from .io_utils import read_jsonl
from .provenance import ChunkStore
from .retrieve import CrossEncoderReranker, Retriever


def device() -> str:
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def get_embedder(model_id: str, revision: str, prefix: str) -> Embedder:
    return Embedder(model_id, revision, prefix, device=device())


@lru_cache(maxsize=1)
def get_reranker(model_id: str, revision: str) -> CrossEncoderReranker:
    return CrossEncoderReranker(model_id, revision, device=device())


def embedder_from_cfg(cfg: dict) -> Embedder:
    m = cfg["models"]["embedder"]
    return get_embedder(m["id"], m["revision"], m["query_prefix"])


def reranker_from_cfg(cfg: dict) -> CrossEncoderReranker:
    m = cfg["models"]["reranker"]
    return get_reranker(m["id"], m["revision"])


def corpus_passages(name: str, cfg: dict) -> list[Passage]:
    """Passages for a named corpus: 'course' (d2l chunks) or 'squad-cal' / 'squad-test' / 'squad-dev*'."""
    proc = repo_path(cfg["paths"]["processed"])
    if name == "course":
        store = ChunkStore.load(proc / "chunks.jsonl")
        return [Passage(c.chunk_id, c.text, index_text(c)) for c in store]
    rows = read_jsonl(proc / "squad_rag" / f"{name}_corpus.jsonl")
    return [Passage(r["chunk_id"], r["text"], f"{r['title']}\n{r['text']}") for r in rows]


def index_dir(name: str, cfg: dict) -> Path:
    return repo_path(cfg["paths"]["processed"]) / "indices" / name


def build_or_load_index(name: str, cfg: dict, rebuild: bool = False) -> HybridIndex:
    d = index_dir(name, cfg)
    if d.exists() and not rebuild:
        return HybridIndex.load(d)
    idx = HybridIndex.build(corpus_passages(name, cfg), embedder_from_cfg(cfg))
    idx.save(d, meta={"corpus": name, "embedder": cfg["models"]["embedder"]})
    return idx


def retriever_for(name: str, cfg: dict | None = None, rerank: bool = True) -> Retriever:
    cfg = cfg or load_config()
    r = cfg["retrieval"]
    return Retriever(build_or_load_index(name, cfg), embedder_from_cfg(cfg),
                     reranker_from_cfg(cfg) if rerank else None,
                     r["bm25_k"], r["dense_k"], r["rrf_k"], r["rerank_top"])
