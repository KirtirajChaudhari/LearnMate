"""Gate training data (spec C6): SQuAD 2.0 pairs + retrieval hard negatives.

label 1 (sufficient): (answerable question, its gold paragraph)
label 0 (insufficient):
  * squad_neg : (unanswerable question, its paragraph)            -- adversarial, paragraph-local
  * hard_neg  : (answerable question, a top-BM25 non-gold paragraph from the same pool that contains
                 none of the gold answer strings)                  -- "retrieved != sufficient"
Hard negatives are mined only within the split's own article pool (no leakage across partitions).
"""
from __future__ import annotations

import random

import pandas as pd

from ..index import bm25_tokenize
from ..squad import normalize_answer


def mine_hard_negatives(df: pd.DataFrame, n_needed: int, seed: int, top_k: int = 10) -> list[dict]:
    from rank_bm25 import BM25Okapi

    paras = df.drop_duplicates("paragraph_id")[["paragraph_id", "title", "context"]].reset_index(drop=True)
    bm25 = BM25Okapi([bm25_tokenize(t + " " + c) for t, c in zip(paras.title, paras.context)])
    norm_ctx = [normalize_answer(c) for c in paras.context]
    rng = random.Random(seed)
    ans = df[~df.is_impossible]
    order = list(ans.index)
    rng.shuffle(order)
    out = []
    import numpy as np
    for idx in order:
        if len(out) >= n_needed:
            break
        r = ans.loc[idx]
        golds = [normalize_answer(a) for a in r.answer_texts if normalize_answer(a)]
        scores = bm25.get_scores(bm25_tokenize(r.question))
        for j in np.argsort(-scores)[:top_k]:
            if paras.paragraph_id[j] == r.paragraph_id:
                continue
            if any(g in norm_ctx[j] for g in golds):
                continue  # would not be a true negative
            out.append({"question": r.question, "passage": paras.context[j], "label": 0, "kind": "hard_neg",
                        "qid": r.id, "pid": paras.paragraph_id[j], "title": r.title})
            break
    return out


def build_pairs(df: pd.DataFrame, n_total: int, mix: dict, seed: int) -> list[dict]:
    rng = random.Random(seed)
    n_pos = int(n_total * mix["positive"])
    n_sq = int(n_total * mix["squad_negative"])
    n_hn = n_total - n_pos - n_sq
    pos = df[~df.is_impossible].sample(n=min(n_pos, int((~df.is_impossible).sum())), random_state=seed)
    neg = df[df.is_impossible].sample(n=min(n_sq, int(df.is_impossible.sum())), random_state=seed)
    rows = [{"question": r.question, "passage": r.context, "label": 1, "kind": "positive", "qid": r.id,
             "pid": r.paragraph_id, "title": r.title} for r in pos.itertuples()]
    rows += [{"question": r.question, "passage": r.context, "label": 0, "kind": "squad_neg", "qid": r.id,
              "pid": r.paragraph_id, "title": r.title} for r in neg.itertuples()]
    if n_hn > 0:
        rows += mine_hard_negatives(df, n_hn, seed)
    rng.shuffle(rows)
    return rows
