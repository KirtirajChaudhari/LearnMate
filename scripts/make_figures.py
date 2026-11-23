"""Figures for Deliverable E/G, generated only from real analysis outputs (no placeholder data).

    python scripts/make_figures.py [--runs results/runs] [--out results/figures]
Skips any figure whose inputs do not exist yet.
"""
import argparse
from pathlib import Path

import numpy as np

from eval.analyze import system_scores
from eval.labels import error_label, load_judgments
from eval.metrics import risk_coverage_curve
from learnmate.config import load_config, repo_path
from learnmate.io_utils import read_json, read_jsonl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--out", default="results/figures")
    ap.add_argument("--judgments", default="data/annotations/judgments_test.jsonl")
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cfg = load_config()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    frozen_p = repo_path(cfg["paths"]["frozen"]) / "thresholds.json"
    if not frozen_p.exists():
        print("no frozen thresholds yet; nothing to plot"); return
    frozen = read_json(frozen_p)
    judg = load_judgments(a.judgments) if Path(a.judgments).exists() else None
    colors = {"B2": "#888888", "G": "#1f6feb", "A1_minus_verifier": "#d29922", "A2_minus_gate": "#8250df"}
    for split in ("course-test", "squad-test"):
        run = Path(a.runs) / f"{split}__clean"
        if not (run / "records.jsonl").exists():
            continue
        recs = [r for r in read_jsonl(run / "records.jsonl") if error_label(r, "hyb", "clean", judg) is not None]
        err = np.array([error_label(r, "hyb", "clean", judg) for r in recs])
        S = system_scores(recs, frozen)
        fig, ax = plt.subplots(figsize=(4.5, 3.4))
        for name, col in colors.items():
            if name in S:
                cov, risk = risk_coverage_curve(S[name]["score"], err)
                ax.plot(cov, risk, label=name, color=col, lw=1.8)
        b1 = S["B1"]["answered"]
        ax.scatter([b1.mean()], [err[b1].mean() if b1.any() else np.nan], marker="x", color="k", label="B1 (point)")
        ax.set_xlabel("coverage"); ax.set_ylabel("selective risk"); ax.set_title(f"Risk–coverage ({split})")
        ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(out / f"risk_coverage_{split}.png", dpi=200)
        an = run / "analysis.json"
        if an.exists():
            rel = read_json(an)["systems"]["G"].get("reliability")
            if rel:
                fig, ax = plt.subplots(figsize=(3.4, 3.4))
                pts = [(b["mean_p"], b["frac_safe"], b["n"]) for b in rel if b["n"]]
                ax.plot([0, 1], [0, 1], ls="--", color="#999")
                ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=[10 + 3 * p[2] for p in pts], color="#1f6feb")
                ax.set_xlabel("predicted P(safe)"); ax.set_ylabel("observed safe rate"); ax.set_title(f"Reliability G ({split})")
                fig.tight_layout(); fig.savefig(out / f"reliability_{split}.png", dpi=200)
    # stress bars (HwSA / coverage per condition)
    rows = []
    for cond in ("clean", "S1", "S2", "S3", "S4"):
        an = Path(a.runs) / f"course-test__{cond}" / "analysis.json"
        if an.exists():
            s = read_json(an)["systems"]
            rows.append((cond, {k: s[k]["coverage"] for k in ("B1", "B2", "G") if k in s}))
    if rows:
        fig, ax = plt.subplots(figsize=(5, 3))
        w = 0.25
        for j, sysname in enumerate(("B1", "B2", "G")):
            ax.bar(np.arange(len(rows)) + (j - 1) * w, [r[1].get(sysname, np.nan) for r in rows], w, label=sysname)
        ax.set_xticks(range(len(rows))); ax.set_xticklabels([r[0] for r in rows]); ax.set_ylabel("answer rate")
        ax.set_title("Answer rate by stress condition (course-test)"); ax.legend(fontsize=7)
        fig.tight_layout(); fig.savefig(out / "stress_answer_rate.png", dpi=200)
    print("figures ->", out)


if __name__ == "__main__":
    main()
