"""Fusion, calibration and threshold selection (spec C10, ADR-007/008).

* Fusion: L2 logistic regression over <= 9 features, fitted on SQuAD-cal-RAG (target = item is "safe",
  i.e. the answer is correct-and-supported, or 0 if the system should not answer).
* Calibration: Platt scaling (2 parameters) of the fused logit on course-cal.
* Threshold: tau = argmax_tau U_lambda(tau) on course-cal, ties -> higher coverage. The *same* rule fits
  B2's CE threshold and B0's no-answer threshold.
No formal risk guarantee is claimed (experimental_protocol.md §7).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

FEATURES = ["gate_max", "gate_top2", "ce_top1", "ce_margin", "sup_min", "sup_mean", "pp_contra", "sp_contra",
            "uncited_frac"]


def feature_matrix(rows: list[dict], features: list[str]) -> np.ndarray:
    return np.array([[float(r["features"].get(f, 0.0)) for f in features] for r in rows], dtype="float64")


def utility(correct_answered: int, error_answered: int, n: int, lam: float) -> float:
    return (correct_answered - lam * error_answered) / n if n else 0.0


def choose_threshold(scores: np.ndarray, answered_ok: np.ndarray, can_answer: np.ndarray, lam: float) -> dict:
    """Pick tau maximizing U_lambda on calibration data.

    scores      : decision score per item (higher = more confident it is safe to answer)
    answered_ok : 1 if the system's answer for this item is correct-and-supported (0 = error if answered)
    can_answer  : 0 for items the system abstains on regardless of score (e.g. INSUFFICIENT_EVIDENCE output)
    Answer iff can_answer and score >= tau. Candidate taus: all unique scores + (+inf = abstain all).
    """
    scores = np.asarray(scores, float)
    ok = np.asarray(answered_ok, int)
    can = np.asarray(can_answer, bool)
    n = len(scores)
    cands = np.unique(np.concatenate([scores, [np.inf]]))
    best = None
    for tau in cands:
        ans = can & (scores >= tau)
        c = int((ans & (ok == 1)).sum())
        e = int((ans & (ok == 0)).sum())
        u = utility(c, e, n, lam)
        cov = ans.mean() if n else 0.0
        key = (round(u, 12), cov)
        if best is None or key > best[0]:
            best = (key, {"tau": float(tau), "utility": u, "coverage": float(cov), "correct": c, "errors": e})
    return best[1]


@dataclass
class FusionModel:
    features: list[str] = field(default_factory=lambda: list(FEATURES))
    C: float = 1.0
    coef_: np.ndarray | None = None
    intercept_: float = 0.0
    mu_: np.ndarray | None = None
    sd_: np.ndarray | None = None
    platt_a: float = 1.0
    platt_b: float = 0.0
    tau: float | None = None

    # ---- fit -----------------------------------------------------------------------
    def fit(self, X: np.ndarray, y: np.ndarray, cv_Cs=(0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0), seed: int = 13):
        from sklearn.linear_model import LogisticRegression, LogisticRegressionCV

        self.mu_ = X.mean(0)
        self.sd_ = X.std(0) + 1e-8
        Z = (X - self.mu_) / self.sd_
        if len(np.unique(y)) < 2:
            raise ValueError("fusion fit needs both classes")
        n_min = int(min(np.bincount(y.astype(int))))
        if n_min >= 5:
            cv = LogisticRegressionCV(Cs=list(cv_Cs), cv=min(5, n_min), scoring="neg_log_loss",  # L2 (default)
                                      max_iter=2000, random_state=seed).fit(Z, y)
            self.C = float(cv.C_[0])
        lr = LogisticRegression(C=self.C, max_iter=2000).fit(Z, y)
        self.coef_ = lr.coef_[0]
        self.intercept_ = float(lr.intercept_[0])
        return self

    def logit(self, X: np.ndarray) -> np.ndarray:
        Z = (X - self.mu_) / self.sd_
        return Z @ self.coef_ + self.intercept_

    def fit_platt(self, X: np.ndarray, y: np.ndarray):
        """Recalibrate the fused logit on (small) in-domain data: p = sigmoid(a * logit + b)."""
        from sklearn.linear_model import LogisticRegression

        z = self.logit(X).reshape(-1, 1)
        if len(np.unique(y)) < 2:
            return self
        lr = LogisticRegression(C=1e6, max_iter=2000).fit(z, y)  # ~unregularized 2-parameter Platt
        self.platt_a, self.platt_b = float(lr.coef_[0][0]), float(lr.intercept_[0])
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-(self.platt_a * self.logit(X) + self.platt_b)))

    # ---- persistence -------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {"features": self.features, "C": self.C, "coef": self.coef_.tolist(), "intercept": self.intercept_,
                "mu": self.mu_.tolist(), "sd": self.sd_.tolist(), "platt_a": self.platt_a, "platt_b": self.platt_b,
                "tau": self.tau}

    @classmethod
    def from_dict(cls, d: dict) -> "FusionModel":
        m = cls(features=d["features"], C=d["C"])
        m.coef_, m.intercept_ = np.array(d["coef"]), d["intercept"]
        m.mu_, m.sd_ = np.array(d["mu"]), np.array(d["sd"])
        m.platt_a, m.platt_b, m.tau = d["platt_a"], d["platt_b"], d["tau"]
        return m


def uncalibrated_mean_score(X: np.ndarray, lo: np.ndarray, hi: np.ndarray, invert: list[bool]) -> np.ndarray:
    """Ablation A3: min-max-normalized feature mean (features where higher = riskier are inverted)."""
    Z = (X - lo) / np.where(hi - lo > 0, hi - lo, 1.0)
    Z = np.clip(Z, 0, 1)
    Z[:, invert] = 1.0 - Z[:, invert]
    return Z.mean(1)


RISKY_FEATURES = {"pp_contra", "sp_contra", "uncited_frac"}
