"""LearnMate Streamlit demo (spec C12). The UI is a demonstration, not an evaluation (handbook §2).

    streamlit run app/streamlit_app.py
    LEARNMATE_BACKEND=llamacpp streamlit run app/streamlit_app.py      # CPU demo runtime

Shows: state badge, answer with clickable verified citations, the stored passage with provenance,
"related, not supporting" sections on abstention, a B1 / B2 / LearnMate toggle, and per-query logging.
"""
from __future__ import annotations

import html
import json
import os
import sys
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from learnmate.config import load_config, repo_path  # noqa: E402
from learnmate.io_utils import append_jsonl  # noqa: E402

STATE_STYLE = {
    "sufficient": ("✅ Answered from course material", "#1a7f37"),
    "partial": ("◐ Partly covered by course material", "#9a6700"),
    "insufficient": ("⛔ Not answerable from course material", "#cf222e"),
    "contradictory": ("⚠️ Course passages disagree", "#bc4c00"),
    "system_error": ("⛔ Could not verify — not answering", "#6e7781"),
}
SYSTEMS = {"LearnMate (gate + verifier)": "G", "B2: reranker-score threshold": "B2", "B1: prompt-only": "B1"}

st.set_page_config(page_title="LearnMate", page_icon="📘", layout="wide")


@st.cache_resource(show_spinner="Loading models (first run only)…")
def get_pipeline():
    from learnmate.pipeline import LearnMate
    cfg = load_config()
    return LearnMate(cfg, corpus="course",
                     gate_dir=os.environ.get("LEARNMATE_GATE", str(repo_path("models/gate-v1/best"))),
                     frozen_path=os.environ.get("LEARNMATE_FROZEN", str(repo_path("configs/frozen/thresholds.json"))),
                     backend=os.environ.get("LEARNMATE_BACKEND"))


def render_passage(p: dict, store, label: str, supporting: bool | None = None):
    c = store.get(p["chunk_id"].split("#")[0]) if store is not None and p["chunk_id"].split("#")[0] in store else None
    tag = "" if supporting is None else (" — supports the answer" if supporting else " — related, not verified as supporting")
    with st.expander(f"{label} · {p.get('section_path_str', '')}{tag}"):
        st.markdown(p["text"])
        if c is not None:
            st.caption(f"Source: [{c.source_url}]({c.source_url}) · chunk `{c.chunk_id}` · chars {c.char_start}–{c.char_end} "
                       f"· commit `{c.commit_or_version[:10]}` · {c.license} · {c.attribution}")


def main():
    cfg = load_config()
    st.title("📘 LearnMate")
    st.caption("An evidence-grounded course tutor: it answers **only** from the course text, cites the passages, "
               "and says so when the course material doesn't cover a question. "
               f"Course corpus: *{cfg['corpus']['attribution']}* — {cfg['corpus']['status']}.")
    with st.sidebar:
        sys_label = st.radio("System", list(SYSTEMS), index=0)
        show_debug = st.toggle("Show decision details", value=False)
        st.markdown("---")
        st.markdown("**States**")
        for k, (lab, col) in STATE_STYLE.items():
            st.markdown(f"<span style='color:{col}'>{lab}</span>", unsafe_allow_html=True)
        gallery = repo_path("results/demo_gallery.jsonl")
        if gallery.exists():
            st.markdown("---\n**Recorded failure cases (from real runs)**")
            for line in gallery.read_text().splitlines()[:8]:
                g = json.loads(line)
                st.caption(f"• {g['question']} → {g['state']} ({g['note']})")

    q = st.chat_input("Ask a question about the course…")
    if "history" not in st.session_state:
        st.session_state.history = []
    if q:
        lm = get_pipeline()
        res = lm.answer(q, SYSTEMS[sys_label])
        st.session_state.history.append(res)
        append_jsonl(repo_path("results/app_logs/queries.jsonl"),
                     {"ts": time.time(), "question": q, "system": res["system"], "state": res["decision"]["state"],
                      "p_safe": res["decision"].get("p_safe"), "retrieved": [r["chunk_id"] for r in res["retrieved"]],
                      "timings": res["timings"]})

    store = None
    if st.session_state.history:
        store = get_pipeline().store
    for res in reversed(st.session_state.history):
        d = res["decision"]
        lab, col = STATE_STYLE[d["state"]]
        with st.chat_message("user"):
            st.write(res["question"])
        with st.chat_message("assistant"):
            st.markdown(f"<div style='border-left:4px solid {col};padding-left:8px'><b style='color:{col}'>{lab}</b>"
                        f" <small>· {res['system']}</small></div>", unsafe_allow_html=True)
            by_id = {p["chunk_id"]: (k, p) for k, p in enumerate(res["passages"], start=1)}
            if d["answered"]:
                parts = []
                for s in d["displayed_sentences"]:
                    cites = " ".join(f"<sup>[{by_id[c][0]}]</sup>" for c in s.get("citations", []) if c in by_id)
                    parts.append(html.escape(s["text"]) + " " + cites)
                st.markdown(" ".join(parts), unsafe_allow_html=True)
                if d["state"] == "partial":
                    st.info(d["message"])
                shown = {c for s in d["displayed_sentences"] for c in s.get("citations", [])}
                for cid in sorted(shown, key=lambda c: by_id[c][0] if c in by_id else 99):
                    if cid in by_id:
                        render_passage(by_id[cid][1], store, f"[{by_id[cid][0]}]", supporting=True)
            else:
                st.warning(d["message"])
                ids = d.get("contradiction_ids") or d.get("related_ids") or []
                for cid in ids:
                    if cid in by_id:
                        render_passage(by_id[cid][1], store, f"[{by_id[cid][0]}]", supporting=False)
            if show_debug:
                st.json({"reason": d["reason"], "p_safe": d.get("p_safe"), "tau": d.get("tau"),
                         "features": res.get("features"), "timings_s": res.get("timings"),
                         "raw_answer": res.get("raw_answer")})


if __name__ == "__main__":
    main()
