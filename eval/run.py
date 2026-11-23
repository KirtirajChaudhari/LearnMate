"""Staged, cached experiment runner (spec C11, ADR-009). One model on the device at a time.

    python -m eval.run --split course-dev --stages retrieve generate gate verify
    python -m eval.run --split squad-cal  --stages retrieve generate gate verify --limit 200
    python -m eval.run --split course-test --condition S1 --stages all --require-prereg

Splits: course-dev | course-cal | course-test | squad-cal | squad-test
Outputs: results/runs/<split>__<condition>/{retrieval,gen_b1,gen_hyb,gate,verify,b0}.jsonl and records.jsonl
Test splits refuse to run unless research/preregistration.md is FROZEN and configs/frozen/thresholds.json exists.
"""
from __future__ import annotations

import argparse
import gc
import time
from pathlib import Path

from learnmate.citations import parse_answer
from learnmate.config import load_config, repo_path
from learnmate.io_utils import env_fingerprint, read_jsonl, sha256_file, write_json, write_jsonl
from learnmate.provenance import ChunkStore
from learnmate.retrieve import Retrieved, ce_features

from .stress import EDIT_SUFFIX, apply_post_retrieval, exclude_ids

STAGES = ["retrieve", "generate", "gate", "gate_noHN", "b0", "verify", "assemble"]  # "evaluator" runs separately (test only)


# ------------------------------------------------------------------ data
def load_split(split: str, cfg: dict) -> tuple[list[dict], str]:
    if split.startswith("squad"):
        return read_jsonl(repo_path(cfg["paths"]["processed"]) / "squad_rag" / f"{split}_items.jsonl"), split
    part = split.split("-", 1)[1]
    path = repo_path(cfg["paths"]["annotations"]) / "course_items.jsonl"
    if not path.exists():
        raise SystemExit(f"{path} missing: course items are authored by the two annotators (see "
                         "research/dataset_and_annotation_plan.md and annotation/GUIDELINES.md)")
    items = [i for i in read_jsonl(path) if i.get("split") == part and i.get("status", "final") == "final"]
    return items, "course"


def check_prereg(cfg: dict) -> dict:
    pre = repo_path("research/preregistration.md")
    thr = repo_path(cfg["paths"]["frozen"]) / "thresholds.json"
    if not pre.exists() or "STATUS: FROZEN" not in pre.read_text():
        raise SystemExit("test split locked: research/preregistration.md missing or not 'STATUS: FROZEN'")
    if not thr.exists():
        raise SystemExit("test split locked: configs/frozen/thresholds.json missing (run eval.calibrate first)")
    return {"preregistration_sha256": sha256_file(pre), "thresholds_sha256": sha256_file(thr)}


def _passage_dicts(top: list[Retrieved], store: ChunkStore | None, titles: dict[str, str]) -> list[dict]:
    out = []
    for r in top:
        base = r.chunk_id.split(EDIT_SUFFIX)[0]
        path = store.get(base).display_path if store is not None and base in store else titles.get(base, "")
        out.append({"chunk_id": r.chunk_id, "text": r.text, "section_path_str": path})
    return out


def _free():
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
    except ImportError:
        pass


def _peak_vram() -> float | None:
    try:
        import torch
        return round(torch.cuda.max_memory_allocated() / 1e9, 3) if torch.cuda.is_available() else None
    except ImportError:
        return None


# ------------------------------------------------------------------ stages
def stage_retrieve(items, corpus, cfg, condition, out: Path):
    from learnmate.resources import retriever_for
    edits = {}
    ep = repo_path(cfg["paths"]["annotations"]) / "stress_edits.jsonl"
    if condition in ("S3", "S4"):
        if not ep.exists():
            raise SystemExit(f"{ep} missing (S3/S4 edits are authored per dataset plan §6)")
        edits = {e["item_id"]: e for e in read_jsonl(ep)}
    ret = retriever_for(corpus, cfg)
    rows, lat = [], []
    for it in items:
        t = time.perf_counter()
        ex = exclude_ids(condition, it)
        b1 = ret.dense(it["question"], k=cfg["retrieval"]["b1_dense_top"], exclude=ex)
        top, cands = ret.hybrid(it["question"], exclude=ex)
        if condition in ("S2", "S3", "S4"):
            b1 = apply_post_retrieval(condition, it, b1, b1, edits)
            top = apply_post_retrieval(condition, it, top, cands, edits)
            # re-score any passage whose text changed so CE features describe what the model sees
            changed = [r for r in top if r.extra.get("stress") in ("S3_edited", "S4_edited_copy")]
            if changed and ret.reranker is not None:
                lg = ret.reranker.score(it["question"], [r.text for r in changed])
                import numpy as np
                for r, l in zip(changed, lg):
                    r.ce_logit, r.ce_prob = float(l), float(1 / (1 + np.exp(-l)))
        lat.append(time.perf_counter() - t)
        rows.append({"item_id": it["item_id"], "condition": condition,
                     "b1": [r.to_dict() for r in b1], "hyb": [r.to_dict() for r in top],
                     "cand_ids": [c.chunk_id for c in cands], "ce": ce_features(top)})
    write_jsonl(out / "retrieval.jsonl", rows)
    return {"retrieve_p50_s": _pct(lat, 50), "retrieve_p95_s": _pct(lat, 95)}


def stage_generate(items, corpus, cfg, out: Path, backend=None):
    from learnmate.generate import GenerationCache, generate_cached, generator_from_cfg
    store = ChunkStore.load(repo_path(cfg["paths"]["processed"]) / "chunks.jsonl") if corpus == "course" else None
    titles = {}
    if corpus != "course":
        titles = {r["chunk_id"]: r["title"] for r in read_jsonl(repo_path(cfg["paths"]["processed"]) / "squad_rag" / f"{corpus}_corpus.jsonl")}
    ret = {r["item_id"]: r for r in read_jsonl(out / "retrieval.jsonl")}
    gen = generator_from_cfg(cfg, backend=backend)
    cache = GenerationCache(repo_path(cfg["paths"]["cache"]) / f"generations_{corpus}.jsonl")
    lat = {"b1": [], "hyb": []}
    rows = {"b1": [], "hyb": []}
    q = {i["item_id"]: i["question"] for i in items}
    for iid in [i["item_id"] for i in items]:
        for which in ("b1", "hyb"):
            top = [Retrieved(**r) for r in ret[iid][which]]
            pd_ = _passage_dicts(top, store, titles)
            g = generate_cached(gen, cache, q[iid], pd_, cfg["generation"]["max_new_tokens"])
            lat[which].append(g["latency_s"])
            rows[which].append({"item_id": iid, "passages": pd_, "raw": g["text"], "model": g["model"],
                                "latency_s": g["latency_s"], "new_tokens": g.get("new_tokens")})
    write_jsonl(out / "gen_b1.jsonl", rows["b1"])
    write_jsonl(out / "gen_hyb.jsonl", rows["hyb"])
    m = {"generate_p50_s": _pct(lat["hyb"], 50), "generate_p95_s": _pct(lat["hyb"], 95),
         "generator": gen.tag, "generate_peak_vram_gb": _peak_vram()}
    del gen
    return m


def stage_gate(items, cfg, out: Path, gate_dir: str, name: str = "gate"):
    from learnmate.gate.model import GateScorer, aggregate
    ret = {r["item_id"]: r for r in read_jsonl(out / "retrieval.jsonl")}
    scorer = GateScorer(gate_dir, max_length=cfg["gate"]["max_length"])
    rows, lat = [], []
    for it in items:
        t = time.perf_counter()
        hyb = ret[it["item_id"]]["hyb"]
        p = scorer.score([it["question"]] * len(hyb), [r["text"] for r in hyb])
        lat.append(time.perf_counter() - t)
        rows.append({"item_id": it["item_id"], "probs": [float(x) for x in p], **aggregate(p)})
    write_jsonl(out / f"{name}.jsonl", rows)
    return {f"{name}_p50_s": _pct(lat, 50), f"{name}_peak_vram_gb": _peak_vram(), f"{name}_dir": gate_dir}


def stage_untrained_gate(items, cfg, out: Path):
    """Ablation A5: off-the-shelf SQuAD2 no-answer probability as the gate signal."""
    from learnmate.gate.model import SquadNoAnswerGate, aggregate
    m = cfg["models"]["extractive_b0"]
    g = SquadNoAnswerGate(m["id"], m["revision"])
    ret = {r["item_id"]: r for r in read_jsonl(out / "retrieval.jsonl")}
    rows = []
    for it in items:
        res = [g.answer(it["question"], r["text"]) for r in ret[it["item_id"]]["hyb"]]
        rows.append({"item_id": it["item_id"], "probs": [r["p_answer"] for r in res],
                     **aggregate([r["p_answer"] for r in res]),
                     "b0_best": max(res, key=lambda r: r["margin"]) if res else None})
    write_jsonl(out / "b0.jsonl", rows)
    return {"b0_peak_vram_gb": _peak_vram()}


def stage_verify(items, corpus, cfg, out: Path):
    from learnmate.verify import MiniCheckFT5, NLIModel, Verifier
    m, v = cfg["models"], cfg["verification"]
    ver = Verifier(MiniCheckFT5(m["minicheck"]["id"], m["minicheck"]["revision"], max_len=v["minicheck_max_len"],
                                chunk_words=v["minicheck_chunk_words"]),
                   NLIModel(m["nli"]["id"], m["nli"]["revision"]), v["support_threshold"], v["contradiction_pairs_top"])
    rows, lat = [], []
    for r in read_jsonl(out / "gen_hyb.jsonl"):
        ids = [p["chunk_id"] for p in r["passages"]]
        insufficient, sents = parse_answer(r["raw"], ids)
        t = time.perf_counter()
        feats = ver.verify(sents, {p["chunk_id"]: p["text"] for p in r["passages"]}, ids)
        lat.append(time.perf_counter() - t)
        rows.append({"item_id": r["item_id"], "llm_insufficient": insufficient,
                     "sentences": [s.to_dict() for s in sents], "features": feats})
    write_jsonl(out / "verify.jsonl", rows)
    return {"verify_p50_s": _pct(lat, 50), "verify_peak_vram_gb": _peak_vram()}


def stage_evaluator(items, cfg, out: Path):
    """Independent secondary auto-evaluator (LettuceDetect). Never used for any decision."""
    try:
        from lettucedetect.models.inference import HallucinationDetector
    except ImportError:
        raise SystemExit("pip install 'learnmate[eval]' (lettucedetect) for the evaluator stage")
    m = cfg["models"]["evaluator_lettuce"]
    det = HallucinationDetector(method="transformer", model_path=m["id"])
    q = {i["item_id"]: i["question"] for i in items}
    rows = []
    for r in read_jsonl(out / "gen_hyb.jsonl"):
        spans = det.predict(context=[p["text"] for p in r["passages"]], question=q[r["item_id"]],
                            answer=r["raw"], output_format="spans")
        rows.append({"item_id": r["item_id"], "spans": spans})
    write_jsonl(out / "evaluator_lettuce.jsonl", rows)
    return {}


def stage_assemble(items, out: Path):
    """Merge stage outputs into one record per item (inputs to calibration and analysis)."""
    def load(name):
        p = out / name
        return {r["item_id"]: r for r in read_jsonl(p)} if p.exists() else {}
    ret, g1, gh, gate, ver, b0 = (load(n) for n in ("retrieval.jsonl", "gen_b1.jsonl", "gen_hyb.jsonl",
                                                     "gate.jsonl", "verify.jsonl", "b0.jsonl"))
    gate_nohn = load("gate_noHN.jsonl")
    recs = []
    for it in items:
        iid = it["item_id"]
        f = dict(ret[iid]["ce"]) if iid in ret else {}
        if iid in gate:
            f.update({"gate_max": gate[iid]["gate_max"], "gate_top2": gate[iid]["gate_top2"]})
        if iid in ver:
            f.update(ver[iid]["features"])
        b1_ins, b1_s = parse_answer(g1[iid]["raw"], [p["chunk_id"] for p in g1[iid]["passages"]]) if iid in g1 else (None, [])
        rec = {
            "item_id": iid, "question": it["question"], "gold_state": it.get("gold_state"),
            "category": it.get("category"), "has_math": it.get("has_math", False),
            "gold_chunk_ids": it.get("gold_chunk_ids", []), "gold_answers": it.get("gold_answers"),
            "features": f,
            "hyb_ids": [r["chunk_id"] for r in ret[iid]["hyb"]] if iid in ret else [],
            "b1_ids": [r["chunk_id"] for r in ret[iid]["b1"]] if iid in ret else [],
            "hyb_raw": gh.get(iid, {}).get("raw"), "b1_raw": g1.get(iid, {}).get("raw"),
            "hyb_llm_insufficient": ver.get(iid, {}).get("llm_insufficient"),
            "b1_llm_insufficient": b1_ins,
            "hyb_sentences": ver.get(iid, {}).get("sentences", []),
            "a4_gate": {k: gate_nohn[iid][k] for k in ("gate_max", "gate_top2")} if iid in gate_nohn else None,
            "a5_gate": {k: b0[iid][k] for k in ("gate_max", "gate_top2")} if iid in b0 else None,
            "b0_answer": b0[iid]["b0_best"] if iid in b0 else None,
        }
        recs.append(rec)
    write_jsonl(out / "records.jsonl", recs)
    return {"n_records": len(recs)}


def _pct(xs, q):
    import numpy as np
    return round(float(np.percentile(xs, q)), 4) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--condition", default="clean", choices=["clean", "S1", "S2", "S3", "S4"])
    ap.add_argument("--stages", nargs="+", default=["all"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--gate-dir", default="models/gate-v1/best")
    ap.add_argument("--gate-nohn-dir", default="models/gate-noHN/best")
    ap.add_argument("--backend", default=None, help="override generation backend (llamacpp = CPU smoke only)")
    ap.add_argument("--require-prereg", action="store_true")
    ap.add_argument("--tag", default="", help="optional suffix for the output directory")
    a = ap.parse_args()
    cfg = load_config()
    items, corpus = load_split(a.split, cfg)
    items = items[: a.limit] if a.limit else items
    guard = {}
    if a.split.endswith("test") or a.require_prereg:
        guard = check_prereg(cfg)
    out = repo_path(cfg["paths"]["results"]) / "runs" / f"{a.split}__{a.condition}{a.tag}"
    out.mkdir(parents=True, exist_ok=True)
    stages = STAGES if a.stages == ["all"] else a.stages
    metrics = {"split": a.split, "condition": a.condition, "n_items": len(items), "env": env_fingerprint(), **guard}
    if a.backend == "llamacpp":
        metrics["warning"] = "llamacpp backend: CPU smoke run, not an evaluation result"
    for st in stages:
        t = time.perf_counter()
        print(f"[{st}] {len(items)} items -> {out}", flush=True)
        if st == "retrieve":
            metrics.update(stage_retrieve(items, corpus, cfg, a.condition, out))
        elif st == "generate":
            metrics.update(stage_generate(items, corpus, cfg, out, a.backend))
        elif st == "gate":
            metrics.update(stage_gate(items, cfg, out, str(repo_path(a.gate_dir))))
        elif st == "gate_noHN":
            metrics.update(stage_gate(items, cfg, out, str(repo_path(a.gate_nohn_dir)), name="gate_noHN"))
        elif st == "b0":
            metrics.update(stage_untrained_gate(items, cfg, out))
        elif st == "verify":
            metrics.update(stage_verify(items, corpus, cfg, out))
        elif st == "evaluator":
            metrics.update(stage_evaluator(items, cfg, out))
        elif st == "assemble":
            metrics.update(stage_assemble(items, out))
        metrics[f"{st}_wall_s"] = round(time.perf_counter() - t, 1)
        _free()
        write_json(out / "run_meta.json", metrics)
    print({k: v for k, v in metrics.items() if k != "env"})


if __name__ == "__main__":
    main()
