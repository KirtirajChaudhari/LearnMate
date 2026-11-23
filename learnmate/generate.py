"""Grounded generation backends + deterministic JSONL cache (spec C7, ADR-003/009).

Backends
  * ``hf``       : HF transformers, fp16 (GPU) / nf4 (bitsandbytes) / float32 (CPU). Evaluation runtime.
  * ``llamacpp`` : llama-cpp-python GGUF (CPU demo only; never mixed with evaluation results).
Decoding is greedy. Every output is cached under a key that includes model revision, prompt hash and
passage IDs, so re-runs are exact and resumable across Colab disconnects.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .io_utils import append_jsonl, read_jsonl, sha256_text
from .prompts import build_messages, prompt_hash


class GenerationCache:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._d: dict[str, dict] = {}
        if self.path.exists():
            for r in read_jsonl(self.path):
                self._d[r["key"]] = r

    @staticmethod
    def make_key(model_tag: str, question: str, passage_ids: list[str], max_new_tokens: int) -> str:
        return sha256_text(json.dumps([model_tag, prompt_hash(), question, passage_ids, max_new_tokens]))[:24]

    def get(self, key: str) -> dict | None:
        return self._d.get(key)

    def put(self, row: dict) -> None:
        self._d[row["key"]] = row
        append_jsonl(self.path, row)


class HFGenerator:
    def __init__(self, model_id: str, revision: str | None = None, dtype: str = "float16",
                 max_new_tokens: int = 320, max_input_tokens: int = 3072):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tag = f"hf:{model_id}@{(revision or 'main')[:10]}:{dtype}"
        self.tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
        kw: dict = {"revision": revision}
        if dtype == "nf4":
            from transformers import BitsAndBytesConfig
            kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                           bnb_4bit_compute_dtype=torch.float16)
            kw["device_map"] = "auto"
        elif dtype == "float16":
            kw["torch_dtype"] = torch.float16
            kw["device_map"] = "auto"
        elif dtype == "bfloat16":
            kw["torch_dtype"] = torch.bfloat16
        else:
            kw["torch_dtype"] = torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(model_id, **kw)
        self.model.eval()
        self.max_new_tokens = max_new_tokens
        self.max_input_tokens = max_input_tokens

    def __call__(self, messages: list[dict]) -> dict:
        import torch
        ids = self.tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
        if ids.shape[1] > self.max_input_tokens:
            raise ValueError(f"prompt too long: {ids.shape[1]} tokens > {self.max_input_tokens}")
        ids = ids.to(self.model.device)
        t = time.perf_counter()
        with torch.no_grad():
            out = self.model.generate(ids, attention_mask=torch.ones_like(ids), max_new_tokens=self.max_new_tokens,
                                      do_sample=False, temperature=None, top_p=None, top_k=None,
                                      pad_token_id=self.tok.eos_token_id)
        text = self.tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
        return {"text": text.strip(), "latency_s": time.perf_counter() - t, "prompt_tokens": int(ids.shape[1]),
                "new_tokens": int(out.shape[1] - ids.shape[1])}


class LlamaCppGenerator:
    """CPU demo backend (GGUF Q4_K_M). Not used for any reported evaluation number."""

    def __init__(self, gguf_path: str, n_ctx: int = 4096, max_new_tokens: int = 320, n_threads: int | None = None):
        from llama_cpp import Llama
        self.llm = Llama(model_path=gguf_path, n_ctx=n_ctx, n_threads=n_threads, seed=0, verbose=False)
        self.tag = f"llamacpp:{Path(gguf_path).name}"
        self.max_new_tokens = max_new_tokens

    def __call__(self, messages: list[dict]) -> dict:
        t = time.perf_counter()
        r = self.llm.create_chat_completion(messages=messages, temperature=0.0, top_k=1, max_tokens=self.max_new_tokens)
        return {"text": r["choices"][0]["message"]["content"].strip(), "latency_s": time.perf_counter() - t,
                "prompt_tokens": r["usage"]["prompt_tokens"], "new_tokens": r["usage"]["completion_tokens"]}


def generate_cached(gen, cache: GenerationCache, question: str, passages: list[dict], max_new_tokens: int) -> dict:
    """Generate (or fetch) an answer. ``passages`` are dicts with chunk_id/text/section_path_str."""
    pids = [p["chunk_id"] for p in passages]
    key = GenerationCache.make_key(gen.tag, question, pids, max_new_tokens)
    hit = cache.get(key)
    if hit is not None:
        return hit
    res = gen(build_messages(question, passages))
    if "<think>" in res["text"]:
        res["think_stripped"] = True
        res["text"] = res["text"].split("</think>")[-1].strip()
    row = {"key": key, "model": gen.tag, "prompt_hash": prompt_hash(), "question": question,
           "passage_ids": pids, **res}
    cache.put(row)
    return row


def generator_from_cfg(cfg: dict, backend: str | None = None, gguf_path: str | None = None):
    g = cfg["generation"]
    backend = backend or g["backend"]
    if backend == "llamacpp":
        if gguf_path is None:
            from huggingface_hub import hf_hub_download
            m = cfg["models"]["generator_gguf"]
            gguf_path = hf_hub_download(m["repo"], m["file"], revision=m["revision"])
        return LlamaCppGenerator(gguf_path, max_new_tokens=g["max_new_tokens"])
    m = cfg["models"]["generator"]
    return HFGenerator(m["id"], m["revision"], g["dtype"], g["max_new_tokens"], g["max_input_tokens"])
