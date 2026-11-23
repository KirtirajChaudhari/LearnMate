"""Build hybrid indices for the course corpus and the SQuAD-RAG corpora.

    python scripts/build_indices.py [--rebuild] [--only course]
"""
import argparse
import time

from learnmate.config import load_config
from learnmate.resources import build_or_load_index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--only", nargs="*", default=["course", "squad-cal", "squad-test"])
    a = ap.parse_args()
    cfg = load_config()
    for name in a.only:
        t = time.perf_counter()
        idx = build_or_load_index(name, cfg, rebuild=a.rebuild)
        print(f"{name}: {len(idx.ids)} passages, dim={idx.vectors.shape[1]}, {time.perf_counter()-t:.1f}s")


if __name__ == "__main__":
    main()
