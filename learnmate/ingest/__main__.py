"""Build the provenance-tagged chunk store from the pinned d2l checkout.

    python -m learnmate.ingest [--config configs/base.yaml] [--check]
"""
from __future__ import annotations

import argparse
import subprocess
from collections import Counter

from ..chunking import build_chunks
from ..config import load_config, repo_path
from ..io_utils import sha256_file, write_json, write_jsonl
from ..provenance import ChunkStore
from ..tokenize_utils import token_counter
from .d2l_md import parse_d2l


def git_head(path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--check", action="store_true", help="print audit stats and exit non-zero on violations")
    args = ap.parse_args()
    cfg = load_config(args.config)
    cc = cfg["corpus"]
    repo = repo_path(cc["local_dir"])
    head = git_head(repo)
    if head != cc["commit"]:
        raise SystemExit(f"d2l checkout at {head}, config pins {cc['commit']}: run `git -C {repo} checkout {cc['commit']}`")

    count = token_counter(cfg["chunking"]["tokenizer"])
    out_dir = repo_path(cfg["paths"]["processed"])
    for split_name, chapters in (("indexed", cc["indexed_chapters"]), ("heldout", cc["heldout_chapters"])):
        sections = parse_d2l(repo, chapters, cc["code_framework"], cc["web_base"])
        write_jsonl(out_dir / f"sections_{split_name}.jsonl", (s.to_dict() for s in sections))
        if split_name == "heldout":
            print(f"[heldout] {len(sections)} sections (NOT indexed; source for out-of-syllabus items)")
            continue
        ch = cfg["chunking"]
        chunks = build_chunks(sections, count, cc, ch["max_tokens"], ch["overlap_tokens"], ch["min_tokens"],
                              access_date=cc.get("access_date"))
        store = ChunkStore(chunks)
        store.save(out_dir / "chunks.jsonl", out_dir / "chunks.sqlite")
        by_ch = Counter(c.chapter for c in chunks)
        stats = {
            "commit": head,
            "n_sections": len(sections),
            "n_chunks": len(chunks),
            "max_tokens": max(c.token_count for c in chunks),
            "mean_tokens": round(sum(c.token_count for c in chunks) / len(chunks), 1),
            "chunks_with_math": sum(c.has_math for c in chunks),
            "chunks_with_code": sum(c.has_code for c in chunks),
            "per_chapter": dict(sorted(by_ch.items())),
            "chunks_sha256": sha256_file(out_dir / "chunks.jsonl"),
        }
        write_json(repo_path(cfg["paths"]["manifests"]) / "corpus_manifest.json", stats)
        print({k: v for k, v in stats.items() if k != "per_chapter"})
        if args.check:
            bad = [c.chunk_id for c in chunks if c.token_count > ch["max_tokens"]]
            # spans must reproduce text from their parent section
            sec_by_id = {s.section_id: s for s in sections}
            mism = [c.chunk_id for c in chunks if sec_by_id[c.parent_section_id].text[c.char_start:c.char_end] != c.text]
            if bad or mism:
                raise SystemExit(f"violations: over_budget={len(bad)} span_mismatch={len(mism)}")
            print("check OK: no over-budget chunks, all spans reproduce section text, no cross-section chunks")


if __name__ == "__main__":
    main()
