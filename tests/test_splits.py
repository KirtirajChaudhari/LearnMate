"""Leakage checks on the real manifests (skipped if data not yet built)."""
from pathlib import Path

import pytest

from learnmate.io_utils import read_json, read_jsonl

ROOT = Path(__file__).resolve().parents[1]
MAN = ROOT / "data" / "manifests" / "squad_splits.json"


@pytest.mark.skipif(not MAN.exists(), reason="run scripts/build_squad.py first")
def test_squad_partitions_disjoint_and_counts():
    m = read_json(MAN)
    s = {k: set(v) for k, v in m["splits"].items()}
    keys = list(s)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            assert not s[keys[i]] & s[keys[j]]
    assert m["audit"]["train"] == {"questions": 130319, "answerable": 86821, "unanswerable": 43498,
                                   "articles": 442, "paragraphs": 19029}
    assert m["audit"]["validation"]["articles"] == 35
    assert len(s["squad-cal"]) + len(s["squad-test"]) == 35


@pytest.mark.skipif(not (ROOT / "data/processed/squad_rag/squad-cal_items.jsonl").exists(), reason="no squad-rag")
def test_squad_rag_items_use_only_their_partition():
    m = read_json(MAN)
    for split in ("squad-cal", "squad-test"):
        items = read_jsonl(ROOT / f"data/processed/squad_rag/{split}_items.jsonl")
        corpus_ids = {r["chunk_id"] for r in read_jsonl(ROOT / f"data/processed/squad_rag/{split}_corpus.jsonl")}
        assert all(i["title"] in set(m["splits"][split]) for i in items)
        assert all(set(i["gold_chunk_ids"]) <= corpus_ids for i in items)


COURSE = ROOT / "data" / "annotations" / "course_items.jsonl"


@pytest.mark.skipif(not COURSE.exists(), reason="course items not yet authored")
def test_course_items_section_disjoint():
    from learnmate.annotation import validate_items
    problems = validate_items(read_jsonl(COURSE), check_store=False)
    # verification status is a workflow state (checked at freeze); schema and leakage rules must hold at all times
    errors = [p for p in problems if p["severity"] == "error" and "not human-verified" not in p["msg"]]
    assert not errors, errors[:5]
