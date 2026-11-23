"""Section-aware chunking (spec C3).

Rules (frozen):
* a chunk never crosses a section (heading) boundary — chunking is done per Section;
* chunks are contiguous character spans of the section text, so ``chunk.text == section.text[start:end]``;
* units are sentences inside prose paragraphs; fenced code blocks and display-math blocks are atomic
  units (hard-split by lines only if a single unit exceeds the budget);
* greedy packing up to ``max_tokens`` with ~``overlap_tokens`` of trailing units repeated in the next chunk.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Callable

from .io_utils import sha256_text, stable_id
from .provenance import Chunk, Section

SENT_SPLIT_RE = re.compile(
    r"(?<!\be\.g)(?<!\bi\.e)(?<!\betc)(?<!\bvs)(?<!\bFig)(?<!\bEq)(?<!\bSec)(?<=[.!?])\s+(?=[A-Z$\\(\[*`])"
)


@dataclass
class Unit:
    start: int
    end: int
    kind: str  # sent | code | math


def _blocks(text: str) -> list[tuple[int, int, str]]:
    """Split section text into (start, end, kind) blocks: fenced code, $$ math, prose paragraphs."""
    blocks: list[tuple[int, int, str]] = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("```", i):
            j = text.find("\n```", i + 3)
            end = n if j == -1 else text.find("\n", j + 4)
            end = n if end == -1 else end
            blocks.append((i, end, "code"))
            i = end
        elif text.startswith("$$", i):
            j = text.find("$$", i + 2)
            end = n if j == -1 else j + 2
            blocks.append((i, end, "math"))
            i = end
        elif text[i] in "\n ":
            i += 1
        else:
            # prose until blank line, fence or display math
            j = i
            while j < n:
                if text.startswith("\n\n", j) or text.startswith("\n```", j) or text.startswith("$$", j):
                    break
                j += 1
            blocks.append((i, j, "prose"))
            i = j
    return blocks


def _units(text: str) -> list[Unit]:
    units: list[Unit] = []
    for s, e, kind in _blocks(text):
        if kind != "prose":
            units.append(Unit(s, e, kind))
            continue
        seg = text[s:e]
        pos = 0
        for m in SENT_SPLIT_RE.finditer(seg):
            if m.start() > pos:
                units.append(Unit(s + pos, s + m.start(), "sent"))
            pos = m.end()
        if pos < len(seg):
            units.append(Unit(s + pos, e, "sent"))
    return [u for u in units if text[u.start:u.end].strip()]


def _split_long(text: str, u: Unit, count: Callable[[str], int], max_tokens: int) -> list[Unit]:
    """Hard-split an over-budget unit by lines, then by fixed character windows."""
    pieces: list[Unit] = []
    seg = text[u.start:u.end]
    lines, pos = seg.split("\n"), 0
    cur_start, cur_len = 0, 0
    for k, line in enumerate(lines):
        ln = count(line) + 1
        if cur_len + ln > max_tokens and pos > cur_start:
            pieces.append(Unit(u.start + cur_start, u.start + pos - 1, u.kind))
            cur_start, cur_len = pos, 0
        cur_len += ln
        pos += len(line) + 1
    pieces.append(Unit(u.start + cur_start, u.end, u.kind))
    out: list[Unit] = []
    for p in pieces:
        if count(text[p.start:p.end]) <= max_tokens:
            out.append(p)
            continue
        width = max(200, int(len(text[p.start:p.end]) * max_tokens / max(1, count(text[p.start:p.end]))))
        for a in range(p.start, p.end, width):
            out.append(Unit(a, min(p.end, a + width), p.kind))
    return out


def chunk_section(
    section: Section,
    count_tokens: Callable[[str], int],
    max_tokens: int = 400,
    overlap_tokens: int = 50,
    min_tokens: int = 20,
) -> list[tuple[int, int]]:
    """Return list of (char_start, char_end) spans for one section."""
    text = section.text
    units: list[Unit] = []
    for u in _units(text):
        if count_tokens(text[u.start:u.end]) > max_tokens:
            units.extend(_split_long(text, u, count_tokens, max_tokens))
        else:
            units.append(u)
    if not units:
        return []
    toks = [count_tokens(text[u.start:u.end]) for u in units]
    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(units):
        j, total = i, 0
        while j < len(units) and (total + toks[j] <= max_tokens or j == i):
            total += toks[j]
            j += 1
        spans.append((units[i].start, units[j - 1].end))
        if j >= len(units):
            break
        # overlap: step back over trailing units totalling <= overlap_tokens (never back to i)
        k, ov = j, 0
        while k - 1 > i and ov + toks[k - 1] <= overlap_tokens:
            k -= 1
            ov += toks[k]
        i = k
    # merge a too-small trailing chunk into its predecessor when it fits
    if len(spans) >= 2:
        last = text[spans[-1][0]:spans[-1][1]]
        merged = text[spans[-2][0]:spans[-1][1]]
        if count_tokens(last) < min_tokens and count_tokens(merged) <= max_tokens:
            spans[-2:] = [(spans[-2][0], spans[-1][1])]
    return spans


def build_chunks(
    sections: list[Section],
    count_tokens: Callable[[str], int],
    cfg_corpus: dict,
    max_tokens: int = 400,
    overlap_tokens: int = 50,
    min_tokens: int = 20,
    extraction_tool: str = "learnmate.ingest.d2l_md@0.1.0",
    access_date: str | None = None,
) -> list[Chunk]:
    access_date = access_date or date.today().isoformat()
    chunks: list[Chunk] = []
    for sec in sections:
        for ordinal, (s, e) in enumerate(chunk_section(sec, count_tokens, max_tokens, overlap_tokens, min_tokens)):
            text = sec.text[s:e]
            if count_tokens(text) < 3:
                continue
            quality = "ok"
            chunks.append(Chunk(
                chunk_id="c_" + stable_id(sec.section_id, str(ordinal), str(s), str(e), n=12),
                doc_id=sec.doc_id,
                chapter=sec.chapter,
                title=sec.section_path[-1],
                section_path=list(sec.section_path),
                parent_section_id=sec.section_id,
                source_url=sec.source_url,
                commit_or_version=cfg_corpus.get("commit", "unknown"),
                license=cfg_corpus.get("license", "unknown"),
                attribution=cfg_corpus.get("attribution", ""),
                char_start=s,
                char_end=e,
                text=text,
                token_count=count_tokens(text),
                extraction_tool=extraction_tool,
                extraction_quality=quality,
                sha256=sha256_text(text),
                access_date=access_date,
                has_math=("$" in text),
                has_code=("```" in text),
            ))
    return chunks


def index_text(chunk: Chunk) -> str:
    """Text that is embedded / BM25-indexed: section path as a title line + chunk text."""
    return f"{chunk.display_path}\n{chunk.text}"
