"""Grounded-generation prompt P_v1 (frozen at pre-registration; hashed into every cache key)."""
from __future__ import annotations

from .citations import INSUFFICIENT_TOKEN
from .io_utils import sha256_text

PROMPT_VERSION = "P_v1"

SYSTEM_PROMPT = f"""You are LearnMate, a course tutor. You answer ONLY from the numbered course passages provided.

Rules:
1. Use only information stated in the passages. Do not use outside knowledge, even if you know the answer.
2. End every sentence that states a fact with the marker(s) of the passage(s) that support it, e.g. [C2] or [C1][C3].
3. If the passages do not contain enough information to answer the question, reply with exactly:
{INSUFFICIENT_TOKEN}
4. If the passages answer only part of the question, answer that part with citations and say which part the course passages do not cover.
5. Be concise: at most 5 sentences. Keep mathematical notation as in the passages."""

EXAMPLE_USER = """Passages:
[C1] (Optimization Algorithms > Momentum) Momentum replaces the gradient with a leaky average of past gradients, which accelerates convergence along directions with consistent gradients.
[C2] (Optimization Algorithms > Adagrad) Adagrad divides the learning rate per coordinate by the square root of the accumulated squared gradients.

Question: What does momentum replace the gradient with?"""

EXAMPLE_ASSISTANT = "Momentum replaces the gradient with a leaky average of past gradients [C1]. This accelerates convergence along directions where the gradients are consistent [C1]."


def render_passages(passages: list[dict]) -> str:
    lines = []
    for k, p in enumerate(passages, start=1):
        path = p.get("section_path_str") or ""
        head = f"[C{k}] ({path}) " if path else f"[C{k}] "
        lines.append(head + p["text"].strip())
    return "\n".join(lines)


def build_messages(question: str, passages: list[dict]) -> list[dict]:
    user = f"Passages:\n{render_passages(passages)}\n\nQuestion: {question.strip()}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": EXAMPLE_USER},
        {"role": "assistant", "content": EXAMPLE_ASSISTANT},
        {"role": "user", "content": user},
    ]


def prompt_hash() -> str:
    return sha256_text(PROMPT_VERSION + SYSTEM_PROMPT + EXAMPLE_USER + EXAMPLE_ASSISTANT)[:12]
