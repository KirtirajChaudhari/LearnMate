# LearnMate — Frozen Implementation Architecture (v1.0)

**Design A:** a single-process Python package, `learnmate`, plus evaluation notebooks and a Streamlit app.

The stack has no microservices, no agents, no paid APIs, no LLM fine-tuning and no web fallback.
All thresholds come from `configs/*.yaml` and are fitted only on calibration splits.

```
                       OFFLINE                                              ONLINE (per question)
 d2l Markdown @commit ─┐                                    q ─► normalize ─► BM25 top-20 ┐
 faculty PDF/DOCX ─────┼─► ingest ─► section-aware chunks ─►     │           dense top-20 ┴─► RRF(k=60) ─► CE rerank ─► top-5 P
   (Docling, optional) ┘   + provenance (SQLite/JSONL)          │                                                         │
                           ─► BM25 index + FAISS(bge-base)      │        ┌──────────── trained GATE g(q,p_i) ◄────────────┤
                                                                 │        │                                                ▼
                                                                 │        │                         GENERATE (Qwen3-4B-Instruct-2507, greedy,
                                                                 │        │                         passages labelled [C1]..[C5])
                                                                 │        │                                                ▼
                                                                 │        │                         CITATION VALIDATOR (IDs ∈ P, strip/flag)
                                                                 │        │                                                ▼
                                                                 │        │                         VERIFY: MiniCheck(sentence, cited p) ;
                                                                 │        │                                 NLI contradiction (p_i,p_j),(s,p)
                                                                 │        ▼                                                ▼
                                                                 └──► FUSE (logistic, ≤9 features) ─► calibrated P(safe) ─► POLICY ─► UI / log
                                                                                                         τ from cal split      {sufficient, partial,
                                                                                                                                insufficient, contradictory,
                                                                                                                                system_error}
```

## 1. Component classification

| Class | Components |
|---|---|
| **Mandatory MVP** (working, evaluated assignment) | C1 ingestion; C2 provenance store; C3 chunking + indexing; C4 hybrid retrieval; C5 rerank; C7 grounded generation; C9 citation validation; B1/B2 decision rules; C11 evaluation harness; C12 Streamlit app; config, seeds, logging, tests |
| **Research intervention** (the variable under test) | C6 trained sufficiency gate; C8 claim-level verification + contradiction; C10 fusion, calibration, threshold and decision policy |
| **Optional extensions** (must not delay submission) | Docling PDF/PPTX ingestion of faculty files (becomes mandatory if faculty supplies PDFs); B0 extractive reference; embedder swap (Qwen3-Embedding-0.6B); generator swap (Qwen2.5-7B-Instruct NF4); sentence-pruning evaluation for partial answers; Learn-then-Test risk-controlled operating point; contextual chunk prefixes; early-exit (skip generation when the gate is very low); CPU GGUF demo runtime; second course corpus |

## 2. Component specifications

### C1 Document ingestion
| Field | Specification |
|---|---|
| Function | Turn approved sources into normalized section trees, without network fetches at ingest time |
| Input | (a) `d2l-en` repo at a pinned commit, chapter allow-list in config; (b) optional faculty files (PDF/DOCX/PPTX) in `data/raw/faculty/` |
| Output | `data/processed/sections.jsonl`: `{doc_id, section_path[], title, text_md, source_url, commit, license, char_offsets}` |
| Selected | Custom d2l Markdown parser. It keeps headings and LaTeX (`$…$`, `$$…$$`) verbatim, keeps only `#@tab pytorch` code cells (d2l carries multi-framework tabs) and strips d2l-specific directives (`:label:`, `:eqref:`, `@save`), recording the stripping in the provenance flags. **Docling** (MIT, v2.x) is used for PDF/DOCX/PPTX |
| Alternatives | PyMuPDF4LLM (AGPL, rejected); Marker (weight terms, slow on CPU); MarkItDown (dropped tables in a reported test) |
| Justification | Markdown removes PDF parse error as a confound. Docling gives structure and page numbers for faculty files |
| Compute | CPU, < 1 min for d2l |
| Dependencies | stdlib + `pyyaml`; `docling` (optional extra) |
| Failure handling | Unknown file type, a macro-bearing document, or a parse error → skip and log with `extraction_quality=failed`. Never silently partial. Allow-listed extensions only |
| Tests | Golden-file test on 2 d2l sections; LaTeX preserved; non-PyTorch tabs removed; heading tree correct; deterministic output hash |
| Experimental role | Fixed across all systems |

### C2 Source provenance store
| Field | Specification |
|---|---|
| Function | Single source of truth for passage IDs and citation targets |
| Schema (per chunk) | `chunk_id` (stable hash of doc_id + section_path + ordinal), `doc_id`, `title`, `section_path`, `parent_section_id`, `source_url`, `commit_or_version`, `license`, `attribution`, `page` (PDF only), `char_start`, `char_end`, `text`, `token_count`, `extraction_tool@version`, `extraction_quality` (`ok`/`math_loss`/`table_loss`), `sha256`, `access_date` |
| Storage | `data/processed/chunks.jsonl` plus a SQLite mirror for O(1) ID lookup |
| Failure handling | A duplicate `chunk_id` or a hash mismatch on load → hard error |
| Tests | Every chunk resolves; offsets reproduce the text from its section; ID stability across rebuilds |

### C3 Chunking and indexing
| Field | Specification |
|---|---|
| Function | Section-aware recursive chunking; build the sparse and dense indices |
| Parameters | ≤ 400 tokens (bge tokenizer), 50-token overlap, **never crossing a heading**, paragraph/sentence boundaries preferred; display parent = full section |
| Indices | `rank_bm25` BM25Okapi (lower-case, regex tokenizer that keeps math symbols and identifiers); FAISS `IndexFlatIP` over L2-normalized `BAAI/bge-base-en-v1.5` passage embeddings (query prefix per the BGE card) |
| Alternatives | Semantic chunking (no consistent gain in the Vectara NAACL Findings 2025 study, per secondary sources); Chroma/Qdrant (unnecessary) |
| Compute | Embedding a few thousand chunks: ~1–3 min on CPU, seconds on GPU |
| Failure handling | Index/chunk count mismatch → refuse to serve |
| Tests | No chunk crosses a section; deterministic index rebuild (same IDs and vector checksum); `exclude_chunk_ids` filter works |
| Experimental role | Fixed. The bge-small/Qwen3-Embedding swap is an optional ablation |

### C4 Hybrid retrieval
| Field | Specification |
|---|---|
| Function | Return candidate passages |
| I/O | `(q, exclude_ids=∅) → [(chunk_id, bm25_rank, dense_rank, rrf_score)] × 40` |
| Method | BM25 top-20 ∪ dense top-20 → RRF with k = 60 |
| Used by | B0, B2, G. **B1 uses dense top-5 only** |
| Tests | RRF arithmetic unit test; excluded IDs never returned |

### C5 Cross-encoder rerank
| Field | Specification |
|---|---|
| Model | `cross-encoder/ms-marco-MiniLM-L-6-v2` (Apache-2.0, 22.7M) |
| Alternative | `BAAI/bge-reranker-base` (MIT, 278M): slower; optional |
| I/O | `(q, candidates) → top-5 with raw logit and sigmoid` |
| Logged features | `ce_top1`, `ce_margin = top1 − top2` |
| Compute | ~tens of ms per query on GPU; ~0.3–1 s on CPU (to be measured) |
| Experimental role | B2's abstention score is `ce_top1`; also a fusion feature |

### C6 Trained evidence-sufficiency gate (intervention)
| Field | Specification |
|---|---|
| Function | Estimate P(passage set suffices to answer q) **before** looking at the generated answer |
| Model | `microsoft/deberta-v3-base` (MIT) + binary classification head. Input `[CLS] q [SEP] passage`, max 384 tokens |
| Training data | SQuAD 2.0 train articles minus 22 held-out gate-dev articles. Pairs: positives = answerable (q, gold paragraph); negatives = (unanswerable q, its paragraph) + **retrieval hard negatives** = (answerable q, top-ranked BM25/dense paragraph from the same training pool that does not contain any gold answer string). Target ≈ 60k pairs, ratio ≈ 40% pos / 30% SQuAD-neg / 30% hard-neg (subsample if T4 time requires) |
| Objective | BCE; AdamW, lr 2e-5, warmup 10%, 2 epochs max, batch 16 (gradient accumulation as needed), fp16 if stable (else fp32), seed 13; early stopping on gate-dev AUROC |
| Aggregation at inference | `gate_max = max_i g(q,p_i)`, `gate_top2 = mean of top-2` over the top-5 reranked passages. A concatenated-top-3 variant is compared on **dev only** and one variant is frozen |
| Alternatives | ELECTRA-base / MiniLM-L12 (CPU fallback); untrained `deepset/deberta-v3-base-squad2` no-answer probability (= ablation A5) |
| Justification | Uses SQuAD 2.0 as the handbook intends; sufficiency ≠ relevance (Joren et al.); small enough for a T4 |
| Compute | Training: estimated ≤ 1.5 T4-hours (**measure in M4; subsample if exceeded**). Inference: 5 passes/query, < 50 ms GPU |
| Failure handling | Checkpoint every 1k steps (Colab disconnects); NaN loss → restart in fp32 |
| Tests | Data-builder unit tests (no answer string in hard negatives; no gate-dev article in train); overfit-a-batch sanity test; gate-dev AUROC reported |
| Experimental role | Removed in A2; replaced by untrained gate in A5; trained without hard negatives in A4 |

### C7 Grounded generation
| Field | Specification |
|---|---|
| Model | `Qwen/Qwen3-4B-Instruct-2507` (Apache-2.0, 4.02B, non-thinking only, transformers ≥ 4.51) |
| Runtime | HF transformers, fp16 on GPU (~8 GB weights, estimated). **Fallback:** bitsandbytes NF4 (fp16 compute). One runtime is frozen in the pre-registration commit for *all* evaluation runs. GGUF Q4_K_M (`unsloth/Qwen3-4B-Instruct-2507-GGUF`) via llama-cpp-python for the **CPU demo only** |
| Prompt | System: answer only from the numbered passages; every factual sentence ends with `[C#]`; if the passages do not contain the answer, output exactly `INSUFFICIENT_EVIDENCE`; never use outside knowledge. One worked example. Passages are rendered as `[C1] (section path) text` |
| Decoding | Greedy (`do_sample=False`), `max_new_tokens=320`, fixed seed; outputs cached in JSONL keyed by `(system_retrieval_config, item_id, prompt_hash, model_rev)` |
| Alternatives | Qwen2.5-7B-Instruct (optional swap A6); Phi-4-mini-instruct (MIT; fallback if Qwen weights become inaccessible) |
| Compute | T4 fp16: ~2–6 s per answer (estimate, **measure in M0**) |
| Failure handling | Timeout or exception → typed `system_error` abstention (fail-closed); output containing `<think>` → flagged and stripped (should never happen with 2507) |
| Tests | Prompt rendering snapshot test; cache hit/miss determinism; `INSUFFICIENT_EVIDENCE` parsing |

### C8 Claim-level verification and contradiction (intervention)
| Field | Specification |
|---|---|
| Sentence split | Rule-based splitter (`nltk` punkt or a regex that protects `$…$` math and `e.g.`/`i.e.`) |
| Support verifier | `lytang/MiniCheck-Flan-T5-Large` (MIT weights; Apache-2.0 code, git install at a pinned commit). `support(s) = max over the passages cited by s` of P(supported). An uncited or invalidly cited sentence gets `support = 0` |
| Contradiction | `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` (MIT). `pp_contra = max P(contradiction)` over ordered pairs of the top-3 passages; `sp_contra = max P(contradiction)` of (cited passage → sentence) |
| Features emitted | `sup_min`, `sup_mean`, `frac_supported` (support ≥ 0.5), `pp_contra`, `sp_contra`, `uncited_frac` |
| Alternatives | LettuceDetect-large (kept as the **evaluator**, see C11); HHEM-2.1-Open (CPU option) |
| Compute | ≈ (#sentences × #cited passages) MiniCheck passes + 6 NLI passes; estimated < 1 s on GPU per answer |
| Failure handling | Verifier exception → `system_error` abstention |
| Tests | Known entail/contradict toy pairs; math-protecting sentence splitter; uncited sentence → 0 |
| Experimental role | Removed in A1 |

### C9 Citation validation (MVP invariant)
| Field | Specification |
|---|---|
| Function | Parse `[C#]`; map each to the `chunk_id` of the k-th passage shown; strip IDs outside 1..k |
| Recording | Flag each sentence as `cited` / `uncited` / `invalid_citation` |
| UI distinction | `supported` = cited **and** support ≥ s_min; anything else is shown as "cited but not verified" or removed (policy) |
| Invariant | Every displayed citation resolves to a stored chunk with provenance (100%, tested) |
| Tests | Property tests: random citation strings never produce an unresolved ID in output |

### C10 Fusion, calibration, threshold and decision policy (intervention)
| Field | Specification |
|---|---|
| Features (≤ 9) | `gate_max`, `gate_top2`, `ce_top1`, `ce_margin`, `sup_min`, `sup_mean`, `pp_contra`, `sp_contra`, `uncited_frac`. If the LLM output is `INSUFFICIENT_EVIDENCE`, the item is abstained regardless of score |
| Model | `sklearn` LogisticRegression (L2, C chosen by 5-fold CV) fitted on **SQuAD-cal-RAG**. **Platt recalibration** (2 parameters) on **course-cal**. Ablation: fit course-only |
| Threshold | τ = argmax_τ U_λ=2(τ) on course-cal, with ties broken toward higher coverage. The same rule fits B2's τ_CE and B0's no-answer threshold |
| Contradiction rule | κ_c on `pp_contra` is fixed on **dev** using the dev copies of S4 items (not test) |
| Partial rule | s_min = 0.5 support (MiniCheck default) |
| Policy (testable) | 1. Any component error → `system_error` (abstain). 2. `pp_contra ≥ κ_c` → `contradictory`: show both passages, no adjudication, flag for instructor. 3. `P(safe) < τ` or LLM said `INSUFFICIENT_EVIDENCE` → `insufficient`: abstain, show the 3 nearest sections labelled "related, not supporting". 4. Else if some sentences have support < s_min → `partial`: show only supported sentences plus "This part is not covered by the course material". 5. Else `sufficient`: show the answer with verified citations |
| Display | Uncalibrated scores are never shown as probabilities. The UI shows the state label and, once ECE is reported, the calibrated probability |
| Formal guarantees | **None claimed** (non-exchangeable splits, searched threshold). Clopper–Pearson intervals are reported as descriptive CIs on test selective risk at the frozen threshold. Learn-then-Test is an optional extension |
| Tests | Policy table unit tests (each state reachable); threshold reproducible from cal predictions; τ loaded from a frozen file only |

### C11 Evaluation harness
| Field | Specification |
|---|---|
| Function | Run systems × splits × conditions from cached stage outputs; compute metrics and statistics; export tables and plots |
| Stages | `retrieve` → `generate` → `gate` → `verify` → `fuse` → `decide`. Each is cached and resumable, with one model on the GPU at a time |
| Judges | **Human rubric = primary correctness/support label.** LettuceDetect-large = independent automatic unsupported-span estimate, with human agreement reported. MiniCheck (a decision component) is **never** an evaluator |
| Outputs | `results/<run_id>/predictions.jsonl`, `metrics.json`, risk–coverage CSV/PNG, reliability diagrams, bootstrap and McNemar JSON, environment and VRAM log |
| Tests | AURC on hand-computed toy cases; bootstrap determinism with seed; McNemar exact on toy tables; "test split opened" guard that refuses to run unless the pre-registration hash is present |

### C12 Application interface
| Field | Specification |
|---|---|
| Framework | Streamlit, single process, models cached with `st.cache_resource` |
| Views | Chat; answer with inline citation chips → click opens the stored passage with section path and source link; state badge (sufficient/partial/insufficient/contradictory); "related, not supporting" panel on abstention; system toggle B1 / B2 / LearnMate; pre-loaded failure-case gallery from real logs |
| Logging | Per query JSONL (question, retrieved IDs, scores, state, latency); CSV export of abstained questions for instructor review |
| Note | The UI is not evaluation (HB §2); all reported numbers come from C11 |
| Tests | Smoke test with mocked pipeline; every rendered citation resolves |

## 3. Data flow contracts (Python types)

```python
Passage = {chunk_id, text, section_path, source_url, ce_score, rrf_score, gate_prob}
Answer  = {raw_text, sentences: [{text, citations: [chunk_id], support, sp_contra, status}]}
Decision= {state, p_safe, tau, features: dict, reason, displayed_sentences, related_sections}
```

## 4. Configuration and reproducibility
* `configs/base.yaml` (paths, chunking, k values, model IDs **with HF revision hashes**), `configs/systems/{b0,b1,b2,g,ablations}.yaml`, `configs/frozen/thresholds.json` (written only by the calibration step).
* Global seed utility (python, numpy, torch, cudnn deterministic where available). Seeds: 13 for gate training; bootstrap seed 2026.
* `requirements.lock` produced in M0 on Colab and on CPU (see ADR-010). Model revisions are pinned by commit hash.

## 5. Hardware tiers and memory plan
| Tier | Hardware | What runs | Notes |
|---|---|---|---|
| **T-GPU (primary)** | Colab free T4 (~15 GB usable) or Kaggle T4/P100 | Everything; experiments staged one model at a time | Estimated peaks: generator fp16 ≈ 8–9 GB incl. KV cache for ~2.5k-token prompts; gate training ≈ 6–10 GB at batch 16 × 384 tok fp16; MiniCheck-FT5 ≈ 2 GB. **All to be measured in M0** |
| T-GPU demo (co-hosted) | Same | Generator + gate + MiniCheck + NLI + bge + CE | ≈ 11 GB fp16 estimate; NF4 generator fallback ≈ 6 GB |
| **T-CPU (this container: 4 vCPU, 15 GB RAM, no GPU)** | Development, ingestion, BM25/FAISS, unit tests, calibration and statistics from cached outputs, CPU demo with GGUF Q4 | Generation is slow on CPU (tens of seconds per answer, unmeasured). Gate training on CPU is not planned for the base model |
| Fallback | No GPU at all | Gate: MiniLM-L12 on 20k pairs on CPU; evaluation limited to the course test (~100 items × 2 answer sets) with the GGUF generator | Preserves RQ1/RQ2. Absolute quality drops, so this must be reported |

## 6. Repository layout (to be created in Phase II)
```
learnmate/  config.py seed.py provenance.py ingest/{d2l_md.py,docling_io.py} chunking.py index.py
            retrieve.py rerank.py generate.py citations.py gate/{data.py,model.py,train.py}
            verify.py fuse.py policy.py pipeline.py
eval/       metrics.py aurc.py stats.py stress.py judge_io.py run.py
app/        streamlit_app.py
configs/    base.yaml systems/*.yaml frozen/ (written by calibration only)
data/       manifests/ (split files + SHA-256), annotations/ (course items), raw/ processed/ (git-ignored)
notebooks/  00_smoke_colab.ipynb 01_gate_training.ipynb 02_experiments.ipynb 03_figures.ipynb
tests/      unit + integration (pytest)
research/   this specification
results/    run outputs (git-ignored except summary tables)
```
