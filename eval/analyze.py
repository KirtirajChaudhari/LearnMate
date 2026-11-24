"""Registered analysis (experimental_protocol.md §3-§6). Reads records + judgments + frozen thresholds.

    python -m eval.analyze --run results/runs/course-test__clean --judgments data/annotations/judgments_test.jsonl
    python -m eval.analyze --run results/runs/squad-test__clean            # SQuAD: automatic labels

Systems: B1 (prompt-only point), B2 (CE threshold), G (fused), A1..A5 (ablations), all on the same items.
Primary: H1 = paired-bootstrap CI of AURC(G) - AURC(B2) < 0 AND answerable-coverage(G) >= coverage(B2) - m.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from learnmate.config import load_config, repo_path
from learnmate.fuse import FusionModel, feature_matrix, uncalibrated_mean_score
from learnmate.io_utils import read_json, read_jsonl, stable_id, write_json

from .labels import b0_error, error_label, load_judgments, s1_error_label
from .metrics import aurc, brier, ece, operating_point, reliability_table, risk_at_coverage, utility_at
from .stats import clopper_pearson, holm, mcnemar_exact, paired_bootstrap


def system_scores(recs: list[dict], frozen: dict) -> dict[str, dict]:
    """Return per-system {score, can, answered} arrays."""
    can = np.array([not r["hyb_llm_insufficient"] for r in recs])
    out = {}
    ce = np.array([r["features"]["ce_top1"] for r in recs])
    out["B2"] = {"score": np.where(can, ce, -np.inf), "can": can, "answered": can & (ce >= frozen["tau_b2"])}
    kc = frozen.get("kappa_c")
    for name, d in frozen["variants"].items():
        feats = d["features"]
        if name.startswith("A4") or name.startswith("A5"):
            key = "a4_gate" if name.startswith("A4") else "a5_gate"
            if any(r.get(key) is None for r in recs):
                continue
            rr = [{**r, "features": {**r["features"], **r[key]}} for r in recs]
        else:
            rr = recs
        X = feature_matrix(rr, feats)
        if name.startswith("A3"):
            p = uncalibrated_mean_score(X, np.array(d["lo"]), np.array(d["hi"]), d["invert"])
        else:
            p = FusionModel.from_dict(d).predict_proba(X)
        ans = can & (p >= d["tau"])
        if kc is not None and name == "G":
            ans &= np.array([r["features"].get("claim_conflict", 0.0) < kc for r in recs])
        out[name] = {"score": np.where(can, p, -np.inf), "can": can, "answered": ans, "prob": p}
    if frozen.get("tau_b0") is not None and all(r.get("b0_answer") and r.get("gold_answers") is not None for r in recs):
        mg = np.array([r["b0_answer"]["margin"] for r in recs])
        out["B0"] = {"score": mg, "can": np.ones(len(recs), bool), "answered": mg >= frozen["tau_b0"], "own_errors": True}
    b1_can = np.array([not r["b1_llm_insufficient"] for r in recs])
    out["B1"] = {"score": None, "can": b1_can, "answered": b1_can}
    return out


def analyze(run_dir: Path, judgments_path: str | None, frozen: dict, cfg: dict, condition: str) -> dict:
    if not (run_dir / "records.jsonl").exists():
        raise SystemExit(f"{run_dir}/records.jsonl not found: that run has not completed. Run: python scripts/where_am_i.py")
    recs = read_jsonl(run_dir / "records.jsonl")
    judg = load_judgments(judgments_path) if judgments_path and Path(judgments_path).exists() else None
    lab = s1_error_label if condition == "S1" else (lambda r, s, j: error_label(r, s, condition, j))
    keep = []
    for r in recs:
        eh, eb = lab(r, "hyb", judg), lab(r, "b1", judg)
        if eh is None or eb is None:
            continue
        r["err_hyb"], r["err_b1"] = eh, eb
        keep.append(r)
    recs = keep
    n = len(recs)
    if n == 0:
        raise SystemExit("no fully labelled records")
    gi = np.array([r["gold_state"] == "insufficient" for r in recs])
    err_h = np.array([r["err_hyb"] for r in recs])
    err_b1 = np.array([r["err_b1"] for r in recs])
    ans_correct = (~gi) & (err_h == 0)
    S = system_scores(recs, frozen)
    tiebreak = np.array([int(stable_id(r["item_id"], n=8), 16) for r in recs], float)  # deterministic
    m_pp = cfg["decision"]["coverage_margin_pp"] / 100.0
    res: dict = {"run": str(run_dir), "condition": condition, "n": n, "n_insufficient": int(gi.sum()), "systems": {}}
    for name, s in S.items():
        e = err_b1 if name == "B1" else (np.array([b0_error(r) for r in recs]) if name == "B0" else err_h)
        op = operating_point(s["answered"], e, gi, ans_correct if name != "B1" else (~gi) & (err_b1 == 0))
        k = op["n_errors_answered"]
        op["selective_risk_cp95"] = clopper_pearson(k, op["n_answered"])
        for lam in cfg["decision"]["report_lambdas"]:
            op[f"utility_l{lam:g}"] = utility_at(s["answered"], e, lam)
        if s["score"] is not None:
            op["aurc"] = aurc(s["score"], e, tiebreak)
            op["risk@cov0.5"] = risk_at_coverage(s["score"], e, 0.5, tiebreak)
            op["risk@cov0.7"] = risk_at_coverage(s["score"], e, 0.7, tiebreak)
        if "prob" in s:
            pa = s["can"]
            op["ece"] = ece(s["prob"][pa], 1 - e[pa]) if pa.any() else None
            op["brier"] = brier(s["prob"][pa], 1 - e[pa]) if pa.any() else None
            op["reliability"] = reliability_table(s["prob"][pa], 1 - e[pa]) if pa.any() else None
        res["systems"][name] = op
    # ---- primary H1 (G vs B2) -----------------------------------------------------------------
    if "G" in S:
        g, b2 = S["G"]["score"], S["B2"]["score"]
        boot = paired_bootstrap(lambda idx: aurc(g[idx], err_h[idx], tiebreak[idx]) - aurc(b2[idx], err_h[idx], tiebreak[idx]),
                                n, 10_000, cfg["project"]["bootstrap_seed"])
        cov_g = res["systems"]["G"]["answerable_coverage"]
        cov_b2 = res["systems"]["B2"]["answerable_coverage"]
        res["H1"] = {"delta_aurc_G_minus_B2": boot, "answerable_coverage_G": cov_g, "answerable_coverage_B2": cov_b2,
                     "margin": m_pp, "coverage_condition_met": bool(cov_g >= cov_b2 - m_pp),
                     "supported": bool(boot["ci_high"] < 0 and cov_g >= cov_b2 - m_pp)}
        # ablations vs G (descriptive)
        res["ablations_vs_G"] = {}
        for name in S:
            if name.startswith("A"):
                a = S[name]["score"]
                res["ablations_vs_G"][name] = paired_bootstrap(
                    lambda idx, a=a: aurc(a[idx], err_h[idx], tiebreak[idx]) - aurc(g[idx], err_h[idx], tiebreak[idx]),
                    n, 2_000, cfg["project"]["bootstrap_seed"])
        # secondary H1b: HwSA G vs B1 on insufficient items (paired McNemar on 'abstained')
        if gi.any():
            res["H1b_hwsa_G_vs_B1"] = mcnemar_exact(~S["G"]["answered"][gi], ~S["B1"]["answered"][gi])
            res["H_vs_B2_hwsa"] = mcnemar_exact(~S["G"]["answered"][gi], ~S["B2"]["answered"][gi])
    if condition != "clean":
        res.pop("H1", None)  # H1 is registered for the clean course-test condition only
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--judgments", default=None)
    ap.add_argument("--frozen", default=None)
    ap.add_argument("--condition", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cfg = load_config()
    run = Path(a.run)
    cond = a.condition or run.name.split("__")[-1].split("_")[0]
    if not (run / "records.jsonl").exists():
        raise SystemExit(f"{run}/records.jsonl not found: that run has not completed. Run: python scripts/where_am_i.py")
    frozen = read_json(a.frozen or repo_path(cfg["paths"]["frozen"]) / "thresholds.json")
    if frozen.get("SMOKE_ONLY") and "smoke" not in str(run):
        raise SystemExit("smoke thresholds cannot be used for a real run")
    res = analyze(run, a.judgments, frozen, cfg, cond)
    if "H1" in res and not run.name.startswith("course-test"):
        res["note"] = "H1 is defined on course-test only; this is a secondary/diagnostic analysis"
    out = Path(a.out) if a.out else run / "analysis.json"
    write_json(out, res)
    for k, v in res["systems"].items():
        print(f"{k:22s}", {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()
                             if kk in ("coverage", "selective_risk", "aurc", "hwsa", "fac", "utility_l2", "ece")})
    if "H1" in res:
        print("H1:", res["H1"])


if __name__ == "__main__":
    main()
