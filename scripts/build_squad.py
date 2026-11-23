"""Download SQuAD 2.0, write article-level split manifest and SQuAD-RAG item/corpus files.

    python scripts/build_squad.py
"""
from learnmate.config import load_config, repo_path
from learnmate.io_utils import write_jsonl, write_json
from learnmate import squad


def main():
    cfg = load_config()
    raw = repo_path(cfg["paths"]["raw"]) / "squad_v2"
    man = squad.build_manifest(cfg, raw, repo_path(cfg["paths"]["manifests"]) / "squad_splits.json")
    print("audit:", man["audit"])
    print("split counts:", man["split_counts"])
    dev = squad.load_split(raw / "validation.parquet")
    out = repo_path(cfg["paths"]["processed"]) / "squad_rag"
    nn = cfg["squad"]["rag_sample_per_split"]
    summary = {}
    for name in ("squad-cal", "squad-test"):
        n = nn[name] if isinstance(nn, dict) else nn
        items, corpus = squad.rag_items(dev, man["splits"][name], n, cfg["squad"]["split_seed"], name)
        write_jsonl(out / f"{name}_items.jsonl", items)
        write_jsonl(out / f"{name}_corpus.jsonl", corpus)
        summary[name] = {"items": len(items), "answerable": sum(i["gold_state"] == "sufficient" for i in items),
                         "corpus_paragraphs": len(corpus)}
    write_json(repo_path(cfg["paths"]["manifests"]) / "squad_rag_manifest.json", summary)
    print("squad-rag:", summary)


if __name__ == "__main__":
    main()
