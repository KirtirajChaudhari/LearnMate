"""End-to-end LearnMate pipeline (single-question path used by the app; batch stages live in eval/run.py).

Systems
  B1 : dense top-5 -> LLM (prompt abstention only)
  B2 : hybrid+CE top-5 -> LLM -> abstain if ce_top1 < tau_CE
  G  : B2 retrieval + answers -> gate + verifier features -> fused P(safe) -> typed policy
"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .citations import parse_answer, validate_resolvable
from .config import load_config, repo_path
from .fuse import FusionModel
from .gate.model import GateScorer, aggregate
from .generate import GenerationCache, generate_cached, generator_from_cfg
from .io_utils import read_json
from .policy import Decision, decide
from .provenance import ChunkStore
from .resources import retriever_for
from .retrieve import Retrieved, ce_features
from .verify import MiniCheckFT5, NLIModel, Verifier


def passage_dicts(retrieved: list[Retrieved], store: ChunkStore | None) -> list[dict]:
    out = []
    for r in retrieved:
        path = store.get(r.chunk_id).display_path if store is not None and r.chunk_id in store else r.extra.get("title", "")
        out.append({"chunk_id": r.chunk_id, "text": r.text, "section_path_str": path})
    return out


@dataclass
class Frozen:
    """Frozen calibration artifacts (written only by eval/calibrate.py)."""
    fusion: FusionModel | None = None
    tau_b2: float | None = None
    kappa_c: float | None = None
    s_min: float = 0.5
    meta: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "Frozen":
        d = read_json(path)
        return cls(FusionModel.from_dict(d["fusion"]) if d.get("fusion") else None, d.get("tau_b2"),
                   d.get("kappa_c"), d.get("s_min", 0.5), d)


class LearnMate:
    """Lazy-loading single-question pipeline (Streamlit demo). Fail-closed on any exception."""

    def __init__(self, cfg: dict | None = None, corpus: str = "course", gate_dir: str | None = None,
                 frozen_path: str | None = None, backend: str | None = None):
        self.cfg = cfg or load_config()
        self.corpus = corpus
        self.store = ChunkStore.load(repo_path(self.cfg["paths"]["processed"]) / "chunks.jsonl") if corpus == "course" else None
        self.retriever = retriever_for(corpus, self.cfg)
        self.generator = generator_from_cfg(self.cfg, backend=backend)
        self.cache = GenerationCache(repo_path(self.cfg["paths"]["cache"]) / f"generations_{corpus}.jsonl")
        self.gate = GateScorer(gate_dir) if gate_dir and Path(gate_dir).exists() else None
        m = self.cfg["models"]
        v = self.cfg["verification"]
        self.verifier = Verifier(MiniCheckFT5(m["minicheck"]["id"], m["minicheck"]["revision"]),
                                 NLIModel(m["nli"]["id"], m["nli"]["revision"]), v["support_threshold"],
                                 v["contradiction_pairs_top"])
        self.frozen = Frozen.load(frozen_path) if frozen_path and Path(frozen_path).exists() else Frozen()

    def answer(self, question: str, system: str = "G") -> dict:
        t0 = time.perf_counter()
        timings: dict[str, float] = {}
        try:
            if system == "B1":
                top = self.retriever.dense(question)
            else:
                top, _ = self.retriever.hybrid(question)
            timings["retrieve"] = time.perf_counter() - t0
            passages = passage_dicts(top, self.store)
            t = time.perf_counter()
            gen = generate_cached(self.generator, self.cache, question, passages, self.cfg["generation"]["max_new_tokens"])
            timings["generate"] = time.perf_counter() - t
            ids = [p["chunk_id"] for p in passages]
            insufficient, sents = parse_answer(gen["text"], ids)
            if self.store is not None:
                sents = validate_resolvable(sents, self.store.__contains__)
            feats = ce_features(top)
            decision: Decision
            if system == "B1":
                decision = decide(llm_insufficient=insufficient, sentences=[s.to_dict() for s in sents],
                                  p_safe=None, tau=None, ranked_ids=ids, score_only=True)
            elif system == "B2":
                decision = decide(llm_insufficient=insufficient, sentences=[s.to_dict() for s in sents],
                                  p_safe=feats["ce_top1"], tau=self.frozen.tau_b2, ranked_ids=ids, score_only=True)
            else:
                t = time.perf_counter()
                if self.gate is None:
                    raise RuntimeError("gate model not available (train it: python -m learnmate.gate.train)")
                g = self.gate.score([question] * len(top), [r.text for r in top])
                feats.update(aggregate(g))
                for r, p in zip(top, g):
                    r.extra["gate_prob"] = float(p)
                timings["gate"] = time.perf_counter() - t
                t = time.perf_counter()
                feats.update(self.verifier.verify(sents, {p["chunk_id"]: p["text"] for p in passages}, ids))
                timings["verify"] = time.perf_counter() - t
                fm = self.frozen.fusion
                if fm is None:
                    raise RuntimeError("no frozen fusion model (run eval/calibrate.py)")
                p_safe = float(fm.predict_proba(np.array([[feats[f] for f in fm.features]]))[0])
                decision = decide(llm_insufficient=insufficient, sentences=[s.to_dict() for s in sents],
                                  p_safe=p_safe, tau=fm.tau, pp_contra=feats["pp_contra"],
                                  kappa_c=self.frozen.kappa_c, s_min=self.frozen.s_min, ranked_ids=ids)
            timings["total"] = time.perf_counter() - t0
            return {"question": question, "system": system, "passages": passages,
                    "retrieved": [r.to_dict() for r in top], "raw_answer": gen["text"],
                    "sentences": [s.to_dict() for s in sents], "features": feats,
                    "decision": decision.to_dict(), "timings": timings, "model": gen["model"]}
        except Exception as e:  # fail-closed (ADR-012)
            d = decide(llm_insufficient=True, sentences=[], p_safe=None, tau=None, error=repr(e))
            return {"question": question, "system": system, "passages": [], "retrieved": [], "raw_answer": "",
                    "sentences": [], "features": {}, "decision": d.to_dict(),
                    "timings": {"total": time.perf_counter() - t0}, "traceback": traceback.format_exc()}
