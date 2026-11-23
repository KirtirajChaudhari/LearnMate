"""Claim-level verification (spec C8): support (MiniCheck) + contradiction (3-class NLI).

``MiniCheckFT5`` re-implements the inference path of MiniCheck-Flan-T5-Large from the official repository
(https://github.com/Liyan06/MiniCheck, Apache-2.0, commit b58b9fa; Tang, Laban & Durrett, EMNLP 2024):
input ``"predict: " + doc + "</s>" + claim``, a single decoder step from token 0, and
P(supported) = softmax(logits[[3, 209]])[1]; documents longer than ``chunk_words`` are split on sentence
boundaries and the max over chunks is taken. Re-implemented (rather than pip-installed) to avoid the
package's unpinned openai/vllm dependency chain; parity with the official package is checked in
``tests/test_verify_models.py`` when it is installed.
"""
from __future__ import annotations

import re

import numpy as np

from .citations import Sentence


def _sent_split(text: str) -> list[str]:
    out = []
    for block in text.split("\n"):
        out.extend(s for s in re.split(r"(?<=[.!?])\s+", block) if s.strip())
    return out or [""]


class MiniCheckFT5:
    SUPPORT_TOKENS = (3, 209)  # (unsupported, supported) per the official implementation

    def __init__(self, model_id: str = "lytang/MiniCheck-Flan-T5-Large", revision: str | None = None,
                 device: str | None = None, max_len: int = 2048, chunk_words: int = 500, batch_size: int = 8,
                 dtype: str = "float32"):
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
        td = torch.float16 if (dtype == "float16" and self.device == "cuda") else torch.float32
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_id, revision=revision, torch_dtype=td).to(self.device)
        self.model.eval()
        self.max_len, self.chunk_words, self.batch_size = max_len, chunk_words, batch_size

    def _chunks(self, doc: str) -> list[str]:
        sents, chunks, cur, n = _sent_split(doc), [], [], 0
        for s in sents:
            w = len(s.split())
            if n + w > self.chunk_words and cur:
                chunks.append(" ".join(cur))
                cur, n = [s], w
            else:
                cur.append(s)
                n += w
        if cur:
            chunks.append(" ".join(cur))
        return [c.strip() for c in chunks if c.strip()] or [""]

    def score_pairs(self, docs: list[str], claims: list[str]) -> np.ndarray:
        """P(supported) for each (doc, claim) pair, max over doc chunks."""
        import torch

        flat, owner = [], []
        for i, (d, c) in enumerate(zip(docs, claims)):
            for ch in self._chunks(d):
                flat.append("predict: " + ch + self.tok.eos_token + c)
                owner.append(i)
        probs = np.zeros(len(flat), dtype="float32")
        for a in range(0, len(flat), self.batch_size):
            enc = self.tok(flat[a:a + self.batch_size], max_length=self.max_len, truncation=True, padding=True,
                           return_tensors="pt").to(self.device)
            dec = torch.zeros((enc["input_ids"].shape[0], 1), dtype=torch.long, device=self.device)
            with torch.no_grad():
                logits = self.model(input_ids=enc["input_ids"], attention_mask=enc["attention_mask"],
                                    decoder_input_ids=dec).logits[:, 0, :]
            two = logits[:, list(self.SUPPORT_TOKENS)].float()
            probs[a:a + self.batch_size] = torch.softmax(two, dim=-1)[:, 1].cpu().numpy()
        out = np.zeros(len(docs), dtype="float32")
        for p, i in zip(probs, owner):
            out[i] = max(out[i], p)
        return out


class NLIModel:
    """3-class NLI (entailment / neutral / contradiction)."""

    def __init__(self, model_id: str = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli", revision: str | None = None,
                 device: str | None = None, max_len: int = 512, batch_size: int = 16):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_id, revision=revision).to(self.device)
        self.model.eval()
        id2label = {int(k): v.lower() for k, v in self.model.config.id2label.items()}
        self.contra_idx = next(i for i, l in id2label.items() if l.startswith("contra"))
        self.entail_idx = next(i for i, l in id2label.items() if l.startswith("entail"))
        self.max_len, self.batch_size = max_len, batch_size

    def probs(self, premises: list[str], hypotheses: list[str]) -> np.ndarray:
        import torch

        out = []
        for a in range(0, len(premises), self.batch_size):
            enc = self.tok(premises[a:a + self.batch_size], hypotheses[a:a + self.batch_size], truncation="only_first",
                           max_length=self.max_len, padding=True, return_tensors="pt").to(self.device)
            with torch.no_grad():
                out.append(torch.softmax(self.model(**enc).logits.float(), dim=-1).cpu().numpy())
        return np.concatenate(out) if out else np.zeros((0, 3), dtype="float32")

    def contradiction(self, premises: list[str], hypotheses: list[str]) -> np.ndarray:
        p = self.probs(premises, hypotheses)
        return p[:, self.contra_idx] if len(p) else np.zeros(0, dtype="float32")


def passage_contradiction(nli: NLIModel, passages: list[str], top: int = 3) -> float:
    """pp_contra: max P(contradiction) over ordered pairs among the top passages (both directions)."""
    ps = passages[:top]
    prem, hyp = [], []
    for i in range(len(ps)):
        for j in range(len(ps)):
            if i != j:
                prem.append(ps[i])
                hyp.append(ps[j])
    if not prem:
        return 0.0
    return float(nli.contradiction(prem, hyp).max())


class Verifier:
    def __init__(self, minicheck: MiniCheckFT5, nli: NLIModel, support_threshold: float = 0.5, contra_top: int = 3):
        self.mc, self.nli = minicheck, nli
        self.s_min, self.contra_top = support_threshold, contra_top

    def verify(self, sentences: list[Sentence], passage_text: dict[str, str], ranked_ids: list[str]) -> dict:
        """Fill per-sentence support / contradiction and return fusion features (spec C8)."""
        docs, claims, owners = [], [], []
        for s in sentences:
            for cid in s.citations:
                docs.append(passage_text[cid])
                claims.append(s.text)
                owners.append(s.idx)
        sup = self.mc.score_pairs(docs, claims) if docs else np.zeros(0)
        con = self.nli.contradiction(docs, claims) if docs else np.zeros(0)
        best_sup = {s.idx: 0.0 for s in sentences}
        best_con = {s.idx: 0.0 for s in sentences}
        for o, sp, cp in zip(owners, sup, con):
            best_sup[o] = max(best_sup[o], float(sp))
            best_con[o] = max(best_con[o], float(cp))
        for s in sentences:  # uncited / invalid -> support 0 (spec C8)
            s.support = best_sup[s.idx] if s.citations else 0.0
            s.sp_contra = best_con[s.idx] if s.citations else 0.0
        pp = passage_contradiction(self.nli, [passage_text[c] for c in ranked_ids], self.contra_top)
        conflict = self.claim_conflict(sentences, [passage_text[c] for c in ranked_ids[: self.contra_top]])
        feats = features_from_sentences(sentences, pp, self.s_min)
        feats["claim_conflict"] = conflict
        return feats

    def claim_conflict(self, sentences: list[Sentence], passages: list[str]) -> float:
        """max over sentences s and passage pairs i != j of min(support(s, p_i), P_contra(p_j -> s)).

        High only when one top passage supports a claim while another contradicts it (evidence disagreement
        on the claim itself), unlike whole-passage NLI which fires on merely different passages."""
        if not sentences or len(passages) < 2:
            return 0.0
        docs, claims, own = [], [], []
        for s in sentences:
            for j, p in enumerate(passages):
                docs.append(p); claims.append(s.text); own.append((s.idx, j))
        sup = self.mc.score_pairs(docs, claims)
        con = self.nli.contradiction(docs, claims)
        S, C = {}, {}
        for (si, j), a, b in zip(own, sup, con):
            S[(si, j)], C[(si, j)] = float(a), float(b)
        best = 0.0
        for s in sentences:
            for i in range(len(passages)):
                for j in range(len(passages)):
                    if i != j:
                        best = max(best, min(S[(s.idx, i)], C[(s.idx, j)]))
        return best


def features_from_sentences(sentences: list[Sentence], pp_contra: float, s_min: float = 0.5) -> dict:
    if not sentences:
        return {"sup_min": 0.0, "sup_mean": 0.0, "frac_supported": 0.0, "pp_contra": float(pp_contra),
                "sp_contra": 0.0, "uncited_frac": 1.0, "claim_conflict": 0.0}
    sup = [s.support or 0.0 for s in sentences]
    return {
        "sup_min": float(min(sup)),
        "sup_mean": float(sum(sup) / len(sup)),
        "frac_supported": float(sum(x >= s_min for x in sup) / len(sup)),
        "pp_contra": float(pp_contra),
        "sp_contra": float(max(s.sp_contra or 0.0 for s in sentences)),
        "uncited_frac": float(sum(not s.citations for s in sentences) / len(sentences)),
    }
