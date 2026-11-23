"""Trained sufficiency gate: inference wrapper and aggregation over retrieved passages (spec C6)."""
from __future__ import annotations

import numpy as np


class GateScorer:
    def __init__(self, model_dir: str, device: str | None = None, max_length: int = 384, batch_size: int = 16):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(self.device)
        self.model.eval()
        self.max_length, self.batch_size = max_length, batch_size

    def score(self, questions: list[str], passages: list[str]) -> np.ndarray:
        """P(sufficient) for each (question, passage) pair (label index 1)."""
        import torch

        out = []
        for a in range(0, len(questions), self.batch_size):
            enc = self.tok(questions[a:a + self.batch_size], passages[a:a + self.batch_size], truncation="only_second",
                           max_length=self.max_length, padding=True, return_tensors="pt").to(self.device)
            with torch.no_grad():
                out.append(torch.softmax(self.model(**enc).logits.float(), dim=-1)[:, 1].cpu().numpy())
        return np.concatenate(out) if out else np.zeros(0, dtype="float32")


def aggregate(probs: list[float] | np.ndarray) -> dict[str, float]:
    """gate_max and gate_top2 (mean of the two highest) over the reranked top-k passages."""
    p = sorted((float(x) for x in probs), reverse=True)
    if not p:
        return {"gate_max": 0.0, "gate_top2": 0.0}
    return {"gate_max": p[0], "gate_top2": float(np.mean(p[:2]))}


class SquadNoAnswerGate:
    """Ablation A5 (untrained gate): 1 - P(no-answer) from an off-the-shelf SQuAD 2.0 extractive model.

    P(no-answer) is taken from the [CLS] start/end logits relative to the best non-null span score.
    """

    def __init__(self, model_id: str = "deepset/deberta-v3-base-squad2", revision: str | None = None,
                 device: str | None = None, max_length: int = 384):
        import torch
        from transformers import AutoModelForQuestionAnswering, AutoTokenizer

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
        self.model = AutoModelForQuestionAnswering.from_pretrained(model_id, revision=revision).to(self.device)
        self.model.eval()
        self.max_length = max_length

    def answer(self, question: str, passage: str, max_answer_len: int = 30) -> dict:
        import torch

        enc = self.tok(question, passage, truncation="only_second", max_length=self.max_length,
                       return_offsets_mapping=True, return_tensors="pt")
        offsets = enc.pop("offset_mapping")[0].tolist()
        seq_ids = enc.sequence_ids(0)
        with torch.no_grad():
            out = self.model(**{k: v.to(self.device) for k, v in enc.items()})
        s, e = out.start_logits[0].float().cpu().numpy(), out.end_logits[0].float().cpu().numpy()
        null = float(s[0] + e[0])
        ctx = [i for i, sid in enumerate(seq_ids) if sid == 1]
        best, span = -1e9, (0, 0)
        top_s = sorted(ctx, key=lambda i: -s[i])[:20]
        top_e = sorted(ctx, key=lambda i: -e[i])[:20]
        for i in top_s:
            for j in top_e:
                if i <= j < i + max_answer_len and s[i] + e[j] > best:
                    best, span = float(s[i] + e[j]), (i, j)
        text = passage[offsets[span[0]][0]:offsets[span[1]][1]] if best > -1e9 else ""
        p_answer = float(1.0 / (1.0 + np.exp(-(best - null))))  # logistic of span-vs-null margin
        return {"text": text, "margin": best - null, "p_answer": p_answer}
