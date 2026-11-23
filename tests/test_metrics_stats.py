import numpy as np

from eval.metrics import aurc, ece, operating_point, risk_coverage_curve, utility_at
from eval.stats import clopper_pearson, holm, mcnemar_exact, paired_bootstrap


def test_aurc_hand_computed():
    # ranked by score: errors [0, 1, 0] -> risks 0, 1/2, 1/3 -> mean = 5/18
    assert abs(aurc([0.9, 0.5, 0.1], [0, 1, 0]) - (0 + 0.5 + 1 / 3) / 3) < 1e-12
    assert aurc([0.9, 0.5], [0, 0]) == 0.0
    # perfect ranking beats reversed ranking
    assert aurc([3, 2, 1], [0, 0, 1]) < aurc([1, 2, 3], [0, 0, 1])


def test_abstained_items_ranked_last():
    cov, risk = risk_coverage_curve([0.9, -np.inf, 0.5], [0, 1, 0])
    assert list(risk) == [0.0, 0.0, 1 / 3]


def test_operating_point_and_utility():
    op = operating_point([1, 1, 0, 0], [0, 1, 1, 0], gold_insufficient=[0, 1, 1, 0], answerable_correct=[1, 0, 0, 1])
    assert op["coverage"] == 0.5 and op["selective_risk"] == 0.5 and op["hwsa"] == 0.5 and op["fac"] == 0.5
    assert utility_at([1, 1, 0], [0, 1, 0], lam=2) == (1 - 2) / 3


def test_ece_perfect():
    assert ece([1.0, 0.0], [1, 0]) == 0.0


def test_bootstrap_deterministic_and_mcnemar():
    x = np.array([1, 0, 1, 1, 0, 1, 0, 1.0])
    r1 = paired_bootstrap(lambda idx: x[idx].mean(), len(x), 500, seed=1)
    r2 = paired_bootstrap(lambda idx: x[idx].mean(), len(x), 500, seed=1)
    assert r1 == r2 and r1["ci_low"] <= r1["point"] <= r1["ci_high"]
    m = mcnemar_exact([1, 1, 1, 0], [0, 0, 1, 0])
    assert m["a_only"] == 2 and m["b_only"] == 0 and abs(m["p_value"] - 0.5) < 1e-12


def test_holm_and_cp():
    h = holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert h["a"]["p_holm"] == 0.03 and h["c"]["p_holm"] == 0.06 and h["b"]["p_holm"] == 0.06
    lo, hi = clopper_pearson(0, 30)
    assert lo == 0.0 and 0.1 < hi < 0.13
