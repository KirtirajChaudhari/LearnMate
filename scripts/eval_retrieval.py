"""E6 retrieval sanity: dense vs hybrid(RRF) vs hybrid+CE on answerable items of a split.

    python scripts/eval_retrieval.py --split squad-cal
    python scripts/eval_retrieval.py --split course-dev   # needs data/annotations/course_items.jsonl
"""
import argparse
import time

from eval.retrieval_metrics import summarize
from learnmate.config import load_config, repo_path
from learnmate.io_utils import read_jsonl, write_json
from learnmate.resources import retriever_for


def load_items(split, cfg):
    if split.startswith("squad"):
        return read_jsonl(repo_path(cfg["paths"]["processed"]) / "squad_rag" / f"{split}_items.jsonl"), split
    items = [i for i in read_jsonl(repo_path(cfg["paths"]["annotations"]) / "course_items.jsonl")
             if i["split"] == split.split("-")[1]]
    return items, "course"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="squad-cal")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    if a.split.endswith("test"):
        raise SystemExit("test splits are locked; retrieval on test runs only inside the registered experiment")
    cfg = load_config()
    items, corpus = load_items(a.split, cfg)
    items = [i for i in items if i["gold_state"] != "insufficient" and i.get("gold_chunk_ids")][: a.limit]
    ret = retriever_for(corpus, cfg)
    rows = {"dense": [], "hybrid_rrf": [], "hybrid_ce": []}
    t0 = time.perf_counter()
    for it in items:
        q, gold = it["question"], it["gold_chunk_ids"]
        rows["dense"].append({"ranked": [r.chunk_id for r in ret.dense(q, k=20)], "gold": gold})
        top, cands = ret.hybrid(q)
        rows["hybrid_rrf"].append({"ranked": [c.chunk_id for c in cands], "gold": gold})
        reranked = sorted(cands, key=lambda c: -c.ce_logit)
        rows["hybrid_ce"].append({"ranked": [c.chunk_id for c in reranked], "gold": gold})
    res = {k: summarize(v) for k, v in rows.items()}
    res["seconds_per_query"] = round((time.perf_counter() - t0) / max(1, len(items)), 3)
    res["split"] = a.split
    write_json(repo_path(cfg["paths"]["results"]) / f"retrieval_{a.split}.json", res)
    for k, v in res.items():
        print(k, v)


if __name__ == "__main__":
    main()
