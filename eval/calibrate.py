"""Fit fusion + Platt + thresholds on calibration splits and FREEZE them (spec C10, protocol §1).

    python -m eval.calibrate --squad-cal results/runs/squad-cal__clean \
                             --course-cal results/runs/course-cal__clean \
                             --judgments data/annotations/judgments_cal.jsonl \
                             [--course-dev-s4 results/runs/course-dev__S4]

Writes configs/frozen/thresholds.json (G, ablations A1-A5, B2 tau_CE, kappa_c) and a calibration report.
Test data are never read here.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from learnmate.config import load_config, repo_path
from learnmate.fuse import FEATURES, RISKY_FEATURES, FusionModel, choose_threshold, feature_matrix, uncalibrated_mean_score
from learnmate.io_utils import read_jsonl, sha256_file, write_json

from .labels import error_label, load_judgments
from .metrics import aurc, brier, ece

ABLATIONS = {
    "G": FEATURES,
    "A1_minus_verifier": ["gate_max", "gate_top2", "ce_top1", "ce_margin"],
    "A2_minus_gate": ["ce_top1", "ce_margin", "sup_min", "sup_mean", "claim_conflict", "sp_contra", "uncited_frac"],
}


def labelled(run_dir: Path, judgments) -> list[dict]:
    recs = read_jsonl(run_dir / "records.jsonl")
    out = []
    for r in recs:
        e = error_label(r, "hyb", "clean", judgments)
        if e is None:
            continue
        r["error"] = e
        r["can_answer"] = not r["hyb_llm_insufficient"]
        out.append(r)
    return out


def swap_gate(recs, key):
    out = []
    for r in recs:
        if r.get(key) is None:
            return None
        rr = dict(r)
        rr["features"] = {**r["features"], **r[key]}
        out.append(rr)
    return out


def fit_variant(name, feats, sq, cc, lam, report):
    fit_rows = [r for r in sq if r["can_answer"]]
    X = feature_matrix(fit_rows, feats)
    y = np.array([1 - r["error"] for r in fit_rows])
    fm = FusionModel(features=feats).fit(X, y)
    Xc = feature_matrix([r for r in cc if r["can_answer"]], feats)
    yc = np.array([1 - r["error"] for r in cc if r["can_answer"]])
    fm.fit_platt(Xc, yc)
    s = np.array([fm.predict_proba(feature_matrix([r], feats))[0] if r["can_answer"] else -np.inf for r in cc])
    thr = choose_threshold(np.where(np.isfinite(s), s, -1.0), [1 - r["error"] for r in cc],
                           [r["can_answer"] for r in cc], lam)
    fm.tau = thr["tau"]
    ps = s[np.isfinite(s)]
    report[name] = {"features": feats, "C": fm.C, "coef": dict(zip(feats, np.round(fm.coef_, 4).tolist())),
                    "platt": [fm.platt_a, fm.platt_b], "threshold": thr,
                    "cal_aurc": aurc(np.where(np.isfinite(s), s, -1.0), [r["error"] for r in cc]),
                    "cal_ece": ece(ps, yc) if len(ps) else None, "cal_brier": brier(ps, yc) if len(ps) else None,
                    "n_fit_squad": len(fit_rows), "n_cal_course": len(cc)}
    return fm.to_dict()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--squad-cal", required=True)
    ap.add_argument("--course-cal", required=True)
    ap.add_argument("--judgments", required=True)
    ap.add_argument("--course-dev-s4", default=None, help="dev S4 run used to set kappa_c (never test)")
    ap.add_argument("--allow-squad-as-course", action="store_true",
                    help="PIPELINE SMOKE ONLY: use squad-cal for the course-cal role (never for reported results)")
    a = ap.parse_args()
    cfg = load_config()
    lam = cfg["decision"]["utility_lambda"]
    if "test" in a.squad_cal or "test" in a.course_cal:
        raise SystemExit("calibration must not read test runs")
    judg = load_judgments(a.judgments) if Path(a.judgments).exists() else None
    sq = labelled(Path(a.squad_cal), None)
    cc = labelled(Path(a.course_cal), judg)
    if not cc:
        raise SystemExit("no labelled course-cal records (are judgments complete?)")
    report: dict = {"lambda": lam}
    frozen: dict = {"s_min": cfg["verification"]["support_threshold"], "lambda": lam, "variants": {}}
    for name, feats in ABLATIONS.items():
        frozen["variants"][name] = fit_variant(name, feats, sq, cc, lam, report)
    for name, key in (("A4_gate_noHN", "a4_gate"), ("A5_untrained_gate", "a5_gate")):
        sq2, cc2 = swap_gate(sq, key), swap_gate(cc, key)
        if sq2 and cc2:
            frozen["variants"][name] = fit_variant(name, FEATURES, sq2, cc2, lam, report)
    # A3: uncalibrated normalized mean, tau = 0.5 (no fitting on outcomes)
    Xs = feature_matrix(sq, FEATURES)
    frozen["variants"]["A3_minus_calibration"] = {"features": FEATURES, "lo": Xs.min(0).tolist(),
                                                  "hi": Xs.max(0).tolist(),
                                                  "invert": [f in RISKY_FEATURES for f in FEATURES], "tau": 0.5}
    # B2: CE threshold with the same utility rule
    ce = np.array([r["features"]["ce_top1"] for r in cc])
    b2 = choose_threshold(ce, [1 - r["error"] for r in cc], [r["can_answer"] for r in cc], lam)
    frozen["tau_b2"] = b2["tau"]
    report["B2"] = {"threshold": b2, "cal_aurc": aurc(np.where([r["can_answer"] for r in cc], ce, -1.0),
                                                      [r["error"] for r in cc])}
    # B0 (extractive reference): threshold on the best span-vs-null margin, fitted on squad-cal (auto labels)
    b0_rows = [r for r in sq if r.get("b0_answer")]
    if b0_rows:
        from .labels import b0_error
        mg = np.array([r["b0_answer"]["margin"] for r in b0_rows])
        ok = np.array([1 - b0_error(r) for r in b0_rows])
        b0 = choose_threshold(mg, ok, [True] * len(b0_rows), lam)
        frozen["tau_b0"] = b0["tau"]
        report["B0"] = {"threshold": b0, "cal_aurc": aurc(mg, 1 - ok), "fitted_on": "squad-cal"}
    # kappa_c from dev S4 (constructed contradictions) vs dev clean: smallest threshold flagging no clean dev item
    kc = None
    if a.course_dev_s4:
        s4 = read_jsonl(Path(a.course_dev_s4) / "records.jsonl")
        clean_dir = Path(str(a.course_dev_s4).replace("__S4", "__clean"))
        cl = read_jsonl(clean_dir / "records.jsonl") if (clean_dir / "records.jsonl").exists() else []
        clean_max = max((r["features"].get("claim_conflict", 0.0) for r in cl), default=0.0)
        s4_vals = sorted(r["features"].get("claim_conflict", 0.0) for r in s4)
        kc = float(min(0.99, max(0.5, clean_max + 1e-3)))
        report["kappa_c"] = {"clean_dev_max_claim_conflict": clean_max, "s4_dev_claim_conflict": s4_vals,
                             "s4_dev_recall": float(np.mean([v >= kc for v in s4_vals])) if s4_vals else None}
    frozen["kappa_c"] = kc
    frozen["fusion"] = frozen["variants"]["G"]
    frozen["inputs"] = {"squad_cal_records_sha256": sha256_file(Path(a.squad_cal) / "records.jsonl"),
                        "course_cal_records_sha256": sha256_file(Path(a.course_cal) / "records.jsonl"),
                        "judgments_sha256": sha256_file(a.judgments) if Path(a.judgments).exists() else None}
    if a.allow_squad_as_course:
        frozen["SMOKE_ONLY"] = True
        out = repo_path(cfg["paths"]["results"]) / "smoke" / "thresholds_smoke.json"
    else:
        out = repo_path(cfg["paths"]["frozen"]) / "thresholds.json"
    write_json(out, frozen)
    write_json(out.with_name(out.stem + "_report.json"), report)
    print("wrote", out)
    for k, v in report.items():
        if isinstance(v, dict) and "threshold" in v:
            print(k, v["threshold"], "cal_aurc", round(v["cal_aurc"], 4))


if __name__ == "__main__":
    main()
