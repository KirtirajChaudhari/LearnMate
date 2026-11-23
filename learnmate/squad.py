"""SQuAD 2.0 audit, article-level splits and SQuAD-RAG construction (dataset plan §1).

Partitions (all by article title, seeded):
  gate-train : train articles minus ``gate_dev_articles`` held-out  -> gate training pairs
  gate-dev   : held-out train articles                              -> gate early stopping / sanity AUROC
  squad-cal  : ``cal_articles`` of the 35 dev articles               -> fusion LR fit (open retrieval)
  squad-test : remaining dev articles                               -> secondary confirmatory test (locked)
"""
from __future__ import annotations

import random
import re
import string
from collections import Counter
from pathlib import Path

import pandas as pd

from .io_utils import sha256_file, stable_id, write_json

HF_PARQUET = "https://huggingface.co/api/datasets/rajpurkar/squad_v2/parquet/squad_v2/{split}/0.parquet"


def download_squad(out_dir: str | Path) -> dict[str, Path]:
    """Download the official HF parquet conversion (train, validation)."""
    import urllib.request

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for split in ("train", "validation"):
        p = out_dir / f"{split}.parquet"
        if not p.exists():
            urllib.request.urlretrieve(HF_PARQUET.format(split=split), p)
        paths[split] = p
    return paths


def load_split(path: str | Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["answer_texts"] = df["answers"].apply(lambda a: [str(t) for t in a["text"]])
    df["is_impossible"] = df["answer_texts"].apply(lambda t: len(t) == 0)
    df["paragraph_id"] = [stable_id(t, c, n=12) for t, c in zip(df["title"], df["context"])]
    return df


def audit(df: pd.DataFrame) -> dict:
    return {
        "questions": int(len(df)),
        "answerable": int((~df.is_impossible).sum()),
        "unanswerable": int(df.is_impossible.sum()),
        "articles": int(df.title.nunique()),
        "paragraphs": int(df.paragraph_id.nunique()),
    }


def article_splits(train: pd.DataFrame, dev: pd.DataFrame, seed: int, n_gate_dev: int,
                   n_cal: int, n_test: int) -> dict[str, list[str]]:
    rng = random.Random(seed)
    tr_titles = sorted(train.title.unique())
    dv_titles = sorted(dev.title.unique())
    rng.shuffle(tr_titles)
    rng.shuffle(dv_titles)
    if n_cal + n_test != len(dv_titles):
        raise ValueError(f"cal+test={n_cal + n_test} must equal #dev articles={len(dv_titles)}")
    return {
        "gate-dev": sorted(tr_titles[:n_gate_dev]),
        "gate-train": sorted(tr_titles[n_gate_dev:]),
        "squad-cal": sorted(dv_titles[:n_cal]),
        "squad-test": sorted(dv_titles[n_cal:]),
    }


def build_manifest(cfg: dict, raw_dir: Path, manifest_path: Path) -> dict:
    paths = download_squad(raw_dir)
    train, dev = load_split(paths["train"]), load_split(paths["validation"])
    sq = cfg["squad"]
    splits = article_splits(train, dev, sq["split_seed"], sq["gate_dev_articles"], sq["cal_articles"], sq["test_articles"])
    # disjointness assertions
    sets = {k: set(v) for k, v in splits.items()}
    keys = list(sets)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            assert not sets[keys[i]] & sets[keys[j]], f"overlap {keys[i]} vs {keys[j]}"
    counts = {}
    for name, titles in splits.items():
        src = train if name.startswith("gate") else dev
        counts[name] = audit(src[src.title.isin(titles)])
    manifest = {
        "hf_dataset": sq["hf_dataset"],
        "revision": sq["revision"],
        "license": "CC BY-SA 4.0",
        "source_sha256": {k: sha256_file(v) for k, v in paths.items()},
        "audit": {"train": audit(train), "validation": audit(dev)},
        "split_seed": sq["split_seed"],
        "splits": splits,
        "split_counts": counts,
    }
    write_json(manifest_path, manifest)
    return manifest


# ---------------------------------------------------------------- answer normalization (official SQuAD)

def normalize_answer(s: str) -> str:
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def token_f1(pred: str, gold: str) -> float:
    p, g = normalize_answer(pred).split(), normalize_answer(gold).split()
    if not p or not g:
        return float(p == g)
    common = Counter(p) & Counter(g)
    same = sum(common.values())
    if same == 0:
        return 0.0
    prec, rec = same / len(p), same / len(g)
    return 2 * prec * rec / (prec + rec)


def auto_correct(answer_text: str, gold_answers: list[str], f1_threshold: float = 0.5) -> bool:
    """Automatic correctness for a *generated* answer to an answerable SQuAD question (ADR-008).

    Correct if the normalized answer contains any normalized gold string, or max token-F1 >= threshold.
    Audited against humans on a 100-item sample.
    """
    na = normalize_answer(answer_text)
    for g in gold_answers:
        ng = normalize_answer(g)
        if ng and ng in na:
            return True
    return max((token_f1(answer_text, g) for g in gold_answers), default=0.0) >= f1_threshold


# ---------------------------------------------------------------- SQuAD-RAG sets

def rag_items(df: pd.DataFrame, titles: list[str], n: int, seed: int, prefix: str) -> tuple[list[dict], list[dict]]:
    """Sample a stratified 1:1 answerable:unanswerable question set; corpus = all paragraphs of `titles`."""
    sub = df[df.title.isin(titles)]
    paras = sub.drop_duplicates("paragraph_id")[["paragraph_id", "title", "context"]]
    corpus = [{"chunk_id": f"sq_{r.paragraph_id}", "title": r.title, "text": r.context} for r in paras.itertuples()]
    rng = random.Random(seed)
    ans = sub[~sub.is_impossible].index.tolist()
    una = sub[sub.is_impossible].index.tolist()
    rng.shuffle(ans)
    rng.shuffle(una)
    k = min(n // 2, len(ans), len(una))
    chosen = sorted(ans[:k] + una[:k])
    items = []
    for idx in chosen:
        r = sub.loc[idx]
        items.append({
            "item_id": f"{prefix}-{r['id']}",
            "squad_id": r["id"],
            "question": r["question"],
            "title": r["title"],
            "gold_state": "insufficient" if r["is_impossible"] else "sufficient",
            "gold_chunk_ids": [f"sq_{r['paragraph_id']}"],
            "gold_answers": list(r["answer_texts"]),
            "split": prefix,
        })
    return items, corpus
