"""Annotation tooling for the independently checked course evaluation set (dataset plan §3-4).

    python -m learnmate.annotation validate          # schema + leakage checks on course_items.jsonl
    python -m learnmate.annotation assign-splits     # section-disjoint dev/cal/test assignment (seeded)
    python -m learnmate.annotation blind-sheet --for B --out data/annotations/second_label_B.jsonl
    python -m learnmate.annotation kappa             # agreement between author and blind second labels
    python -m learnmate.annotation judge-sheet --run results/runs/course-cal__clean --out ...
    python -m learnmate.annotation freeze            # hash items + write manifest (end of Week 2)

Nothing here *creates* gold labels: items and labels are written by the two human annotators.
"""
from __future__ import annotations

from pathlib import Path

import argparse
import random
from collections import Counter, defaultdict

from .config import load_config, repo_path
from .io_utils import read_jsonl, sha256_file, write_json, write_jsonl

CATEGORIES = {"A1": "sufficient", "A2": "sufficient", "P": "partial", "U1": "insufficient", "U2": "insufficient"}
REQUIRED = ["item_id", "question", "category", "gold_state", "gold_chunk_ids", "reference_answer", "section_path",
            "author"]
VERDICTS = ("correct_supported", "partially_correct", "incorrect", "unsupported", "abstained")


def validate_items(items: list[dict], check_store: bool = True) -> list[dict]:
    problems: list[dict] = []
    ids = Counter(i.get("item_id") for i in items)
    store = None
    if check_store:
        from .provenance import ChunkStore
        store = ChunkStore.load(repo_path(load_config()["paths"]["processed"]) / "chunks.jsonl")
    for it in items:
        iid = it.get("item_id")
        for f in REQUIRED:
            if f not in it:
                problems.append({"item_id": iid, "severity": "error", "msg": f"missing field {f}"})
        if ids[iid] > 1:
            problems.append({"item_id": iid, "severity": "error", "msg": "duplicate item_id"})
        cat = it.get("category")
        if cat not in CATEGORIES:
            problems.append({"item_id": iid, "severity": "error", "msg": f"bad category {cat}"})
        elif it.get("gold_state") != CATEGORIES[cat]:
            problems.append({"item_id": iid, "severity": "error", "msg": "gold_state inconsistent with category"})
        if it.get("gold_state") in ("sufficient", "partial") and not it.get("gold_chunk_ids"):
            problems.append({"item_id": iid, "severity": "error", "msg": "answerable item without gold_chunk_ids"})
        if it.get("gold_state") == "partial" and not it.get("uncovered_claims"):
            problems.append({"item_id": iid, "severity": "warn", "msg": "partial item without uncovered_claims"})
        if store is not None:
            for c in it.get("gold_chunk_ids", []):
                if c not in store:
                    problems.append({"item_id": iid, "severity": "error", "msg": f"unknown chunk {c}"})
        if it.get("genai_assisted") and not it.get("human_verified"):
            problems.append({"item_id": iid, "severity": "error", "msg": "gen-AI-assisted item not human-verified"})
    # section disjointness across splits
    split_of_section: dict[str, set] = defaultdict(set)
    for it in items:
        if it.get("split"):
            split_of_section[_split_key(it)].add(it["split"])
    for sec, splits in split_of_section.items():
        if len(splits) > 1:
            problems.append({"item_id": None, "severity": "error", "msg": f"section {sec} spans splits {sorted(splits)}"})
    return problems


def _split_key(it: dict) -> str:
    """Leakage unit: the d2l subsection (first 3 levels of section_path) or the held-out chapter for U2."""
    sp = it.get("section_path", "")
    parts = sp.split(" > ") if isinstance(sp, str) else list(sp)
    return " > ".join(parts[:3])


def assign_splits(items: list[dict], seed: int, frac=(0.2, 0.3, 0.5)) -> list[dict]:
    """Assign whole sections to dev/cal/test, greedily balancing item counts to the target fractions."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        groups[_split_key(it)].append(it)
    keys = sorted(groups)
    random.Random(seed).shuffle(keys)
    n = len(items)
    target = {"dev": frac[0] * n, "cal": frac[1] * n, "test": frac[2] * n}
    count = {"dev": 0, "cal": 0, "test": 0}
    for k in sorted(keys, key=lambda k: -len(groups[k])):
        split = max(target, key=lambda s: target[s] - count[s])
        for it in groups[k]:
            it["split"] = split
        count[split] += len(groups[k])
    return items


def kappa_report(items: list[dict]) -> dict:
    from sklearn.metrics import cohen_kappa_score
    pairs = [(i["gold_state"], i["label_b"]["gold_state"]) for i in items if i.get("label_b")]
    if not pairs:
        return {"n": 0}
    a, b = zip(*pairs)
    f1s = []
    for i in items:
        if i.get("label_b") and i.get("gold_chunk_ids"):
            g, h = set(i["gold_chunk_ids"]), set(i["label_b"].get("gold_chunk_ids", []))
            p = len(g & h) / len(h) if h else 0.0
            r = len(g & h) / len(g)
            f1s.append(2 * p * r / (p + r) if p + r else 0.0)
    return {"n": len(pairs), "kappa_gold_state": float(cohen_kappa_score(a, b)),
            "raw_agreement": sum(x == y for x, y in pairs) / len(pairs),
            "span_overlap_f1": sum(f1s) / len(f1s) if f1s else None,
            "confusion": Counter(f"{x}->{y}" for x, y in pairs)}


def blind_sheet(items: list[dict], for_annotator: str) -> list[dict]:
    """Items authored by the *other* annotator, with gold labels removed."""
    out = [{"item_id": i["item_id"], "question": i["question"], "section_hint": None,
            "label_b": {"gold_state": None, "gold_chunk_ids": []}} for i in items if i["author"] != for_annotator]
    random.Random(7).shuffle(out)
    return out


def judge_sheet(run_dir, items: list[dict], seed: int = 11, condition: str = "clean") -> tuple[list[dict], list[dict]]:
    """Blinded judging sheet: system identity hidden, outputs shuffled; returns (sheet, private key).

    Outputs the system itself abstained on (INSUFFICIENT_EVIDENCE / verbal refusal) need no judgment and are skipped.
    Each output is assigned to the member who did NOT author the item. Passage texts are embedded so judges can
    work offline with scripts/review.py (stdlib only).
    """
    recs = {r["item_id"]: r for r in read_jsonl(run_dir / "records.jsonl")}
    ret = {r["item_id"]: r for r in read_jsonl(run_dir / "retrieval.jsonl")}
    by_id = {i["item_id"]: i for i in items}
    rows, key = [], []
    for iid, r in recs.items():
        it = by_id.get(iid, {})
        for aset, rk in (("hyb", "hyb"), ("b1", "b1")):
            raw = r.get(f"{aset}_raw")
            if raw is None or r.get(f"{aset}_llm_insufficient"):
                continue
            oid = f"o{len(rows):05d}"
            other = {"A": "B", "B": "A"}.get(it.get("author"))
            rows.append({"output_id": oid, "question": r["question"], "answer": raw,
                         "passages": [{"chunk_id": p["chunk_id"], "text": p["text"]} for p in ret[iid][rk]],
                         "reference_answer": it.get("reference_answer"), "gold_state": it.get("gold_state"),
                         "assigned_judge": other, "verdict": None, "judge": None})
            key.append({"output_id": oid, "item_id": iid, "answer_set": aset, "condition": condition})
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    return [rows[i] for i in order], [key[i] for i in order]


def merge_judgments(sheet: list[dict], key: list[dict]) -> list[dict]:
    k = {r["output_id"]: r for r in key}
    out = []
    for s in sheet:
        if s.get("verdict") is None:
            continue
        if s["verdict"] not in VERDICTS:
            raise ValueError(f"bad verdict {s['verdict']} for {s['output_id']}")
        out.append({**k[s["output_id"]], "verdict": s["verdict"], "sentence_labels": s.get("sentence_labels"),
                    "judge": s.get("judge")})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["validate", "assign-splits", "blind-sheet", "kappa", "judge-sheet", "merge", "freeze"])
    ap.add_argument("--all-split", default=None, choices=["dev", "cal", "test"],
                    help="assign EVERY item to one split (deadline profile: all items are the locked test set)")
    ap.add_argument("--for", dest="for_annotator", default="B")
    ap.add_argument("--run", default=None)
    ap.add_argument("--sheet", default=None)
    ap.add_argument("--key", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--condition", default="clean")
    a = ap.parse_args()
    cfg = load_config()
    ann = repo_path(cfg["paths"]["annotations"])
    path = ann / "course_items.jsonl"
    items = read_jsonl(path) if path.exists() else []
    if a.cmd in ("kappa", "freeze", "validate"):
        items = [i for i in items if i.get("status") != "rejected"]
    if a.cmd == "validate":
        probs = validate_items(items)
        for p in probs:
            print(p)
        print(f"{len(items)} items; errors={sum(p['severity'] == 'error' for p in probs)} "
              f"warnings={sum(p['severity'] == 'warn' for p in probs)}; categories={Counter(i.get('category') for i in items)}")
    elif a.cmd == "assign-splits":
        if (ann / "FROZEN").exists():
            raise SystemExit("items are frozen")
        if a.all_split:
            for i in items:
                i["split"] = a.all_split
            write_jsonl(path, items)
        else:
            write_jsonl(path, assign_splits(items, cfg["project"]["seed"]))
        print(Counter(i["split"] for i in items))
    elif a.cmd == "blind-sheet":
        write_jsonl(a.out, blind_sheet(items, a.for_annotator))
    elif a.cmd == "kappa":
        rep = kappa_report(items)
        write_json(ann / "kappa_report.json", {k: (dict(v) if isinstance(v, Counter) else v) for k, v in rep.items()})
        print(rep)
    elif a.cmd == "judge-sheet":
        if not (Path(a.run) / "records.jsonl").exists():
            raise SystemExit(f"{a.run}/records.jsonl not found: the locked test runs have not completed (they refuse to start "
                             "until research/preregistration.md says STATUS: FROZEN). Run: python scripts/where_am_i.py")
        sheet, key = judge_sheet(Path(a.run), items, condition=a.condition)
        write_jsonl(a.out, sheet)
        write_jsonl(str(a.out).replace(".jsonl", "_KEY_DO_NOT_OPEN.jsonl"), key)
        print(f"{len(sheet)} outputs to judge -> {a.out}")
    elif a.cmd == "merge":
        if not Path(a.sheet).exists():
            raise SystemExit(f"{a.sheet} not found: create it with `judge-sheet` first (needs the completed test runs). Run: python scripts/where_am_i.py")
        sheet = read_jsonl(a.sheet)
        verd = {}
        for vf in sorted(Path(a.sheet).parent.glob("verdicts_*.jsonl")):
            verd.update({r["output_id"]: r for r in read_jsonl(vf)})
        for r in sheet:
            if r["output_id"] in verd:
                r["verdict"], r["judge"] = verd[r["output_id"]]["verdict"], verd[r["output_id"]]["judge"]
        rows = merge_judgments(sheet, read_jsonl(a.key))
        write_jsonl(a.out, rows)
        print(f"{len(rows)} judgments -> {a.out}")
    elif a.cmd == "freeze":
        probs = [p for p in validate_items(items) if p["severity"] == "error"]
        if probs:
            raise SystemExit(f"cannot freeze: {len(probs)} validation errors")
        man = {"n_items": len(items), "sha256": sha256_file(path), "splits": Counter(i["split"] for i in items),
               "categories": Counter(i["category"] for i in items), "kappa": kappa_report(items).get("kappa_gold_state")}
        write_json(repo_path(cfg["paths"]["manifests"]) / "course_items_manifest.json",
                   {k: (dict(v) if isinstance(v, Counter) else v) for k, v in man.items()})
        (ann / "FROZEN").write_text(man["sha256"] + "\n")
        print(man)


if __name__ == "__main__":
    main()
