"""UI smoke test with a mocked pipeline (no models): every rendered citation must resolve to a passage."""
import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")


def fake_result(state="sufficient"):
    answered = state in ("sufficient", "partial")
    return {
        "question": "What does the forget gate do?", "system": "G",
        "passages": [{"chunk_id": "c1", "text": "The forget gate decides whether to keep or flush memory.",
                      "section_path_str": "LSTM > Gates"}],
        "retrieved": [{"chunk_id": "c1"}], "raw_answer": "It decides to keep or flush memory [C1].",
        "sentences": [{"text": "It decides to keep or flush memory.", "citations": ["c1"], "support": 0.95}],
        "features": {"gate_max": 0.9}, "timings": {"total": 0.1},
        "decision": {"state": state, "answered": answered, "p_safe": 0.9, "tau": 0.5, "reason": "test",
                     "message": "msg", "related_ids": [] if answered else ["c1"], "contradiction_ids": [],
                     "displayed_sentences": [{"text": "It decides to keep or flush memory.", "citations": ["c1"],
                                              "support": 0.95}] if answered else []},
    }


STATE = {"value": "sufficient"}


class FakeLM:
    store = None

    def answer(self, q, system):
        return fake_result(STATE["value"])


def _script():
    import app.streamlit_app as m
    import tests.test_app_smoke as t
    m.get_pipeline = lambda: t.FakeLM()
    m.append_jsonl = lambda *a, **k: None
    m.main()


@pytest.mark.parametrize("state", ["sufficient", "partial", "insufficient", "contradictory", "system_error"])
def test_app_renders_each_state(state):
    STATE["value"] = state
    at = st_testing.AppTest.from_function(_script, default_timeout=30)
    at.run()
    assert not at.exception
    at.chat_input[0].set_value("What does the forget gate do?").run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    if state in ("sufficient", "partial"):
        assert "<sup>[1]</sup>" in text  # citation chip rendered and resolvable to passage 1
    else:
        assert len(at.warning) >= 1  # abstention message shown
