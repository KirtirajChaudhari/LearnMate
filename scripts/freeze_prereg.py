"""Write research/preregistration.md (STATUS: FROZEN) with real hashes. Run AFTER calibration, BEFORE any test run.

    python scripts/freeze_prereg.py [--gate-dir models/gate-v1] [--m 10] [--lam 2]
The test runner refuses to start unless this file exists with 'STATUS: FROZEN' and thresholds.json exists.
"""
import argparse
import subprocess
from datetime import datetime, timezone

from learnmate.config import load_config, repo_path
from learnmate.io_utils import read_json, sha256_file
from learnmate.prompts import prompt_hash


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-dir", default="models/gate-v1")
    ap.add_argument("--m", type=float, default=None)
    ap.add_argument("--lam", type=float, default=None)
    ap.add_argument("--dtype", default=None)
    a = ap.parse_args()
    cfg = load_config()
    thr = repo_path(cfg["paths"]["frozen"]) / "thresholds.json"
    items_man = repo_path(cfg["paths"]["manifests"]) / "course_items_manifest.json"
    if not thr.exists() or not items_man.exists():
        raise SystemExit("need configs/frozen/thresholds.json (eval.calibrate) and course_items_manifest.json (annotation freeze)")
    frozen = read_json(thr)
    log = repo_path(a.gate_dir) / "train_log.json"
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit = "unknown"
    man = read_json(items_man)
    m = a.m if a.m is not None else cfg["decision"]["coverage_margin_pp"]
    lam = a.lam if a.lam is not None else cfg["decision"]["utility_lambda"]
    text = f"""# LearnMate Pre-registration

STATUS: FROZEN

- Frozen at (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}
- Code commit: {commit}
- Course items manifest sha256: {man['sha256']}  ({man['n_items']} items; splits {man['splits']}; kappa(gold state) = {man.get('kappa')})
- Frozen thresholds sha256: {sha256_file(thr)}
- Threshold profile: {frozen.get('profile')}
- Prompt: {cfg['generation']['prompt_version']} / hash {prompt_hash()}
- Generator: {cfg['models']['generator']['id']} @ {cfg['models']['generator']['revision'][:10]}, dtype {a.dtype or cfg['generation']['dtype']}, greedy decoding
- Gate checkpoint: {a.gate_dir}/best  (train_log sha256 {sha256_file(log) if log.exists() else 'n/a'})
- Analysis code: eval/analyze.py (commit above)

## Hypothesis (research/final_research_problem.md section 5, unchanged)
H1: on the course test items, the paired-bootstrap 95% CI (10,000 resamples, seed 2026) of AURC(G) - AURC(B2) lies entirely
below 0, AND answerable-coverage(G) >= answerable-coverage(B2) - m.
H1 is evaluated once, on course-test, condition `clean`. Everything else is secondary/descriptive.

## Fixed values
- m = {m} percentage points (team-set; instructor confirmation: pending)
- lambda = {lam} for threshold selection; reported lambda in {{1, 2, 4}}
- s_min = {frozen.get('s_min')}; kappa_c = {frozen.get('kappa_c')} (None = contradiction state disabled: no dev S4 items were built)
- Error definition: strict (partially_correct counts as an error)

## Documented deviations from the frozen specification (time-compressed submission profile)
1. Course set is smaller than the 150-item floor and is used entirely as the locked test set (no course-dev / course-cal).
2. Fusion weights, tau, tau_CE and tau_B0 are fitted on squad-cal ONLY, in-sample, without Platt recalibration; they are applied to course-test with no domain adaptation.
3. Gate trained on a reduced pair budget (see train_log.json); ablation A4 (no hard negatives) not run.
4. SQuAD-RAG sets use {cfg['squad']['rag_sample_per_split']} questions instead of 1,500 per split.
5. Stress conditions S3, S4 not run; S2 not run (no judging capacity); S1 is run. Human judging was done by one member per output (the member who did not author the item), without double-judging.
6. Course items were drafted by an AI assistant from the corpus text and then verified, edited or rejected by the two members, each of whom also labelled the other's items blind (disclosed per item: genai_assisted=true).

## Runs executed once after this commit
course-test x {{clean, S1}}; squad-test x clean. Systems B1, B2, G, A1, A2, A3, A5 (+B0 on SQuAD). Anything else is exploratory.
"""
    out = repo_path("research/preregistration.md")
    out.write_text(text)
    print("wrote", out)


if __name__ == "__main__":
    main()
