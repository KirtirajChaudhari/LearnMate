# Experimental Protocol

**Principle:** the final test data are opened once, after a pre-registration commit. They are never used for model selection, threshold optimization or architecture tuning.

## 1. Phases and data access

| Phase | Data touched | Allowed actions |
|---|---|---|
| Development | course-dev, gate-dev, SQuAD train | Prompt wording, chunk size, gate aggregation variant, κ_c, verifier sentence splitter, debugging |
| Calibration | course-cal, squad-cal | Fit fusion LR (squad-cal), Platt (course-cal), τ for G/B2/B0 (course-cal, U(λ=2)) — automated script only |
| **Pre-registration commit** | — | Commit `research/preregistration.md` (H1, m, λ, metrics, analysis code hash, test-split hash, frozen thresholds, model revisions, runtime). Tag `prereg-v1` |
| Test | course-test, squad-test, stress copies | Run once per system/condition; human judgments; analysis exactly as registered |
| Post-hoc | Any | Allowed only if labelled **exploratory** |

## 2. Systems and shared settings

| Setting | B0 | B1 | B2 | G | Ablations |
|---|---|---|---|---|---|
| Corpus/chunks | shared | shared | shared | shared | shared |
| Retrieval | hybrid+CE top-5 | dense top-5 | hybrid+CE top-5 | = B2 | = G (except A-rerank) |
| Answerer | extractive DeBERTa-SQuAD2 | Qwen3-4B-Instruct-2507 | same | same answers as B2 | same answers |
| Prompt | — | P_v1 | P_v1 | P_v1 | P_v1 |
| Decision score | no-answer margin | none (binary prompt abstention) | ce_top1 | fused P(safe) | variant |
| Threshold rule | U(λ=2) on cal | — | U(λ=2) on cal | U(λ=2) on cal | U(λ=2) on cal |

In addition, every LLM system abstains whenever the model outputs `INSUFFICIENT_EVIDENCE`, so B2 and G both include prompt abstention. They differ only in the additional gate.

## 3. Experiments

| ID | Question | Data | Comparison | Output |
|---|---|---|---|---|
| **E1 (primary)** | RQ1/H1 | course-test (clean) | G vs B2 (+B1 point, B0 reference) | ΔAURC + CI, operating-point table, risk–coverage plot |
| E2 | H1c, RQ3 transfer | squad-test RAG | G vs B2 vs B0 | ΔAURC, ECE |
| E3 | RQ4 robustness | course-test S1–S4 | B1, B2, G | HwSA under S1; correct-answer rate under S2; answer-on-edited-fact rate under S3; contradiction recall under S4 |
| E4 | RQ2/RQ3 ablations | course-test (+squad-test) | G vs A1–A5 | ΔAURC per ablation vs G |
| E5 | RQ5 grounding & usefulness | course-test answered items | B1 vs B2/G-answer set; G's partial-mode pruning (secondary) | Citation P/R, unsupported-claim rate (human; LettuceDetect secondary + agreement), FAC |
| E6 | Retrieval sanity | course-dev/test, squad | dense vs hybrid vs hybrid+CE | Recall@5/20, MRR, nDCG@10 |
| E7 | Cost | all runs | per stage | p50/p95 latency, peak VRAM, gate train GPU-minutes |

Ablations (E4): **A1** −verifier features; **A2** −gate features; **A3** −calibration (min-max-normalized feature mean, τ=0.5); **A4** gate trained without hard negatives; **A5** untrained gate (deepset SQuAD2 no-answer prob). Optional: A6 generator swap Qwen2.5-7B-Instruct (requires new answers → compare G vs B2 within that generator), A7 no reranker, A8 embedder swap.

## 4. Labels and correctness

* **Item error (for risk):** human verdict ∈ {incorrect, unsupported} for answered items; for gold_state=insufficient items, any substantive answer = error; for partial items, an answer is an error if it states any unsupported claim about the uncovered part (strict); `partially_correct` counts as error in the primary analysis and as correct in a lenient sensitivity analysis.
* **Abstention** never counts as error; it reduces coverage.
* **Gold evidence state** comes from the adjudicated annotation, never from a model.
* **Evaluator independence:** MiniCheck/NLI/gate outputs are features of G only. Evaluation uses human labels; LettuceDetect gives a secondary automatic unsupported-claim estimate whose agreement (Cohen's κ / accuracy) with human sentence labels is reported. No LLM-as-judge in the primary analysis.

## 5. Metrics (definitions)

* Coverage = answered / N. Selective risk = errors among answered / answered.
* **AURC** = mean over k=1..N of risk among the top-k items ranked by decision score (descending confidence); ties broken by item_id hash (fixed). B1 has no score → reported as an operating point only.
* HwSA = answered rate on gold_state=insufficient items. FAC = abstention rate on answerable items whose B2/G answer was judged correct when retrieved with gold present (i.e., abstentions that cost a correct answer).
* U(λ) = (#correct answered − λ·#error answered) / N.
* ECE: 10 equal-width bins on fused probability vs (1 − error); Brier score; reliability diagram.
* Citation precision / recall per ALCE definitions on human sentence labels (citation_ok, sentence support).
* Retrieval: Recall@k against `gold_chunk_ids` (any-hit and all-hit for A2 items), MRR, nDCG@10.

## 6. Statistics

* **Primary:** paired bootstrap over test items (10,000 resamples, seed 2026) of ΔAURC (G − B2); two-sided 95% percentile CI; H1 supported iff CI < 0 and coverage-margin condition holds (§ `final_research_problem.md` H1).
* **Secondary (Holm-corrected family):** H1b (HwSA G vs B1, exact McNemar on paired abstain/answer decisions over insufficient items), H1c (squad ΔAURC bootstrap), H1d (S1 HwSA G vs B2, McNemar).
* Ablations: ΔAURC bootstrap CIs, descriptive (no multiplicity claim).
* Effect sizes always reported with CIs; null results reported in the main table.
* **Clopper–Pearson** 95% intervals reported for selective risk at each frozen operating point — *descriptive only, no guarantee*.
* Power note: with ~100 items the CI half-width on ΔAURC is expected to be several points; squad-test (≈1,500 items) gives a large-N directional check.

## 7. Selective-risk guarantee assumptions (why none is claimed)

A Clopper–Pearson / LTT risk bound requires (1) calibration and test examples exchangeable (i.i.d.); (2) threshold fixed before seeing calibration losses, or a multiplicity-controlled selection procedure; (3) correct, independent error labels. Here (1) fails — section-disjoint splits and a SQuAD→course mix; (2) fails for argmax-U thresholding; (3) holds approximately (human labels). Therefore results are empirical comparisons. An optional LTT fixed-sequence analysis on course-cal may be shown as an illustration with these caveats.

## 8. Error analysis

Every test error for G and B2 is tagged (two-judge sample for κ): `retrieval_miss` (gold not in top-5) · `gate_false_accept` · `gate_false_reject` · `verifier_false_support` (incl. math/notation) · `verifier_false_reject` · `generator_unfaithful` (RAGTruth subtypes: evident/subtle conflict, evident/subtle baseless, implicit truth) · `citation_mismatch` · `format_failure` · `system_error`. Report counts by category and by `has_math`; select 5–10 qualitative cases (incl. ≥2 genuine G failures) for paper and demo.

## 9. Memory and latency measurement

`torch.cuda.max_memory_allocated` reset per stage; wall-clock per stage with `time.perf_counter` over the course-test run; report p50/p95; hardware string (GPU model, driver, CUDA, torch, transformers versions) in each `metrics.json`. Gate training: GPU-minutes, peak VRAM, examples/sec.

## 10. Reported tables and figures (Deliverable E/G)

Tables: (1) dataset & split statistics + κ; (2) main comparison (B0/B1/B2/G: AURC, coverage, risk@op, HwSA, FAC, U(1/2/4), ECE, citation P/R, latency, VRAM); (3) stress S1–S4; (4) ablations A1–A5; (5) retrieval metrics; (6) error taxonomy counts. Figures: architecture; risk–coverage curves (course & squad); reliability diagrams (raw vs calibrated); stress bar chart; qualitative cases.
