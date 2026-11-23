"""Token counting with the embedder's tokenizer (chunk budgets are in embedder tokens)."""
from __future__ import annotations

from functools import lru_cache
from typing import Callable


@lru_cache(maxsize=4)
def _tok(name: str):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(name)


def token_counter(name: str) -> Callable[[str], int]:
    tok = _tok(name)

    def count(text: str) -> int:
        return len(tok(text, add_special_tokens=False, truncation=False)["input_ids"])

    return count
