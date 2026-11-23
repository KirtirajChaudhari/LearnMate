import random

from learnmate.citations import INSUFFICIENT_TOKEN, citation_coverage, parse_answer, validate_resolvable

IDS = ["c1", "c2", "c3", "c4", "c5"]


def test_basic_and_invalid_markers():
    ins, s = parse_answer("A is true [C1]. B holds [C2][C3]. C is false [C9].", IDS)
    assert not ins
    assert [x.citations for x in s] == [["c1"], ["c2", "c3"], []]
    assert s[2].status == "invalid_citation" and s[2].invalid_markers == ["C9"]
    assert all("[C" not in x.text for x in s)


def test_comma_markers_and_math():
    _, s = parse_answer("The loss is $a. b$ here [C1, C4]. Next, e.g. this [C2].", IDS)
    assert s[0].citations == ["c1", "c4"] and "$a. b$" in s[0].text
    assert len(s) == 2


def test_insufficient_token():
    assert parse_answer(INSUFFICIENT_TOKEN, IDS) == (True, [])
    assert parse_answer("   ", IDS) == (True, [])


def test_paragraph_trailing_block():
    _, s = parse_answer("First claim. Second claim. Third claim. [C1][C3]", IDS)
    assert all(x.citations == ["c1", "c3"] for x in s)
    assert [x.status for x in s] == ["cited_paragraph", "cited_paragraph", "cited"]
    assert citation_coverage(s) == 1.0


def test_no_propagation_when_other_sentences_cited():
    _, s = parse_answer("First claim [C2]. Second claim. Third claim. [C1]", IDS)
    assert s[1].citations == []


def test_property_every_citation_resolves():
    rng = random.Random(0)
    for _ in range(300):
        parts = []
        for _ in range(rng.randint(1, 5)):
            marks = "".join(f"[C{rng.randint(-1, 9)}]" for _ in range(rng.randint(0, 3)))
            parts.append(f"Claim {rng.randint(0, 99)} {marks}.")
        _, sents = parse_answer(" ".join(parts), IDS)
        sents = validate_resolvable(sents, set(IDS).__contains__)
        for x in sents:
            assert all(c in IDS for c in x.citations)


def test_verbal_abstention_detected():
    for t in ["The passages do not state what X is. Instead, they describe Y [C1].",
              "The provided passages do not contain information about GANs.",
              "This question cannot be answered from the passages.",
              "There is not enough information in the passages to answer."]:
        assert parse_answer(t, IDS)[0], t


def test_verbal_abstention_not_overtriggered():
    for t in ["The passages describe dropout as a regularizer [C1].",
              "Dropout does not change the expected value of activations [C2].",
              "The model does not use the passages directly; it uses attention [C3]."]:
        assert not parse_answer(t, IDS)[0], t
