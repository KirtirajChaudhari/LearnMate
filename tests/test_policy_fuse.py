import numpy as np

from learnmate.fuse import FusionModel, choose_threshold
from learnmate.policy import STATES, decide

S_OK = {"text": "a", "citations": ["c1"], "support": 0.9}
S_BAD = {"text": "b", "citations": ["c2"], "support": 0.1}
S_UNC = {"text": "c", "citations": [], "support": 0.0}


def test_every_state_reachable():
    seen = {
        decide(llm_insufficient=False, sentences=[S_OK], p_safe=0.9, tau=0.5, error="boom").state,
        decide(llm_insufficient=False, sentences=[S_OK], p_safe=0.9, tau=0.5, pp_contra=0.95, kappa_c=0.9).state,
        decide(llm_insufficient=True, sentences=[], p_safe=0.9, tau=0.5).state,
        decide(llm_insufficient=False, sentences=[S_OK], p_safe=0.2, tau=0.5).state,
        decide(llm_insufficient=False, sentences=[S_OK, S_BAD], p_safe=0.9, tau=0.5).state,
        decide(llm_insufficient=False, sentences=[S_OK], p_safe=0.9, tau=0.5).state,
    }
    assert seen == set(STATES)


def test_partial_shows_only_supported():
    d = decide(llm_insufficient=False, sentences=[S_OK, S_BAD, S_UNC], p_safe=0.9, tau=0.5)
    assert d.state == "partial" and d.displayed_sentences == [S_OK]


def test_baseline_score_only_does_not_prune():
    d = decide(llm_insufficient=False, sentences=[S_OK, S_BAD], p_safe=0.7, tau=0.5, score_only=True)
    assert d.state == "sufficient" and len(d.displayed_sentences) == 2


def test_choose_threshold_utility():
    scores = np.array([0.9, 0.8, 0.7, 0.2])
    ok = np.array([1, 1, 0, 0])
    r = choose_threshold(scores, ok, [True] * 4, lam=2.0)
    assert r["tau"] == 0.8 and r["correct"] == 2 and r["errors"] == 0
    r_all = choose_threshold(scores, np.zeros(4), [True] * 4, lam=2.0)
    assert r_all["coverage"] == 0.0  # abstain-all is best when everything is wrong


def test_fusion_roundtrip_and_monotone():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(400, 3))
    y = (X[:, 0] + 0.2 * rng.normal(size=400) > 0).astype(int)
    fm = FusionModel(features=["a", "b", "c"]).fit(X, y)
    fm.fit_platt(X[:100], y[:100])
    fm.tau = 0.5
    fm2 = FusionModel.from_dict(fm.to_dict())
    assert np.allclose(fm.predict_proba(X), fm2.predict_proba(X))
    assert fm.coef_[0] > 0
