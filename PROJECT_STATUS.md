# LearnMate (G06) — Project Status

**Phase:** I complete (research reconciliation + specification freeze) → **awaiting approval to start Phase II (development)**
**Last updated:** 23 Nov 2026
**Readiness:** CONDITIONALLY READY. See `research/development_readiness.md`.

## Frozen specification (v1.0)

| Document | Purpose |
|---|---|
| `research/reconciliation_report.md` | Compares the Gemini dossier and the Markdown report; conflicts A–E and their resolutions |
| `research/verified_sources_and_corrections.md` | Verification of models, licenses, data and papers; correction audit trail; revised 10-paper matrix |
| `research/final_research_problem.md` | Problem, objectives, RQs, H1/H0, intervention, baselines, metrics, limitations |
| `research/final_architecture.md` | Component specifications, contracts, hardware tiers, repository layout |
| `research/architecture_decisions.md` | ADR-001 to ADR-014 |
| `research/dataset_and_annotation_plan.md` | SQuAD splits, provisional corpus, course item schema, annotation protocol and budget, stress sets |
| `research/experimental_protocol.md` | Experiments E1–E7, labels, metrics, statistics, guarantee assumptions |
| `research/implementation_roadmap.md` | Milestones M0–M9 with verification commands, plus fallbacks |
| `research/requirements_traceability.md` | Handbook → specification → evidence; deliverables A–H; rubric |
| `research/inputs/` | The three original inputs, unchanged (SHA-256 in `SHA256SUMS`) |

## One-line summary of the plan

The system is a local RAG tutor over d2l. The d2l corpus is provisional and still awaits faculty approval. The pipeline:

1. **Retrieval:** BM25 + bge-base, fused with RRF, then reranked by ms-marco-MiniLM.
2. **Generation:** Qwen3-4B-Instruct-2507 writes cited answers.
3. **Sufficiency gate:** a DeBERTa-v3-base model trained on SQuAD 2.0 plus hard negatives.
4. **Verification:** MiniCheck checks claims; a DeBERTa NLI model checks for contradictions.
5. **Decision:** a calibrated logistic fusion uses a utility-chosen threshold. It outputs one of four states: sufficient, partial, insufficient or contradictory.

The test compares this pipeline with a reranker-score threshold baseline. The primary metric is AURC on a locked, double-annotated course test set. Stress tests and ablations are also run.

## Milestones

| Milestone | Status |
|---|---|
| Phase I research (two independent reports) | ☑ done (inputs) |
| Reconciliation, verification, specification freeze | ☑ done |
| Phase II approval | ☐ **pending user approval** |
| M0 Repository and environment smoke test | ☐ |
| M1 Dataset audit and ingestion | ☐ |
| M2 Retrieval baseline | ☐ |
| M3 B1/B2 generation baselines | ☐ |
| M4 Gate training, verifier | ☐ |
| M5 Annotation freeze and pre-registration | ☐ |
| M6 Calibration | ☐ |
| M7 Experiments, stress tests, ablations, human audit | ☐ |
| M8 Streamlit UI | ☐ |
| M9 Reproducibility and deliverables A–H | ☐ |

## Open blockers and conditions

1. **GPU access.** This container has no GPU. Colab or Kaggle is needed from M0.
2. **Faculty approval** of the course corpus. d2l is in use as a provisional corpus meanwhile.
3. **Instructor confirmation** of the coverage-loss margin (m = 10 pp) and the utility weight (λ = 2) before pre-registration.

## Code status

No application code, no model downloads and no training yet. This is intentional; Phase II has not been approved.
