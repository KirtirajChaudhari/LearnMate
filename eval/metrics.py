"""Selective-prediction, abstention and calibration metrics (experimental_protocol.md §5).

Conventions
  score      : decision confidence (higher = more confident the answer is safe). Items the system abstains on
               regardless of score (e.g. LLM output INSUFFICIENT_EVIDENCE) carry score = -inf.
  error      : 1 if the item's answer would be an error *if answered* (human verdict incorrect/unsupported, or
               any answer to a gold-insufficient item), else 0.
  answered   : boolean decision at the frozen operating point.
"""
from __future__ import annotations

import math

import numpy as np


def _order(scores: np.ndarray, tiebreak: np.ndarray | None) -> np.ndarray:
    s = np.asarray(scores, float)
    tb = np.zeros_like(s) if tiebreak is None else np.asarray(tiebreak, float)
    return np.lexsort((tb, -s))  # descending score, deterministic tie-break


def risk_coverage_curve(scores, errors, tiebreak=None) -> tuple[np.ndarray, np.ndarray]:
    """Coverage k/N and selective risk among the top-k most confident items, k = 1..N.

    Items with score -inf are never 'answered' by the system; the curve stops at the last finite score and
    the remaining coverage levels are filled with the risk at full achievable coverage (they cannot be
    reached; AURC treats them as answered-in-order-of-tiebreak, which matches 'abstain is last').
    """
    e = np.asarray(errors, float)[_order(scores, tiebreak)]
    k = np.arange(1, len(e) + 1)
    return k / len(e), np.cumsum(e) / k


def aurc(scores, errors, tiebreak=None) -> float:
    """Area under the risk-coverage curve (Geifman & El-Yaniv 2017): mean selective risk over k = 1..N."""
    if len(errors) == 0:
        return float("nan")
    _, risk = risk_coverage_curve(scores, errors, tiebreak)
    return float(risk.mean())


def operating_point(answered, errors, gold_insufficient=None, answerable_correct=None) -> dict:
    """Metrics at a fixed answer/abstain decision vector."""
    a = np.asarray(answered, bool)
    e = np.asarray(errors, int)
    n = len(a)
    out = {
        "n": n,
        "coverage": float(a.mean()) if n else float("nan"),
        "selective_risk": float(e[a].mean()) if a.any() else float("nan"),
        "n_answered": int(a.sum()),
        "n_errors_answered": int((a & (e == 1)).sum()),
    }
    if gold_insufficient is not None:
        gi = np.asarray(gold_insufficient, bool)
        out["hwsa"] = float(a[gi].mean()) if gi.any() else float("nan")       # unsupported-answer rate
        out["answerable_coverage"] = float(a[~gi].mean()) if (~gi).any() else float("nan")
        out["abstention_accuracy"] = float(((~a) == gi).mean()) if n else float("nan")
    if answerable_correct is not None:
        ac = np.asarray(answerable_correct, bool)  # answerable items whose answer was judged correct
        out["fac"] = float((~a[ac]).mean()) if ac.any() else float("nan")    # false-abstention cost
    return out


def utility_at(answered, errors, lam: float) -> float:
    a = np.asarray(answered, bool)
    e = np.asarray(errors, int)
    return float(((a & (e == 0)).sum() - lam * (a & (e == 1)).sum()) / len(a)) if len(a) else float("nan")


def risk_at_coverage(scores, errors, coverage: float, tiebreak=None) -> float:
    cov, risk = risk_coverage_curve(scores, errors, tiebreak)
    k = max(1, int(math.ceil(coverage * len(cov))))
    return float(risk[k - 1])


def ece(probs, outcomes, n_bins: int = 10) -> float:
    """Expected calibration error, equal-width bins; outcome = 1 if safe (correct-and-supported)."""
    p = np.asarray(probs, float)
    y = np.asarray(outcomes, float)
    bins = np.minimum((p * n_bins).astype(int), n_bins - 1)
    tot = 0.0
    for b in range(n_bins):
        m = bins == b
        if m.any():
            tot += m.sum() / len(p) * abs(p[m].mean() - y[m].mean())
    return float(tot)


def brier(probs, outcomes) -> float:
    p = np.asarray(probs, float)
    y = np.asarray(outcomes, float)
    return float(((p - y) ** 2).mean())


def reliability_table(probs, outcomes, n_bins: int = 10) -> list[dict]:
    p = np.asarray(probs, float)
    y = np.asarray(outcomes, float)
    bins = np.minimum((p * n_bins).astype(int), n_bins - 1)
    return [{"bin": b, "n": int((bins == b).sum()), "mean_p": float(p[bins == b].mean()) if (bins == b).any() else None,
             "frac_safe": float(y[bins == b].mean()) if (bins == b).any() else None} for b in range(n_bins)]


def citation_precision_recall(sentence_labels: list[dict]) -> dict:
    """ALCE-style on human sentence labels: recall = supported sentences / sentences;
    precision = citations judged to support their sentence / all citations."""
    if not sentence_labels:
        return {"citation_recall": float("nan"), "citation_precision": float("nan"), "unsupported_claim_rate": float("nan")}
    rec = np.mean([s["label"] == "supported" and s.get("citation_ok", False) for s in sentence_labels])
    cits = [c for s in sentence_labels for c in s.get("citation_judgments", [s.get("citation_ok", False)])]
    prec = float(np.mean(cits)) if cits else float("nan")
    unsup = np.mean([s["label"] != "supported" for s in sentence_labels])
    return {"citation_recall": float(rec), "citation_precision": prec, "unsupported_claim_rate": float(unsup)}
