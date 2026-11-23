"""CPU smoke test of retrieval + generation + citation parsing on hand-picked questions.
NOT an evaluation: questions are ad-hoc and the llama.cpp backend is the CPU demo runtime."""
import sys, time
from learnmate.config import load_config, repo_path
from learnmate.resources import retriever_for
from learnmate.provenance import ChunkStore
from learnmate.generate import GenerationCache, generate_cached, generator_from_cfg
from learnmate.citations import parse_answer, validate_resolvable, format_compliance
from learnmate.pipeline import passage_dicts
from learnmate.io_utils import write_json

cfg = load_config()
store = ChunkStore.load(repo_path(cfg["paths"]["processed"]) / "chunks.jsonl")
ret = retriever_for("course", cfg)
gen = generator_from_cfg(cfg, backend="llamacpp")
cache = GenerationCache(repo_path("results/smoke/generations_smoke.jsonl"))
qs = sys.argv[1:] or [
    "Why does dropout help reduce overfitting?",
    "What is the purpose of the forget gate in an LSTM?",
    "How does a generative adversarial network train its discriminator?",  # held-out chapter -> should abstain
]
out = []
for q in qs:
    t = time.perf_counter()
    top, _ = ret.hybrid(q)
    ps = passage_dicts(top, store)
    g = generate_cached(gen, cache, q, ps, cfg["generation"]["max_new_tokens"])
    ins, sents = parse_answer(g["text"], [p["chunk_id"] for p in ps])
    sents = validate_resolvable(sents, store.__contains__)
    rec = {"question": q, "top": [(p["chunk_id"], p["section_path_str"], round(r.ce_prob, 3)) for p, r in zip(ps, top)],
           "raw": g["text"], "insufficient": ins, "n_sentences": len(sents),
           "format_compliance": format_compliance(sents), "latency_s": round(g["latency_s"], 1),
           "total_s": round(time.perf_counter() - t, 1)}
    out.append(rec)
    print("=" * 100); print("Q:", q)
    for c in rec["top"]: print("   ", c)
    print("A:", g["text"]); print("insufficient:", ins, "| sentences:", len(sents), "| compliance:", rec["format_compliance"], "| gen s:", rec["latency_s"])
write_json(repo_path("results/smoke/generation_smoke.json"), {"backend": gen.tag, "note": "CPU smoke only", "records": out})
