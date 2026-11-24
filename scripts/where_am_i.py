"""Print which pipeline prerequisites exist and the single next step. Run anywhere (Colab or laptop); stdlib only.

    python scripts/where_am_i.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
ANN = ROOT / "data/annotations"


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).exists() else []


def exists(p):
    return (ROOT / p).exists()


def main():
    items = jl(ANN / "course_items.jsonl")
    patch = {}
    for f in sorted(ANN.glob("decisions_*.jsonl")):
        for r in jl(f):
            patch[r["item_id"]] = r["patch"]
    labels = {}
    for f in sorted(ANN.glob("labels_*.jsonl")):
        for r in jl(f):
            labels[r["item_id"]] = r["label_b"]
    for it in items:
        it.update(patch.get(it["item_id"], {}))
        if it["item_id"] in labels:
            it["label_b"] = labels[it["item_id"]]
    live = [i for i in items if i.get("status") != "rejected"]
    verified = [i for i in live if i.get("human_verified")]
    unreviewed = len(live) - len(verified)
    by_member = {m: sum(1 for i in items if i["author"] == m and (i["item_id"] in patch)) for m in "AB"}
    labelled = sum(1 for i in verified if i.get("label_b"))
    gate_ok = exists("models/gate-v1/best")
    sq_cal = exists("results/runs/squad-cal__clean/records.jsonl")
    thr = exists("configs/frozen/thresholds.json")
    man = exists("data/manifests/course_items_manifest.json")
    pre = exists("research/preregistration.md") and "STATUS: FROZEN" in (ROOT / "research/preregistration.md").read_text()
    runs = {n: exists(f"results/runs/{n}/records.jsonl") for n in ("course-test__clean", "course-test__S1", "squad-test__clean")}
    sheet = exists("data/annotations/judge_test.jsonl")
    verd = sorted(p.name for p in ANN.glob("verdicts_*.jsonl"))
    judg = exists("data/annotations/judgments_test.jsonl")
    ana = exists("results/runs/course-test__clean/analysis.json")

    steps = [
        ("Gate trained (models/gate-v1/best)", gate_ok, "notebook 03, Part 1a"),
        ("SQuAD calibration run (squad-cal__clean)", sq_cal, "notebook 03, Part 1b"),
        ("Thresholds frozen (configs/frozen/thresholds.json)", thr, "notebook 03: `python -m eval.calibrate --squad-cal results/runs/squad-cal__clean`"),
        (f"Items verified by members ({len(verified)}/{len(live)} accepted; unreviewed {unreviewed}; decision files for A={by_member['A']} B={by_member['B']} items)",
         bool(live) and unreviewed == 0 and all(by_member[m] > 0 for m in "AB"),
         "each member: `python scripts/review.py verify --member A|B`, then commit+push decisions_X.jsonl"),
        ("Items frozen (course_items_manifest.json)", man, "Colab: git pull; review.py apply; annotation assign-splits --all-split test; annotation freeze"),
        ("Pre-registration FROZEN", pre, "Colab: `python scripts/freeze_prereg.py --dtype float16`"),
        ("Test runs done: " + ", ".join(f"{k}={'yes' if v else 'NO'}" for k, v in runs.items()), all(runs.values()), "notebook 03 'locked test runs' cell"),
        ("Judging sheet created", sheet, "notebook 03 'blinded judging sheet' cell, then commit+push the sheet and KEY"),
        (f"Blind second labels, do these in PARALLEL with the GPU runs ({labelled}/{len(verified)})", bool(verified) and labelled == len(verified),
         "each member: `python scripts/review.py second-label --member A|B`, then commit+push labels_X.jsonl"),
        (f"Verdict files pushed: {verd}", len(verd) >= 2, "each member: `python scripts/review.py judge --sheet data/annotations/judge_test.jsonl --member A|B`"),
        ("Judgments merged (judgments_test.jsonl)", judg, "notebook 03 merge cell"),
        ("Analysis written (analysis.json)", ana, "notebook 03 analysis cell"),
    ]
    nxt = None
    for name, ok, how in steps:
        print(("[x] " if ok else "[ ] ") + name)
        if not ok and nxt is None:
            nxt = (name, how)
    print()
    print("NEXT STEP:", f"{nxt[0].split(' (')[0]}\n   how: {nxt[1]}" if nxt else "everything is done; send me the analysis.json files")


if __name__ == "__main__":
    main()
