# Implementation Roadmap (Phase II, after approval)

**Window:** 4 weeks (handbook §8) plus an optional extension in weeks 5–10.

**Owners:**
- **A** — retrieval, LLM, UI
- **B** — gate, verification, evaluation
- Both annotate.

**Rules for every milestone:**
- Ends with `pytest -q` passing and a commit.
- No mocked results.
- Real models and data only.

**Handbook checkpoints:**

| Week | Checkpoint |
|---|---|
| W1 | Problem + dataset approval |
| W2 | Baseline review |
| W3 | Stress test |
| W4 | Presentation |

---

## M0 — Repository setup & environment smoke test (Days 1–2) · Owner A+B
- **Depends on:** approval of this specification; GPU access (Colab/Kaggle).
- **Tasks:**
  - Scaffold the layout (`final_architecture.md` §6): `pyproject.toml`, `learnmate/` package, `configs/base.yaml`, seed utility, JSONL logger, `.gitignore` for `data/raw`, `data/processed` and `results/`.
  - `notebooks/00_smoke_colab.ipynb`: load each model once, run one forward pass, record peak VRAM and latency.
    - Models: Qwen3-4B-Instruct-2507 fp16 (then NF4), DeBERTa-v3-base, MiniCheck-FT5, NLI, LettuceDetect, bge-base, CE.
  - Resolve the transformers 4.x/5.x pin (ADR-010) → commit `requirements.lock`.
  - Record HF revision hashes in the config.
- **Outputs:** skeleton repo; `results/m0_smoke.json` (VRAM/latency per model, GPU string); lockfile.
- **Verify:** `pytest -q tests/test_imports.py`; smoke notebook runs top-to-bottom on a fresh Colab.
- **Done when:**
  - All 7 models load and produce outputs.
  - Generator runtime (fp16 vs NF4) decided by measurement.
  - Lockfile committed.
- **Risks:** transformers 5 incompatibility with MiniCheck/LettuceDetect → pin `<5`; Colab GPU unavailable → Kaggle, then CPU fallback (see §Fallbacks).

## M1 — Dataset audit & ingestion (Week 1) · Owner B (+A)
- **Depends on:** M0. Faculty-approval request sent on Day 1, but it does **not** block M1 (provisional corpus).
- **Tasks:**
  - SQuAD download and article-level split → `data/manifests/squad_splits.json` + SHA-256; audit counts (must reproduce the verified counts).
  - d2l clone at a pinned commit → Markdown parser → `sections.jsonl` → chunker → `chunks.jsonl` + SQLite.
  - Dataset card v0 (Deliv. C).
  - Annotation guideline v1; both members begin authoring course items (target 50% by end of W1).
  - Requirement spec (Deliv. A) and 5-paper initial review (W1 checkpoint evidence).
- **Outputs:** manifests, chunk store, dataset card draft, guideline, ≥100 draft items, Deliverable A draft.
- **Verify:** `pytest -q tests/test_ingest.py tests/test_provenance.py tests/test_splits.py`; `python -m learnmate.ingest --config configs/base.yaml --check` reports chunk count, max tokens ≤ 400 and zero cross-heading chunks.
- **Done when:**
  - Deterministic rebuild yields the same chunk IDs and hash.
  - SQuAD counts match the verified values.
  - No split overlap.
- **Risks:** d2l directive parsing edge cases (log `extraction_quality`); annotation lag (start Day 2).

## M2 — Retrieval baseline (Week 1–2) · Owner A
- **Depends on:** M1 chunks.
- **Tasks:**
  - BM25 + FAISS(bge-base) build; RRF; CE rerank; `exclude_chunk_ids`.
  - Retrieval eval on course-dev (gold chunk IDs) and the squad-cal-RAG corpus.
- **Outputs:** indices; `results/retrieval_dev.json` (Recall@5/20, MRR, nDCG@10 for dense / hybrid / hybrid+CE).
- **Verify:** `pytest -q tests/test_retrieval.py`; `python -m eval.run --stage retrieve --split course-dev`.
- **Done when:**
  - Metrics computed from real gold IDs.
  - Index rebuild is deterministic.
  - Exclusion filter tested.
- **Risks:** math-symbol tokenization in BM25 (custom tokenizer; check on dev).

## M3 — Grounded generation baselines B1, B2 (+B0) (Week 2) · Owner A
- **Depends on:** M2, M0 runtime decision.
- **Tasks:**
  - Prompt P_v1 with a 1-shot example.
  - Generator with JSONL cache.
  - Citation validator.
  - `INSUFFICIENT_EVIDENCE` parsing.
  - Format-compliance logging.
  - B1 and B2 run on course-dev and squad-cal.
  - B0 extractive (optional).
  - Iterate the prompt on **dev only**.
- **Outputs:** cached answers; W2 baseline metrics on dev; citation-validity report (must be 100% resolvable after validation).
- **Verify:** `pytest -q tests/test_citations.py tests/test_generate.py`; `python -m eval.run --system b2 --split course-dev`.
- **Done when:**
  - B1 and B2 produce cited answers or typed abstentions on all dev items.
  - W2 checkpoint evidence assembled (working pipeline, initial metrics, split audit).
- **Risks:**
  - Citation format failures → stricter example + regex repair.
  - Generation throughput → measure; reduce squad-cal sample if needed.

## M4 — Research intervention components (Week 2) · Owner B
- **Depends on:** M1 (SQuAD splits), M2 (retriever, for hard-negative mining on gate-train), M0.
- **Tasks:**
  - Gate data builder: positives, SQuAD negatives, retrieval hard negatives; check that no answer string appears in a hard negative.
  - `notebooks/01_gate_training.ipynb`: train ≥1 run with checkpoints; log GPU-minutes and VRAM; gate-dev AUROC.
  - Train an A4 variant (no hard negatives).
  - Verifier module (MiniCheck + NLI) with features.
  - Pick the aggregation variant on dev.
  - Build dev S3/S4 items; fit κ_c on dev.
- **Outputs:** `models/gate-v1` (+ `gate-noHN`); training log; `results/gate_dev.json`; verifier features for dev.
- **Verify:** `pytest -q tests/test_gate_data.py tests/test_verify.py`; overfit-one-batch test; gate-dev AUROC reported (no target is imposed; it is a result).
- **Done when:**
  - Gate checkpoints are reproducible from seed 13 within tolerance.
  - Verifier features are computed for all dev items.
- **Risks:**
  - T4 time over budget → subsample to 30k pairs or fall back to ELECTRA-base.
  - DeBERTa fp16 NaN → fp32 / bf16-off.

## M5 — Annotation freeze & pre-registration (end of Week 2) · Owner B (+A)
- **Depends on:** all items authored; M3 and M4 dev decisions made.
- **Tasks:**
  - Blind second labelling, κ, adjudication.
  - Assign splits by section.
  - Hash `course_items.jsonl`.
  - Write `research/preregistration.md` (H1, m, λ, metrics, analysis-code hash, model revisions, runtime, prompt hash).
  - Tag `prereg-v1`.
- **Outputs:** frozen items; κ report; pre-registration commit.
- **Verify:** `pytest -q tests/test_splits.py` (section-disjoint; near-duplicate scan); `git tag --list prereg-v1`.
- **Done when:**
  - ≥150 adjudicated items.
  - κ reported.
  - Pre-registration tag pushed.
- **Risks:**
  - κ < 0.6 → guideline revision for the disputed category (time-boxed to 1 day).
  - Item shortfall → 150-item floor.

## M6 — Calibration (start of Week 3) · Owner B
- **Depends on:** M5, cached squad-cal and course-cal outputs (B2/G answers, gate and verifier features).
- **Tasks:**
  - Fit the fusion LR on squad-cal.
  - Platt-scale on course-cal.
  - Fit τ for G, B2 and B0 by U(λ=2).
  - Run ablation fits A1–A5 with the same procedure.
  - Write `configs/frozen/thresholds.json`.
  - Plot cal reliability diagrams.
- **Verify:** `pytest -q tests/test_fuse.py tests/test_policy.py`; re-running the calibration script reproduces the thresholds file byte-for-byte.
- **Done when:** thresholds frozen and committed **before** any test inference.

## M7 — Controlled experiments, stress tests, ablations, human audit (Week 3) · Owner B (+A)
- **Depends on:** M6.
- **Tasks:**
  - Single test run E1, E2, E4 (staged GPU jobs).
  - Build stress copies S1–S4 by script; run E3.
  - Shuffle outputs, blind them and judge them (both members); 25% double-judged.
  - Sentence-level citation audit.
  - LettuceDetect secondary scores and their agreement with humans.
  - Statistics (bootstrap, McNemar, Holm).
  - Error tagging.
- **Outputs:** `results/test_v1/*` (predictions, judgments, metrics, plots); W3 checkpoint (baseline failure analysis + proposed modification evidence).
- **Verify:** `pytest -q tests/test_metrics.py tests/test_stats.py`; `python -m eval.run --all --split course-test --require-prereg`; `python -m eval.report --run results/test_v1`.
- **Done when:**
  - All registered analyses produced, including nulls.
  - The test split is touched only by registered runs (the run log proves it).
- **Risks:**
  - Judging time → prioritize the primary analysis (clean course test), then S1, then the others.
  - Negative result → report it with the ablations as diagnosis.

## M8 — Application UI (Week 3–4, parallel with M7) · Owner A
- **Depends on:** M3 (B1/B2), M6 (frozen G).
- **Tasks:**
  - Streamlit chat with state badge, citation chips, passage inspector and "related, not supporting" panel.
  - System toggle.
  - Failure gallery built from real `results/test_v1` cases.
  - Query log and abstention CSV export.
  - Colab tunnel or local run instructions.
  - CPU GGUF option.
- **Verify:** `pytest -q tests/test_app_smoke.py`; manual script of 6 demo queries (one per state + 2 failure cases).
- **Done when:** the demo runs on T4 (co-hosted, VRAM measured) and in the CPU mode.

## M9 — Integration, reproducibility, deliverables A–H (Week 4) · Both
- **Tasks:**
  - Fresh-Colab end-to-end reproduction from README (tables within bootstrap CI).
  - `notebooks/02_experiments.ipynb`, `03_figures.ipynb`.
  - Model cards for the gate.
  - Dataset card final.
  - 4–6 page draft with results populated from `results/` JSON only.
  - 3–5 min demo video.
  - Contribution statement (actual work).
  - Gen-AI disclosure.
  - LCA-3 slides.
- **Verify:** `make reproduce` (or notebook) on a clean runtime; `pytest -q` (full suite).
- **Done when:** the deliverables checklist in `requirements_traceability.md` is all green.

## Optional extension (Weeks 5–10, faculty approval)
- Second corpus (faculty materials via Docling).
- Generator swap A6 (Qwen2.5-7B).
- Learn-then-Test operating point.
- External stress sets (RefusalBench, UAEval4RAG).
- Expanded course set (≥400 items).
- Early-exit latency study.
- Venue targeting (BEA 2027 @ NAACL 2027; AIED/EDM/L@S 2027): verify CFPs.

---

## Fallback strategies (each preserves RQ1/RQ2 where possible)

| Failure | Fallback | Research impact |
|---|---|---|
| No Colab GPU | Kaggle free GPU → any local ≥8 GB GPU with NF4 → CPU mode | — |
| CPU mode | GGUF Q4 generator via llama.cpp; gate = MiniLM-L12 / ELECTRA-small trained on 20k pairs on CPU; verifier = MiniCheck-DeBERTa-v3-Large or HHEM-2.1-Open; skip squad-test (E2) | Primary E1 and ablations A1/A2 preserved; E2 dropped; absolute quality lower, reported |
| Qwen weights inaccessible | `microsoft/Phi-4-mini-instruct` (MIT) → `ibm-granite/granite-3.3-8b-instruct` (Apache-2.0, NF4) | None (generator is shared across systems) |
| MiniCheck install/compat failure | Load `lytang/MiniCheck-DeBERTa-v3-Large` directly via transformers; else HHEM-2.1-Open | Verifier changes; documented |
| Gate training too slow | Subsample to 30k → ELECTRA-base → reduce max_len to 256 | Weaker gate; A5 still tests trained vs untrained |
| Faculty materials never approved | Keep d2l, labelled provisional; seek written approval of d2l as the course text | Compliance note in Deliverable C |
| Faculty supplies different materials late (after W2 freeze) | Use them for demo only; experiments stay on frozen d2l set (re-running would breach pre-registration) | None |
| Annotation shortfall | 150-item floor; report wider CI | Lower power |
| Test result null/negative | Report as negative finding with ablation diagnosis (handbook §9) | Valid outcome |
