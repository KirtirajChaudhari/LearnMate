"""Provenance store: the single source of truth for passage IDs and citation targets (spec C2).

Every citation the system displays must resolve to a Chunk held here.
"""
from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .io_utils import read_jsonl, sha256_text, write_jsonl


@dataclass
class Section:
    doc_id: str                 # e.g. "chapter_linear-regression/linear-regression"
    section_id: str             # stable hash
    section_path: list[str]     # ["Linear Neural Networks for Regression", "Linear Regression", "Basics"]
    chapter: str                # "chapter_linear-regression"
    text: str                   # normalized markdown text of this (sub)section body
    source_url: str
    label: str | None = None    # d2l :label: if any
    flags: list[str] = field(default_factory=list)  # e.g. ["code_stripped:mxnet", "math"]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    chapter: str
    title: str
    section_path: list[str]
    parent_section_id: str
    source_url: str
    commit_or_version: str
    license: str
    attribution: str
    char_start: int             # offsets into the parent section's normalized text
    char_end: int
    text: str
    token_count: int
    extraction_tool: str
    extraction_quality: str     # ok | math_loss | table_loss | failed
    sha256: str
    access_date: str
    page: int | None = None     # PDF sources only
    has_math: bool = False
    has_code: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def display_path(self) -> str:
        return " > ".join(self.section_path)


class ChunkStore:
    """In-memory chunk store backed by JSONL (canonical) and an optional SQLite mirror."""

    def __init__(self, chunks: list[Chunk]):
        self._chunks = chunks
        self._by_id: dict[str, Chunk] = {}
        for c in chunks:
            if c.chunk_id in self._by_id:
                raise ValueError(f"duplicate chunk_id {c.chunk_id}")
            if sha256_text(c.text) != c.sha256:
                raise ValueError(f"hash mismatch for chunk {c.chunk_id}")
            self._by_id[c.chunk_id] = c

    def __len__(self) -> int:
        return len(self._chunks)

    def __iter__(self):
        return iter(self._chunks)

    def __contains__(self, chunk_id: str) -> bool:
        return chunk_id in self._by_id

    def get(self, chunk_id: str) -> Chunk:
        return self._by_id[chunk_id]

    def ids(self) -> list[str]:
        return [c.chunk_id for c in self._chunks]

    @property
    def chunks(self) -> list[Chunk]:
        return self._chunks

    # ---- persistence -------------------------------------------------------------
    def save(self, path: str | Path, sqlite_path: str | Path | None = None) -> None:
        write_jsonl(path, (c.to_dict() for c in self._chunks))
        if sqlite_path is not None:
            sqlite_path = Path(sqlite_path)
            if sqlite_path.exists():
                sqlite_path.unlink()
            con = sqlite3.connect(sqlite_path)
            con.execute(
                "CREATE TABLE chunks (chunk_id TEXT PRIMARY KEY, doc_id TEXT, section_path TEXT,"
                " source_url TEXT, license TEXT, text TEXT, sha256 TEXT)"
            )
            con.executemany(
                "INSERT INTO chunks VALUES (?,?,?,?,?,?,?)",
                [(c.chunk_id, c.doc_id, " > ".join(c.section_path), c.source_url, c.license, c.text, c.sha256)
                 for c in self._chunks],
            )
            con.commit()
            con.close()

    @classmethod
    def load(cls, path: str | Path) -> "ChunkStore":
        return cls([Chunk(**r) for r in read_jsonl(path)])
