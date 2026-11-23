from eval.labels import error_label
from learnmate.squad import auto_correct, normalize_answer, token_f1


def test_squad_normalization_and_autocorrect():
    assert normalize_answer("The Normans!") == "normans"
    assert auto_correct("They were the Normans from France [C1].", ["Normans"])
    assert not auto_correct("They were Vikings.", ["Normans"])
    assert abs(token_f1("in the 10th century", "10th century") - 0.8) < 1e-12  # official SQuAD F1
    assert token_f1("10th century", "the 10th century") == 1.0


def test_error_labels_squad():
    base = {"item_id": "x", "gold_answers": ["Normans"], "hyb_raw": "The Normans [C1].", "hyb_llm_insufficient": False}
    assert error_label({**base, "gold_state": "sufficient"}, "hyb") == 0
    assert error_label({**base, "gold_state": "insufficient", "gold_answers": []}, "hyb") == 1
    assert error_label({**base, "gold_state": "insufficient", "hyb_llm_insufficient": True}, "hyb") == 0
