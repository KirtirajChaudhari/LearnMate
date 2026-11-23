"""M0 smoke test: load every model once (sequentially), run one forward pass, record latency + peak VRAM.

    python scripts/smoke_models.py                 # GPU (Colab): all models incl. generator fp16 then nf4
    python scripts/smoke_models.py --skip-generator  # CPU: everything except the 4B HF generator
Writes results/m0_smoke.json. Used to decide the frozen generator runtime (fp16 vs nf4).
"""
import argparse
import gc
import time

from learnmate.config import load_config
from learnmate.io_utils import env_fingerprint, write_json


def peak():
    import torch
    return round(torch.cuda.max_memory_allocated() / 1e9, 3) if torch.cuda.is_available() else None


def reset():
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()


def timed(name, fn, out):
    reset()
    t = time.perf_counter()
    try:
        info = fn() or {}
        out[name] = {"ok": True, "seconds": round(time.perf_counter() - t, 2), "peak_vram_gb": peak(), **info}
    except Exception as e:  # record failures honestly
        out[name] = {"ok": False, "error": repr(e)[:500]}
    print(name, out[name], flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-generator", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    m = cfg["models"]
    out = {"env": env_fingerprint()}

    def embed():
        from learnmate.index import Embedder
        e = Embedder(m["embedder"]["id"], m["embedder"]["revision"], m["embedder"]["query_prefix"])
        return {"dim": int(e.encode_queries(["what is dropout?"]).shape[1])}

    def rerank():
        from learnmate.retrieve import CrossEncoderReranker
        r = CrossEncoderReranker(m["reranker"]["id"], m["reranker"]["revision"])
        return {"logit": float(r.score("what is dropout?", ["Dropout zeroes activations at random."])[0])}

    def gate_base():
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import torch
        tok = AutoTokenizer.from_pretrained(m["gate_base"]["id"], revision=m["gate_base"]["revision"])
        mod = AutoModelForSequenceClassification.from_pretrained(m["gate_base"]["id"], revision=m["gate_base"]["revision"], num_labels=2)
        with torch.no_grad():
            mod(**tok("q", "p", return_tensors="pt"))
        return {}

    def minicheck():
        from learnmate.verify import MiniCheckFT5
        p = MiniCheckFT5(m["minicheck"]["id"], m["minicheck"]["revision"]).score_pairs(
            ["Dropout zeroes hidden units at random during training."], ["Dropout randomly zeroes hidden units."])
        return {"p_support": float(p[0])}

    def nli():
        from learnmate.verify import NLIModel
        n = NLIModel(m["nli"]["id"], m["nli"]["revision"])
        return {"p_contra": float(n.contradiction(["The learning rate is 0.1."], ["The learning rate is 0.5."])[0])}

    def b0():
        from learnmate.gate.model import SquadNoAnswerGate
        g = SquadNoAnswerGate(m["extractive_b0"]["id"], m["extractive_b0"]["revision"])
        return g.answer("What does dropout zero out?", "Dropout zeroes out hidden units at random during training.")

    def generator(dtype):
        def f():
            from learnmate.generate import HFGenerator
            from learnmate.prompts import build_messages
            g = HFGenerator(m["generator"]["id"], m["generator"]["revision"], dtype, 64)
            r = g(build_messages("What does dropout do?", [{"chunk_id": "x", "text": "Dropout zeroes hidden units at random during training.", "section_path_str": "Dropout"}]))
            return {"text": r["text"][:200], "latency_s": round(r["latency_s"], 2), "new_tokens": r["new_tokens"]}
        return f

    for name, fn in [("embedder", embed), ("reranker", rerank), ("gate_base", gate_base), ("minicheck", minicheck),
                     ("nli", nli), ("b0_extractive", b0)]:
        timed(name, fn, out)
    if not a.skip_generator:
        import torch
        if torch.cuda.is_available():
            timed("generator_fp16", generator("float16"), out)
            timed("generator_nf4", generator("nf4"), out)
        else:
            out["generator"] = {"ok": False, "error": "no CUDA: run on Colab/Kaggle GPU"}
    write_json("results/m0_smoke.json", out)


if __name__ == "__main__":
    main()
