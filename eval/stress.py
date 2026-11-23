"""Stress conditions S1-S4 (dataset plan §6). Applied identically to B1, B2 and G on paired items.

S1 withheld gold   : gold chunk IDs excluded from BM25 and FAISS before retrieval
S2 distractors     : the two lowest-ranked non-gold passages in the top-5 are replaced by the highest-ranked
                     non-gold, non-top-5 candidates (most confusable distractors)
S3 misleading edit : a gold passage's text is replaced by an edited copy (data/annotations/stress_edits.jsonl)
S4 contradiction   : the original gold passage is kept AND the edited copy is inserted (replacing rank 5)
"""
from __future__ import annotations

from dataclasses import replace

from learnmate.retrieve import Retrieved

CONDITIONS = ("clean", "S1", "S2", "S3", "S4")
EDIT_SUFFIX = "#edit"


def exclude_ids(condition: str, item: dict) -> set[str]:
    return set(item.get("gold_chunk_ids", [])) if condition == "S1" else set()


def apply_post_retrieval(condition: str, item: dict, top: list[Retrieved], cands: list[Retrieved],
                         edits: dict[str, dict]) -> list[Retrieved]:
    gold = set(item.get("gold_chunk_ids", []))
    top = [replace(r) for r in top]
    if condition == "S2":
        top_ids = {r.chunk_id for r in top}
        pool = [c for c in sorted(cands, key=lambda c: -(c.ce_logit if c.ce_logit is not None else c.rrf_score))
                if c.chunk_id not in top_ids and c.chunk_id not in gold]
        slots = [i for i in range(len(top) - 1, -1, -1) if top[i].chunk_id not in gold][:2]
        for slot, d in zip(slots, pool):
            top[slot] = replace(d, extra={**d.extra, "stress": "S2_distractor"})
        return top
    if condition in ("S3", "S4"):
        e = edits.get(item["item_id"])
        if not e:
            return top
        cid, edited = e["chunk_id"], e["edited_text"]
        if condition == "S3":
            for i, r in enumerate(top):
                if r.chunk_id == cid:
                    top[i] = replace(r, text=edited, extra={**r.extra, "stress": "S3_edited"})
            return top
        # S4: keep original, add edited copy (if the original was retrieved)
        if any(r.chunk_id == cid for r in top):
            copy = Retrieved(cid + EDIT_SUFFIX, edited, extra={"stress": "S4_edited_copy", "source": cid})
            pos = next(i for i, r in enumerate(top) if r.chunk_id == cid)
            insert_at = min(pos + 1, len(top) - 1)
            top = top[:insert_at] + [copy] + top[insert_at:]
            top = top[: len(top) - 1] if len(top) > 5 else top
        return top
    return top
