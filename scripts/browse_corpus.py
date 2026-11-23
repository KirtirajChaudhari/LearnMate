"""Annotator helper: BM25 search over the indexed course chunks (no LLM involved).

    python scripts/browse_corpus.py "forget gate" [-k 8] [--heldout]
    python scripts/browse_corpus.py --chunk c_657289ff451a
"""
import argparse
import textwrap

from rank_bm25 import BM25Okapi

from learnmate.chunking import index_text
from learnmate.config import load_config, repo_path
from learnmate.index import bm25_tokenize
from learnmate.io_utils import read_jsonl
from learnmate.provenance import ChunkStore


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("-k", type=int, default=8)
    ap.add_argument("--chunk")
    ap.add_argument("--heldout", action="store_true", help="search held-out (out-of-syllabus) sections instead")
    a = ap.parse_args()
    cfg = load_config()
    proc = repo_path(cfg["paths"]["processed"])
    if a.heldout:
        secs = read_jsonl(proc / "sections_heldout.jsonl")
        docs = [(s["section_id"], " > ".join(s["section_path"]), s["text"]) for s in secs]
    else:
        store = ChunkStore.load(proc / "chunks.jsonl")
        if a.chunk:
            c = store.get(a.chunk)
            print(c.display_path, "|", c.source_url, f"| chars {c.char_start}-{c.char_end}\n")
            print(c.text)
            return
        docs = [(c.chunk_id, c.display_path, c.text) for c in store]
    bm = BM25Okapi([bm25_tokenize(p + " " + t) for _, p, t in docs])
    scores = bm.get_scores(bm25_tokenize(a.query))
    for i in sorted(range(len(docs)), key=lambda i: -scores[i])[: a.k]:
        cid, path, text = docs[i]
        print(f"[{scores[i]:.1f}] {cid} | {path}")
        print(textwrap.indent(textwrap.shorten(text, 300), "    "))


if __name__ == "__main__":
    main()
