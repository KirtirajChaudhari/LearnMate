"""Fine-tune the sufficiency gate (DeBERTa-v3-base cross-encoder) on SQuAD 2.0 + hard negatives (spec C6).

    python -m learnmate.gate.train --out models/gate-v1                # full config (GPU)
    python -m learnmate.gate.train --out models/gate-noHN --no-hard-negatives   # ablation A4
    python -m learnmate.gate.train --out models/gate-smoke --pairs 256 --dev-pairs 128 --epochs 1 \
        --base microsoft/deberta-v3-xsmall     # CPU smoke test only (never reported)

Checkpoints the best gate-dev AUROC model; resumable after Colab disconnects (``--resume``).
Logs wall-clock, examples/sec and peak VRAM to ``<out>/train_log.json``.
"""
from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

import numpy as np

from ..config import load_config, repo_path
from ..io_utils import read_json, sha256_text, write_json, write_jsonl
from ..seed import set_seed
from .. import squad


def build_datasets(cfg: dict, n_train: int, n_dev: int, hard_negatives: bool) -> tuple[list[dict], list[dict], dict]:
    from .data import build_pairs

    raw = repo_path(cfg["paths"]["raw"]) / "squad_v2"
    man = read_json(repo_path(cfg["paths"]["manifests"]) / "squad_splits.json")
    train = squad.load_split(raw / "train.parquet")
    gtr = train[train.title.isin(man["splits"]["gate-train"])]
    gdv = train[train.title.isin(man["splits"]["gate-dev"])]
    assert not set(gtr.title) & set(gdv.title)
    mix = dict(cfg["gate"]["mix"])
    if not hard_negatives:
        mix = {"positive": mix["positive"] / (mix["positive"] + mix["squad_negative"]),
               "squad_negative": mix["squad_negative"] / (mix["positive"] + mix["squad_negative"]),
               "hard_negative": 0.0}
    seed = cfg["project"]["seed"]
    tr = build_pairs(gtr, n_train, mix, seed)
    dv = build_pairs(gdv, n_dev, dict(cfg["gate"]["mix"]), seed + 1)  # dev always includes hard negatives
    meta = {"mix_train": mix, "n_train": len(tr), "n_dev": len(dv),
            "train_kinds": {k: sum(r["kind"] == k for r in tr) for k in ("positive", "squad_neg", "hard_neg")},
            "dev_kinds": {k: sum(r["kind"] == k for r in dv) for k in ("positive", "squad_neg", "hard_neg")},
            "train_articles": int(gtr.title.nunique()), "dev_articles": int(gdv.title.nunique())}
    return tr, dv, meta


def auroc(y: np.ndarray, p: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p)) if len(set(y.tolist())) > 1 else float("nan")


def evaluate(model, tok, rows, device, max_length, bs=64) -> dict:
    import torch
    model.eval()
    probs = []
    for a in range(0, len(rows), bs):
        b = rows[a:a + bs]
        enc = tok([r["question"] for r in b], [r["passage"] for r in b], truncation="only_second",
                  max_length=max_length, padding=True, return_tensors="pt").to(device)
        with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.float16, enabled=device == "cuda"):
            probs.append(torch.softmax(model(**enc).logits.float(), -1)[:, 1].cpu().numpy())
    p = np.concatenate(probs)
    y = np.array([r["label"] for r in rows])
    res = {"auroc": auroc(y, p), "acc@0.5": float(((p >= 0.5) == y).mean())}
    for kind in ("squad_neg", "hard_neg"):
        m = np.array([r["kind"] in ("positive", kind) for r in rows])
        res[f"auroc_pos_vs_{kind}"] = auroc(y[m], p[m])
    model.train()
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default=None, help="override base model (smoke tests only)")
    ap.add_argument("--pairs", type=int, default=None)
    ap.add_argument("--dev-pairs", type=int, default=4000)
    ap.add_argument("--epochs", type=float, default=None)
    ap.add_argument("--batch-size", type=int, default=None)
    ap.add_argument("--no-hard-negatives", action="store_true")
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

    cfg = load_config()
    g = cfg["gate"]
    set_seed(cfg["project"]["seed"])
    device = "cuda" if torch.cuda.is_available() else "cpu"
    out = repo_path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    base = a.base or cfg["models"]["gate_base"]["id"]
    revision = None if a.base else cfg["models"]["gate_base"]["revision"]

    tr, dv, meta = build_datasets(cfg, a.pairs or g["target_pairs"], a.dev_pairs, not a.no_hard_negatives)
    write_jsonl(out / "train_pairs_manifest.jsonl", ({"qid": r["qid"], "pid": r["pid"], "kind": r["kind"],
                                                       "label": r["label"]} for r in tr))
    tok = AutoTokenizer.from_pretrained(base, revision=revision)
    model = AutoModelForSequenceClassification.from_pretrained(base, revision=revision, num_labels=2).to(device)
    bs = a.batch_size or g["batch_size"]
    epochs = a.epochs or g["epochs"]
    steps_per_epoch = math.ceil(len(tr) / bs)
    total = int(steps_per_epoch * epochs)
    opt = torch.optim.AdamW(model.parameters(), lr=g["lr"], weight_decay=g["weight_decay"])
    sched = get_linear_schedule_with_warmup(opt, int(total * g["warmup_ratio"]), total)
    use_amp = bool(g["fp16"]) and device == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    state_path = out / "trainer_state.pt"
    step, best, history = 0, -1.0, []
    if a.resume and state_path.exists():
        st = torch.load(state_path, map_location=device, weights_only=True)  # own checkpoint: tensors + primitives only
        model.load_state_dict(st["model"]); opt.load_state_dict(st["opt"]); sched.load_state_dict(st["sched"])
        step, best, history = st["step"], st["best"], st["history"]
        print(f"resumed at step {step}")

    start_step = step
    rng = np.random.default_rng(cfg["project"]["seed"])
    order = np.concatenate([rng.permutation(len(tr)) for _ in range(math.ceil(epochs) + 1)])
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    t0, nan_hits = time.perf_counter(), 0
    model.train()
    while step < total:
        idx = order[step * bs:(step + 1) * bs]
        b = [tr[i] for i in idx]
        enc = tok([r["question"] for r in b], [r["passage"] for r in b], truncation="only_second",
                  max_length=g["max_length"], padding=True, return_tensors="pt").to(device)
        labels = torch.tensor([r["label"] for r in b], device=device)
        with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=use_amp):
            loss = torch.nn.functional.cross_entropy(model(**enc).logits.float(), labels)
        if not torch.isfinite(loss):
            nan_hits += 1
            opt.zero_grad(set_to_none=True)
            if nan_hits > 20:
                raise RuntimeError("repeated non-finite loss: rerun with gate.fp16=false")
            step += 1
            continue
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt); scaler.update(); sched.step(); opt.zero_grad(set_to_none=True)
        step += 1
        if step % 50 == 0:
            print(f"step {step}/{total} loss {loss.item():.4f} {(time.perf_counter()-t0):.0f}s", flush=True)
        if step % g["eval_every"] == 0 or step == total:
            ev = evaluate(model, tok, dv, device, g["max_length"])
            ev["step"] = step
            history.append(ev)
            print("gate-dev", ev, flush=True)
            if ev["auroc"] > best:
                best = ev["auroc"]
                model.save_pretrained(out / "best"); tok.save_pretrained(out / "best")
            torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(),
                        "step": step, "best": best, "history": history}, state_path)
    if step == start_step and (out / "train_log.json").exists():
        # a resume of an already-finished run does no training: do NOT overwrite the real timing/throughput log
        print(f"no training steps were run (already at step {step}/{total}); keeping the existing train_log.json")
        return
    secs = time.perf_counter() - t0
    log = {
        "base_model": base, "base_revision": revision, "device": device,
        "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
        "steps": total, "batch_size": bs, "epochs": epochs, "seconds": round(secs, 1),
        "gpu_minutes": round(secs / 60, 2) if device == "cuda" else 0.0,
        "examples_per_sec": round(total * bs / secs, 2),
        "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2) if device == "cuda" else None,
        "best_dev_auroc": best, "history": history, "data": meta, "hard_negatives": not a.no_hard_negatives,
        "config_hash": sha256_text(str(g))[:12],
        "smoke_only": bool(a.base),
    }
    write_json(out / "train_log.json", log)
    print({k: v for k, v in log.items() if k != "history"})


if __name__ == "__main__":
    main()
