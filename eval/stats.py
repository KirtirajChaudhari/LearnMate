"""Statistics for paired comparisons (experimental_protocol.md §6)."""
from __future__ import annotations

from typing import Callable

import numpy as np
from scipy import stats


def paired_bootstrap(metric: Callable[[np.ndarray], float], n_items: int, n_resamples: int = 10_000,
                     seed: int = 2026, alpha: float = 0.05) -> dict:
    """Bootstrap over items. ``metric(idx)`` returns the statistic (e.g. AURC(G)-AURC(B2)) on resampled indices."""
    rng = np.random.default_rng(seed)
    point = float(metric(np.arange(n_items)))
    boots = np.empty(n_resamples)
    for b in range(n_resamples):
        boots[b] = metric(rng.integers(0, n_items, n_items))
    lo, hi = np.nanpercentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    # two-sided bootstrap p-value for H0: delta = 0 (percentile method, reported descriptively)
    p = float(min(1.0, 2 * min((boots <= 0).mean(), (boots >= 0).mean())))
    return {"point": point, "ci_low": float(lo), "ci_high": float(hi), "p_boot": p, "n_resamples": n_resamples,
            "seed": seed}


def mcnemar_exact(a_correct, b_correct) -> dict:
    """Exact McNemar test on paired binary outcomes (two-sided binomial on discordant pairs)."""
    a = np.asarray(a_correct, bool)
    b = np.asarray(b_correct, bool)
    n01 = int((a & ~b).sum())   # a right, b wrong
    n10 = int((~a & b).sum())   # a wrong, b right
    n = n01 + n10
    p = float(stats.binomtest(n01, n, 0.5).pvalue) if n > 0 else 1.0
    return {"a_only": n01, "b_only": n10, "discordant": n, "p_value": p}


def holm(pvalues: dict[str, float], alpha: float = 0.05) -> dict[str, dict]:
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, max(running, (m - i) * p))
        running = adj
        out[k] = {"p": p, "p_holm": adj, "reject": adj < alpha}
    return out


def clopper_pearson(k: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    """Two-sided exact binomial CI (descriptive; no selective-risk guarantee is claimed)."""
    if n == 0:
        return (float("nan"), float("nan"))
    a = 1 - conf
    lo = 0.0 if k == 0 else float(stats.beta.ppf(a / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(1 - a / 2, k + 1, n - k))
    return lo, hi


def cohen_kappa(a: list, b: list) -> float:
    from sklearn.metrics import cohen_kappa_score
    return float(cohen_kappa_score(a, b))
