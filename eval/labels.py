"""Error labels per (item, answer set) — protocol §4.

answer sets: "hyb" (shared by B2 and G and all ablations) and "b1".
error = 1 if, *were the answer shown*, it would be an error:
  * gold_state == insufficient  -> any substantive answer is an error;
  * course items                -> human verdict in {incorrect, unsupported} (+ partially_correct when strict);
  * squad answerable items      -> not auto_correct(answer, gold_answers)   [ADR-008, audited on 100 items].
If the LLM itself output INSUFFICIENT_EVIDENCE the system abstains regardless (can_answer = False); the error
label is then irrelevant for coverage but is kept (= 0 for insufficient items, 1 for answerable ones) so that
AURC treats it like any other abstention placed last.
"""
from __future__ import annotations

from learnmate.citations import MARKER_RE
from learnmate.io_utils import read_jsonl
from learnmate.squad import auto_correct

ERROR_VERDICTS_STRICT = {"incorrect", "unsupported", "partially_correct"}
ERROR_VERDICTS_LENIENT = {"incorrect", "unsupported"}


def load_judgments(path) -> dict[tuple[str, str], dict]:
    """Judgments file rows: {item_id, answer_set: hyb|b1, condition, verdict, sentence_labels, judge}."""
    out = {}
    for r in read_jsonl(path):
        out[(r["item_id"], r.get("answer_set", "hyb"), r.get("condition", "clean"))] = r
    return out


def error_label(rec: dict, answer_set: str, condition: str = "clean", judgments: dict | None = None,
                strict: bool = True) -> int | None:
    llm_ins = rec[f"{answer_set}_llm_insufficient"]
    gold = rec.get("gold_state")
    if gold == "insufficient":
        return 0 if llm_ins else 1
    if llm_ins:
        return 1  # abstained on an answerable item: counts as error only if it were 'answered' (never is)
    if rec.get("gold_answers") is not None:  # SQuAD auto-label
        raw = rec[f"{answer_set}_raw"] or ""
        return 0 if auto_correct(MARKER_RE.sub("", raw), rec["gold_answers"]) else 1
    if judgments is None:
        return None
    j = judgments.get((rec["item_id"], answer_set, condition))
    if j is None:
        return None
    bad = ERROR_VERDICTS_STRICT if strict else ERROR_VERDICTS_LENIENT
    return 1 if j["verdict"] in bad else 0


def s1_error_label(rec: dict, answer_set: str, judgments: dict | None) -> int | None:
    """Under S1 (gold withheld) the correct behaviour is abstention unless a human confirms that another
    retrieved passage genuinely supports a correct answer (verdict correct_supported)."""
    if rec[f"{answer_set}_llm_insufficient"]:
        return 0
    if judgments is not None:
        j = judgments.get((rec["item_id"], answer_set, "S1"))
        if j is not None and j["verdict"] == "correct_supported":
            return 0
    return 1
