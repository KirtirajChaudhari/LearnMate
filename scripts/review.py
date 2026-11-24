#!/usr/bin/env python3
"""Fast terminal tools for the two annotators. Standard library only: just `git pull` and run.

    python scripts/review.py verify       --member A     # confirm/reject/edit the items assigned to you
    python scripts/review.py second-label --member A     # blind label of the OTHER member's items
    python scripts/review.py judge --sheet data/annotations/judge_test.jsonl --member A
    python scripts/review.py status

Progress is saved after every answer; quit with q and resume any time.
Each member writes ONLY their own files (decisions_X / labels_X / verdicts_X .jsonl), so git never conflicts.
After `git pull`, run `python scripts/review.py apply` to merge everyone's work into course_items.jsonl.
Needs data/processed/chunks.jsonl (committed to the repo) and data/annotations/course_items.jsonl.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import textwrap
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "data/annotations/course_items.jsonl"
CHUNKS = ROOT / "data/processed/chunks.jsonl"
HELDOUT = ROOT / "data/processed/sections_heldout.jsonl"

TOK = re.compile(r"\\[a-zA-Z]+|[a-zA-Z]+|\d+")
STOP = set("a an the of to in on for and or is are was were be been by with as at from that this these those it its "
           "which we our you your can will would should could may might not no do does did has have had than then "
           "there their what when where who how why if so such into about over".split())


def load(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def save(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(tmp, path)


ANN = ROOT / "data/annotations"


def overlay(items: list[dict]) -> list[dict]:
    """Apply per-member decision/label files on top of course_items.jsonl (so two people never edit the same file)."""
    by = {i["item_id"]: i for i in items}
    for f in sorted(ANN.glob("decisions_*.jsonl")):
        for r in load(f):
            if r["item_id"] in by:
                by[r["item_id"]].update(r["patch"])
    for f in sorted(ANN.glob("labels_*.jsonl")):
        for r in load(f):
            if r["item_id"] in by:
                by[r["item_id"]]["label_b"] = r["label_b"]
    return items


def load_items() -> list[dict]:
    return overlay(load(ITEMS))


def save_member(kind: str, member: str, store: dict) -> None:
    """kind: decisions | labels. store maps item_id -> patch / label_b."""
    key = "patch" if kind == "decisions" else "label_b"
    save(ANN / f"{kind}_{member}.jsonl", [{"item_id": k, key: v} for k, v in sorted(store.items())])


def load_member(kind: str, member: str) -> dict:
    f = ANN / f"{kind}_{member}.jsonl"
    key = "patch" if kind == "decisions" else "label_b"
    return {r["item_id"]: r[key] for r in load(f)} if f.exists() else {}


def toks(t: str) -> list[str]:
    return [w.lower() for w in TOK.findall(t) if w.lower() not in STOP]


class BM25:
    def __init__(self, docs: list[str], k1=1.5, b=0.75):
        self.docs = [toks(d) for d in docs]
        self.k1, self.b = k1, b
        self.avg = sum(map(len, self.docs)) / max(1, len(self.docs))
        df = Counter(w for d in self.docs for w in set(d))
        n = len(self.docs)
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}
        self.tf = [Counter(d) for d in self.docs]

    def top(self, q: str, k: int) -> list[int]:
        qt = toks(q)
        sc = []
        for i, tf in enumerate(self.tf):
            L = len(self.docs[i])
            s = sum(self.idf.get(w, 0) * tf[w] * (self.k1 + 1) / (tf[w] + self.k1 * (1 - self.b + self.b * L / self.avg))
                    for w in qt if w in tf)
            sc.append(s)
        return sorted(range(len(sc)), key=lambda i: -sc[i])[:k]


def ask(prompt: str, choices: str) -> str:
    while True:
        try:
            a = input(prompt).strip().lower()
        except EOFError:
            return "q"
        if a and a[0] in choices:
            return a[0]
        print("   choose one of:", "/".join(choices))


def short(t: str, n: int) -> str:
    t = t.strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def show_chunk(c: dict, n=900, label=""):
    print(f"   {label}[{c['chunk_id']}] {' > '.join(c['section_path'])}")
    print(textwrap.indent(short(c["text"], n), "      "))


def cmd_verify(a):
    items = load_items()
    mine = load_member("decisions", a.member)
    chunks = {c["chunk_id"]: c for c in load(CHUNKS)}
    bm = BM25([" ".join(c["section_path"]) + " " + c["text"] for c in chunks.values()])
    cl = list(chunks.values())
    todo = [i for i in items if i.get("author") == a.member and not i.get("human_verified") and i.get("status") != "rejected"]
    print(f"{len(todo)} items to verify for member {a.member}. Check each against the course text, not against your memory.")
    for n, it in enumerate(todo, 1):
        print("\n" + "=" * 100)
        print(f"({n}/{len(todo)}) {it['item_id']}  category {it['category']}  gold_state={it['gold_state']}  math={it.get('has_math')}")
        print("Q:", it["question"])
        print("Reference answer:", it["reference_answer"])
        if it.get("uncovered_claims"):
            print("NOT covered by the course (must be absent from the text):", it["uncovered_claims"])
        for cid in it.get("gold_chunk_ids", []):
            show_chunk(chunks[cid], label="GOLD ")
        if it["gold_state"] != "sufficient":
            print("   -- closest course passages found by search (confirm they do NOT answer it):")
            for i in bm.top(it["question"] + " " + " ".join(it.get("uncovered_claims", [])), 3):
                show_chunk(cl[i], 450, label="NEAR ")
        if it["category"] == "U2":
            print("   Out-of-syllabus item: topic comes from held-out chapter:", it.get("section_path"))
        k = ask("\n[a]ccept  [r]eject  [e]dit text  [s]kip  [q]uit > ", "arseq")
        if k == "q":
            break
        if k == "s":
            continue
        if k == "r":
            mine[it["item_id"]] = {"status": "rejected", "verified_by": a.member}
        elif k == "e":
            q = input("  new question (enter = keep): ").strip()
            ra = input("  new reference answer (enter = keep): ").strip()
            mine[it["item_id"]] = {"question": q or it["question"], "reference_answer": ra or it["reference_answer"],
                                   "edited_by_human": True, "human_verified": True, "verified_by": a.member}
        else:
            mine[it["item_id"]] = {"human_verified": True, "verified_by": a.member}
        save_member("decisions", a.member, mine)
    print(f"\nSaved to data/annotations/decisions_{a.member}.jsonl. Commit and push THAT file (not course_items.jsonl).")
    cmd_status(a)


def cmd_second_label(a):
    items = load_items()
    mine = load_member("labels", a.member)
    chunks = load(CHUNKS)
    bm = BM25([" ".join(c["section_path"]) + " " + c["text"] for c in chunks])
    todo = [i for i in items if i.get("author") != a.member and i.get("human_verified") and i.get("status") != "rejected"
            and not i.get("label_b")]
    print(f"{len(todo)} items to label blind (you do NOT see the other member's labels).\n"
          "For each question, read the candidate passages and decide whether the INDEXED course text answers it.\n"
          "Many questions are NOT answered by the course text (they ask for a fact or a topic that is absent): "
          "answer n for those. Keys here differ from `verify`: y / p / n / q.")
    streak = []
    for n, it in enumerate(todo, 1):
        print("\n" + "=" * 100)
        print(f"({n}/{len(todo)}) {it['item_id']}\nQ: {it['question']}\n")
        cand = bm.top(it["question"], 6)
        for j, i in enumerate(cand, 1):
            show_chunk(chunks[i], 650, label=f"#{j} ")
        s = ask("\nDo the passages above ANSWER this question?\n"
                "  [y] yes, fully   [p] only part of it   [n] no / not covered by these passages   [q] quit > ", "ypnq")
        if s == "q":
            break
        gold: list[str] = []
        if s in "yp":
            while True:
                raw = input("  which passage numbers contain the answer (e.g. 1,3)? (0 = none -> then it should be 'n') : ").strip()
                for tkn in re.split(r"[,\s]+", raw):
                    if tkn.isdigit() and 1 <= int(tkn) <= len(cand):
                        gold.append(chunks[cand[int(tkn) - 1]]["chunk_id"])
                    elif tkn.startswith("c_"):
                        gold.append(tkn)
                if gold:
                    break
                if raw.strip() == "0":
                    print("  you said no passage contains the answer: switching this label to 'n'")
                    s = "n"
                    break
        state = {"y": "sufficient", "p": "partial", "n": "insufficient"}[s]
        print(f"  -> recorded: {state.upper()}")
        mine[it["item_id"]] = {"gold_state": state, "gold_chunk_ids": gold, "annotator": a.member}
        save_member("labels", a.member, mine)
        streak.append(s)
        if len(streak) >= 8 and len(set(streak[-8:])) == 1:
            print(f"\n  !! You have given '{streak[-1]}' 8 times in a row. Check that each passage really answers its question; "
                  "about 40% of these questions are NOT answered by the course text.")
    print(f"\nSaved to data/annotations/labels_{a.member}.jsonl. Commit and push THAT file.")
    cmd_status(a)


VERDICTS = {"c": "correct_supported", "p": "partially_correct", "i": "incorrect", "u": "unsupported"}


def cmd_judge(a):
    sheet_path = Path(a.sheet)
    rows = load(sheet_path)
    vfile = sheet_path.parent / f"verdicts_{a.member}.jsonl"
    done = {r["output_id"]: r for r in load(vfile)} if vfile.exists() else {}
    todo = [r for r in rows if r["output_id"] not in done and r.get("assigned_judge") in (None, a.member)]
    print(f"{len(todo)} outputs to judge. You cannot see which system wrote each answer.\n"
          "  c = correct AND every claim is supported by the shown passages\n"
          "  p = correct but incomplete, or contains a minor detail the passages don't support\n"
          "  i = wrong / contradicts the reference\n"
          "  u = claims not in the shown passages (even if true in the real world), or it answers a question the course does not cover")
    for n, r in enumerate(todo, 1):
        print("\n" + "=" * 100)
        print(f"({n}/{len(todo)}) {r['output_id']}   course covers the question: {r.get('gold_state')}")
        print("Q:", r["question"])
        print("Reference:", r.get("reference_answer"))
        for k, p in enumerate(r["passages"], 1):
            print(f"   [C{k}] {p.get('section_path', '')}: {short(p['text'], 600)}")
        print("\nANSWER:\n" + textwrap.indent(r["answer"], "   "))
        v = ask("\n[c]orrect+supported  [p]artial  [i]ncorrect  [u]nsupported  [q]uit > ", "cpiuq")
        if v == "q":
            break
        done[r["output_id"]] = {"output_id": r["output_id"], "verdict": VERDICTS[v], "judge": a.member}
        save(vfile, list(done.values()))
    print(f"judged by {a.member}: {len(done)} -> {vfile.name}. Commit and push that file.")


def cmd_status(a):
    items = load_items() if ITEMS.exists() else []
    live = [i for i in items if i.get("status") != "rejected"]
    print("\nitems:", len(items), "| rejected:", len(items) - len(live), "| verified:", sum(bool(i.get("human_verified")) for i in live),
          "| second-labelled:", sum(bool(i.get("label_b")) for i in live))
    print("categories:", dict(Counter(i["category"] for i in live)), "| authors:", dict(Counter(i["author"] for i in live)))


def cmd_apply(a):
    """Write all members' decisions and labels into course_items.jsonl (run after `git pull`)."""
    items = load_items()
    save(ITEMS, items)
    cmd_status(a)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("verify", "second-label", "judge"):
        p = sub.add_parser(name)
        p.add_argument("--member", required=True, choices=["A", "B"])
        if name == "judge":
            p.add_argument("--sheet", required=True)
    sub.add_parser("status")
    sub.add_parser("apply")
    a = ap.parse_args()
    {"verify": cmd_verify, "second-label": cmd_second_label, "judge": cmd_judge, "status": cmd_status, "apply": cmd_apply}[a.cmd](a)


if __name__ == "__main__":
    main()
