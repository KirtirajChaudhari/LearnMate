"""Sentence splitting and citation validation (spec C9, invariant: every displayed citation resolves).

The generator sees passages labelled [C1]..[Ck]. Each factual sentence should end with one or more
markers such as ``[C2]`` or ``[C1][C3]`` or ``[C1, C3]``. This module:
  * splits the answer into sentences while protecting inline math ``$..$``, code spans and common abbreviations;
  * parses markers per sentence, maps them to the chunk_ids of the passages actually shown;
  * strips invalid markers (index outside 1..k) and records each sentence's status.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

INSUFFICIENT_TOKEN = "INSUFFICIENT_EVIDENCE"

MARKER_RE = re.compile(r"\[\s*C\s*\d+(?:\s*[,;]\s*C?\s*\d+)*\s*\]", re.I)
NUM_RE = re.compile(r"\d+")
ABBREV = ("e.g.", "i.e.", "etc.", "vs.", "Fig.", "Eq.", "Sec.", "cf.", "approx.", "resp.", "w.r.t.")


@dataclass
class Sentence:
    idx: int
    text: str                      # sentence text with markers removed
    raw: str                       # as generated
    cited_indices: list[int]       # 1-based passage indices that were valid
    citations: list[str]           # chunk_ids
    invalid_markers: list[str] = field(default_factory=list)
    status: str = "uncited"        # cited | uncited | invalid_citation
    support: float | None = None   # filled by verifier
    sp_contra: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _protect(text: str) -> tuple[str, dict[str, str]]:
    repl: dict[str, str] = {}

    def sub(m: re.Match) -> str:
        key = f"\x00{len(repl)}\x00"
        repl[key] = m.group(0)
        return key

    text = re.sub(r"\$\$.*?\$\$|\$[^$]+\$|`[^`]+`", sub, text, flags=re.S)
    for ab in ABBREV:
        text = text.replace(ab, ab.replace(".", "\x01"))
    return text, repl


def _restore(text: str, repl: dict[str, str]) -> str:
    for k, v in repl.items():
        text = text.replace(k, v)
    return text.replace("\x01", ".")


def split_sentences(text: str) -> list[str]:
    """Split answer text into sentences; citation markers stay attached to the sentence they follow."""
    return [s for _, s in split_sentences_with_paragraphs(text)]


def split_sentences_with_paragraphs(text: str) -> list[tuple[int, str]]:
    """Like split_sentences but returns (paragraph_index, sentence)."""
    prot, repl = _protect(text.strip())
    parts: list[tuple[int, str]] = []
    for b_idx, block in enumerate( re.split(r"\n\s*\n|\n(?=\s*[-*•]\s)|\n(?=\s*\d+[.)]\s)", prot)):
        block = block.strip()
        if not block:
            continue
        # cut after sentence-final punctuation *and* any trailing citation markers
        pos = 0
        for m in re.finditer(r"[.!?](?:\s*\[\s*C[^\]]*\])*(?=\s+[A-Z0-9$\\(\[*`\x00]|\s*$)", block):
            seg = block[pos:m.end()].strip()
            if seg:
                parts.append((b_idx, seg))
            pos = m.end()
        tail = block[pos:].strip()
        if tail:
            parts.append((b_idx, tail))
    return [(b, _restore(p, repl)) for b, p in parts if _restore(p, repl).strip()]


TRAILING_BLOCK_RE = re.compile(r"[.!?]\s*((?:\[\s*C[^\]]*\]\s*)+)$")


def parse_answer(raw_answer: str, shown_chunk_ids: list[str]) -> tuple[bool, list[Sentence]]:
    """Return (is_insufficient, sentences). ``shown_chunk_ids[k-1]`` is the passage labelled [Ck]."""
    text = raw_answer.strip()
    if text.startswith(INSUFFICIENT_TOKEN) or text == "" or (
            INSUFFICIENT_TOKEN in text and len(MARKER_RE.findall(text)) == 0 and len(text) < 120):
        return True, []
    k = len(shown_chunk_ids)
    sentences: list[Sentence] = []
    paras = split_sentences_with_paragraphs(text)
    para_of: list[int] = []
    for i, (b_idx, s) in enumerate(paras):
        valid: list[int] = []
        invalid: list[str] = []
        for m in MARKER_RE.finditer(s):
            for num in NUM_RE.findall(m.group(0)):
                n = int(num)
                if 1 <= n <= k:
                    if n not in valid:
                        valid.append(n)
                else:
                    invalid.append(f"C{n}")
        clean = MARKER_RE.sub("", s)
        clean = re.sub(r"\s+([.,;:!?])", r"\1", clean)
        clean = re.sub(r"\s{2,}", " ", clean).strip()
        if not clean:
            continue
        status = "cited" if valid else ("invalid_citation" if invalid else "uncited")
        sentences.append(Sentence(idx=len(sentences), text=clean, raw=s, cited_indices=valid,
                                  citations=[shown_chunk_ids[n - 1] for n in valid],
                                  invalid_markers=invalid, status=status))
        para_of.append(b_idx)
    _propagate_trailing_blocks(sentences, para_of, shown_chunk_ids)
    if not sentences:
        return True, []
    return False, sentences


def _propagate_trailing_blocks(sentences: list[Sentence], para_of: list[int], shown_chunk_ids: list[str]) -> None:
    """Paragraph-level citation block: if, within a paragraph of >= 2 sentences, only the LAST sentence carries
    markers and they follow its final punctuation (``... text. [C1][C3]``), apply them to the paragraph's
    uncited sentences (status ``cited_paragraph``). Each sentence is still verified individually."""
    for b in sorted(set(para_of)):
        members = [s for s, p in zip(sentences, para_of) if p == b]
        if len(members) < 2:
            continue
        last = members[-1]
        if not last.cited_indices or any(m.cited_indices or m.invalid_markers for m in members[:-1]):
            continue
        if not TRAILING_BLOCK_RE.search(last.raw.strip()):
            continue
        for m in members[:-1]:
            m.cited_indices = list(last.cited_indices)
            m.citations = [shown_chunk_ids[n - 1] for n in last.cited_indices]
            m.status = "cited_paragraph"


def validate_resolvable(sentences: list[Sentence], store_contains) -> list[Sentence]:
    """Final invariant check against the provenance store: drop any citation that does not resolve."""
    for s in sentences:
        ok = [c for c in s.citations if store_contains(c)]
        if len(ok) != len(s.citations):
            s.invalid_markers.extend([c for c in s.citations if c not in ok])
            s.citations = ok
            s.cited_indices = s.cited_indices[: len(ok)]
            s.status = (s.status if s.status in ("cited", "cited_paragraph") else "cited") if ok else "invalid_citation"
    return sentences


def format_compliance(sentences: list[Sentence]) -> float:
    """Fraction of sentences carrying at least one valid citation (logged per answer)."""
    return sum(s.status == "cited" for s in sentences) / len(sentences) if sentences else 0.0


def citation_coverage(sentences: list[Sentence]) -> float:
    """Fraction of sentences with any valid citation (incl. paragraph-level blocks)."""
    return sum(bool(s.citations) for s in sentences) / len(sentences) if sentences else 0.0
