# Implementation Log: Phase II (decisions, deviations, measured facts)

This log records every implementation decision that refines or departs from the frozen specification (v1.0), with the reason for each. Numbers come only from logged runs, and each one cites its output file.

## Deviations and refinements

| # | Spec reference | Change | Reason / evidence | Effect on research question |
|---|---|---|---|---|
| D1 | ADR-005, C8 | MiniCheck-FT5 inference is **re-implemented** in `learnmate/verify.py` instead of pip-installing the package | The official package pulls in an unpinned `openai` dependency and an optional `vllm` dependency. The re-implementation matches the official package (commit `b58b9fa`) to a max abs diff of **1.2e-7** on 4 pairs (`results/smoke/minicheck_parity.json`) | None |
| D2 | ADR-010 | Stack pinned to **transformers 4.57.6 / sentence-transformers 5.7.0** (CPU lock: `requirements-cpu.lock`) | transformers 5.x is current (5.24.0), but MiniCheck and LettuceDetect were written against 4.x. The GPU lock is produced by notebook 00 | None |
| D3 | C5 | Reranker ID is now `cross-encoder/ms-marco-MiniLM-L6-v2` | `…-L-6-v2` now redirects (HTTP 307) to this canonical ID at the same revision (`233902d`) | None |
| D4 | C6 | Hard negatives are mined with **BM25 only**, within the gate-train article pool | Deterministic and cheap. Dense mining would require embedding 18k paragraphs. Leakage is still impossible (same pool) | Hard negatives may be lexically rather than semantically close; A4 still isolates their value |
| D5 | C9 | **Paragraph-level citation blocks** are propagated. If only the last sentence of a paragraph carries markers and they follow its final punctuation, those markers apply to the paragraph's uncited sentences (status `cited_paragraph`), and every sentence is still verified individually | Observed in a real Qwen3-4B output during the dev smoke test: "… input. [C1][C3][C4][C5]" gave compliance 0.33 (`results/smoke/generation_smoke.json`). Decided before any freeze; sentence-level verification is unchanged | Keeps format quirks from being scored as unsupported claims |
| D6 | C3 | Indexed text = **section path title line + chunk text**. Displayed and verified text = chunk text only | Standard title field. d2l subsection titles ("Basics", "Summary") are meaningless without their path | Applies to all systems equally |
| D7 | Security | Indices are persisted as `.npy` (allow_pickle=False) + JSONL. **No pickle**. BM25 is rebuilt at load | Avoids deserialization of untrusted pickles | None |
| D8 | C1 | The d2l parser also drops framework-specific **prose** blocks (`:begin_tab:`), handles `:citet:`/`:citep:`, and strips the `[**…**]` highlight markup | Found by inspecting real chunks after the first ingest | Cleaner passages |
| D9 | C10 | When the LLM outputs `INSUFFICIENT_EVIDENCE`, every LLM system abstains regardless of score. In AURC such items are ranked last (score −∞) | Makes B2 and G strictly "prompt abstention + additional gate" (protocol §2) | As specified |
| D10 | A5 | The untrained gate uses P(answer) = σ(best-span score − null score) from `deepset/deberta-v3-base-squad2`, computed per passage and aggregated like the trained gate | Defines A5 concretely | None |
| D11 | Calibration | B0's threshold is fitted on **squad-cal** (automatic labels), and B0 is evaluated on SQuAD splits only | Judging extractive spans on course items would add annotation burden for a reference-only baseline | B0 is not part of H1 |
| D12 | Annotation | Course-cal outputs also need human judgments (≈60 items × 1 answer set) before calibration | Correctness labels are required to fit τ. This adds about 2 h per student to the §5 budget | None |

| D13 | C9 / policy | **Verbal-abstention detection**: if the *first* sentence matches a conservative refusal pattern (e.g. "The passages do not state …", "This question cannot be answered …"), the output is treated as `INSUFFICIENT_EVIDENCE` | In the runner smoke test (squad-cal item 3), Qwen3-4B refused in natural language instead of emitting the token, and was scored as answering. Without this, every LLM system (especially B1) is penalised for correct refusals. Tested for over-triggering (`tests/test_citations.py`) | Fairer abstention measurement for all systems |
| D14 | C8 / C10 | The contradiction signal becomes **claim-level conflict**: max over sentences *s* and top-3 passage pairs *i ≠ j* of min(support(*s*, *p_i*), P_contra(*p_j* → *s*)). It replaces whole-passage `pp_contra` in the fusion features and the contradictory-state rule; `pp_contra` is still logged | Whole-passage NLI gave P(contra) = 0.964 for two unrelated paragraphs of the same SQuAD article (smoke records), so it cannot separate real conflicts. The claim-level form gave 0.12–0.64 on the same items and targets exactly what S4 constructs | κ_c is still fitted on dev only; S4 remains diagnostic |
| D15 | Labels | Known limitation: automatic SQuAD correctness (containment or token-F1 ≥ 0.5) misses verbose paraphrases (smoke item 5: "…amount of resources required…" vs gold "its solution requires significant resources") | Conservative: it creates false *errors*. It hits B2 and G identically because they share answers. The 100-item human audit will quantify it | Attenuates rather than biases ΔAURC on SQuAD |

## Measured so far (CPU container, 4 vCPU, no GPU)

| Fact | Value | Source |
|---|---|---|
| Course corpus | 654 sections → 1,242 chunks (≤400 tokens, mean 267.5); spans reproduce section text exactly | `data/manifests/corpus_manifest.json` |
| SQuAD audit | Matches the verified counts exactly; dev = 35 articles | `data/manifests/squad_splits.json` |
| Retrieval, squad-cal (750 answerable, open retrieval over 360 paragraphs) | dense R@5 0.943 / MRR 0.824. Hybrid RRF R@5 0.968 / MRR 0.884. **Hybrid+CE R@5 0.988 / MRR 0.935** / nDCG@10 0.950 | `results/retrieval_squad-cal.json` |
| Retrieval latency (CPU, hybrid + CE over ~40 candidates) | 0.85 s/query | same |
| Index build (CPU, bge-base) | Course 250 s; squad-cal 34 s; squad-test 88 s | console log |
| Generation (CPU, llama.cpp GGUF Q4_K_M, 4 threads) | ≈30–50 s/answer in isolation; ≈2 min/answer under concurrent load | `results/smoke/generation_smoke.json`, runner smoke |
| Gate training throughput on CPU (deberta-v3-xsmall, smoke) | 2.6 examples/s → the full DeBERTa-v3-base run is **infeasible on CPU** | `models/gate-smoke/train_log.json` (smoke_only) |

| M0 model smoke (CPU) | embedder, reranker, gate base, MiniCheck-FT5, NLI, B0 extractive all load and run (e.g. NLI P(contra) "lr 0.1" vs "lr 0.5" = 0.998; B0 extracts "hidden units"). The 4B HF generator needs the GPU tier | `results/m0_smoke.json` |
| End-to-end pipeline smoke | retrieve → generate → gate → B0 → verify → assemble → calibrate → analyze completes on 6 real squad-cal items (smoke gate, llama.cpp). **These numbers are not results** (6 items, in-sample, untrained gate) | `results/smoke/` (git-ignored; analysis refuses smoke thresholds for real runs) |

**Consequence.** All reportable generation, gate training and test runs need the GPU tier (condition C1). This CPU container is used for development, tests, ingestion, indexing, calibration and analysis of cached outputs, and the CPU demo.
