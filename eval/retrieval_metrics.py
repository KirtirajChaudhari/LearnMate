"""Retrieval metrics against gold passage IDs (protocol §5)."""
from __future__ import annotations

import math


def recall_at_k(ranked: list[str], gold: set[str], k: int, mode: str = "any") -> float:
    top = set(ranked[:k])
    if not gold:
        return float("nan")
    return float(bool(top & gold)) if mode == "any" else float(gold <= top)


def mrr(ranked: list[str], gold: set[str]) -> float:
    for i, c in enumerate(ranked, start=1):
        if c in gold:
            return 1.0 / i
    return 0.0


def ndcg_at_k(ranked: list[str], gold: set[str], k: int = 10) -> float:
    dcg = sum(1.0 / math.log2(i + 1) for i, c in enumerate(ranked[:k], start=1) if c in gold)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(gold), k) + 1))
    return dcg / ideal if ideal > 0 else float("nan")


def summarize(rows: list[dict], ks=(1, 5, 20)) -> dict:
    """rows: {"ranked": [...], "gold": [...]} for answerable items."""
    out = {}
    n = len(rows)
    for k in ks:
        out[f"recall@{k}"] = sum(recall_at_k(r["ranked"], set(r["gold"]), k) for r in rows) / n
    out["mrr"] = sum(mrr(r["ranked"], set(r["gold"])) for r in rows) / n
    out["ndcg@10"] = sum(ndcg_at_k(r["ranked"], set(r["gold"]), 10) for r in rows) / n
    out["n"] = n
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items()}
