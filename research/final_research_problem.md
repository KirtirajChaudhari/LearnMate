# LearnMate (G06) — Final Research Definition

**System:** LearnMate, an evidence-grounded course AI tutor. It answers student questions from approved course material, gives citations that can be verified, and abstains when the evidence is inadequate.

**Working paper title** (revises the handbook placeholder after the novelty review): *"LearnMate: A Trained Evidence-Sufficiency Gate with Claim-Level Verification for Calibrated Abstention in a Local Course Tutor"*

---

## 1. Research problem

Small, locally deployable RAG tutors still answer when the course passages they retrieve are **topically relevant but evidentially insufficient**. Typical cases: a question outside the syllabus, a passage that covers only part of the question, or a missing decisive fact. These tutors also produce sentences that their cited passages do not entail.

The cheap abstention mechanisms in common use do not separate these cases reliably:
- **"Say I don't know" prompting** (AbstentionBench, NeurIPS 2025; GRAB-RAG, AACL 2026).
- **Thresholding a retrieval or reranker score.** This measures relevance, not sufficiency.

The large-model sufficiency raters that do work (Joren et al., ICLR 2025, which uses a 24B autorater) cannot run on a free Colab GPU.

**Research question in plain terms:** in a course-tutor setting, can a small *trained* sufficiency classifier, fused with claim-level entailment checks and calibrated on held-out data, rank answers by risk better than a tuned reranker-score threshold? And can it do so without simply abstaining more often?

**Definitions used throughout:**

| Term | Meaning |
|---|---|
| Relevant | The passage is topically related to the question. This is the reranker's job |
| Sufficient | The passages together entail an answer to the question. This is the gate's job |
| Correct | The answer is right **and** each of its claims is entailed by course passages. A world-true but unsupported claim is an *error* in this system (RAGTruth "implicit truth") |
| Cited | A sentence carries a valid passage ID |
| Supported | The cited passage entails the sentence. Citation existence ≠ citation correctness |

## 2. Research objectives

| Objective | Description |
|---|---|
| O1 | Build B0–B2 baselines and the LearnMate pipeline (G) over one provisional course corpus, with provenance-preserving citations |
| O2 | Train a DeBERTa-v3-base answerability/sufficiency cross-encoder on SQuAD 2.0 plus retrieval hard negatives |
| O3 | Combine gate, verifier and retrieval features into a calibrated answer/abstain score, with the threshold fixed on a calibration split |
| O4 | Construct an independently double-labelled course evaluation set (~200 items) with leakage-safe splits |
| O5 | Compare G against the baselines on the locked test set, under four stress conditions, with ablations, human-audited factuality and error analysis |
| O6 | Release a reproducible package (code, configs, seeds, notebook, dataset card) and a working Streamlit demo |

## 3. Principal research question

**RQ1.** On a held-out course test set, does the calibrated fused gate (G) produce a lower area under the risk–coverage curve (AURC) than abstention based on a reranker-score threshold (B2)? Both systems use identical retrieval and identical generated answers.

## 4. Supporting questions

| ID | Question |
|---|---|
| RQ2 (attribution) | Which signal carries the effect: the trained gate or the claim-level verifier? Answered by ablations A1 and A2 |
| RQ3 (training value) | Does training the gate on SQuAD 2.0 plus retrieval hard negatives beat an untrained alternative (the off-the-shelf SQuAD 2.0 no-answer score, A5) and training without hard negatives (A4)? Does it transfer from Wikipedia to course text? Measured by ECE and AURC on course cal/test |
| RQ4 (robustness) | How do B1, B2 and G behave when gold evidence is withheld (S1), distractors are injected (S2), evidence is misleading (S3) or two passages contradict each other (S4)? |
| RQ5 (usefulness and citations) | Among answered items, does G improve citation precision and recall and the human-checked supported-claim rate? How much answerable-question coverage does it cost? |

## 5. Falsifiable hypothesis (pre-registered before the test set is opened)

**H1.** On the locked LearnMate course test split, G yields a **lower AURC** than B2:
- Δ = AURC(G) − AURC(B2) < 0.
- The 95% paired-bootstrap CI (10,000 resamples over items) excludes 0.
- At G's frozen operating threshold, **coverage of answerable items** is not lower than B2's frozen operating point by more than the pre-registered margin *m*. The proposed default is *m* = 10 percentage points; the instructor confirms it in Week 1.

**H0.** At least one of the following holds:
- The CI for ΔAURC includes 0.
- ΔAURC ≥ 0.
- G improves AURC only by exceeding the coverage-loss margin.

**Secondary hypotheses.** These are reported with Holm correction and do not decide H1.

| ID | Hypothesis |
|---|---|
| H1b | On items whose gold state is insufficient (missing-detail and out-of-syllabus), G's unsupported-answer rate (HwSA) at its operating point is lower than B1's (prompt-only) |
| H1c | On the SQuAD-RAG test split (in-domain for the gate), the direction of ΔAURC matches H1 |
| H1d | Under S1 (withheld gold), G's HwSA is lower than B2's |

**What does not count as success:**
- A higher abstention rate on its own.
- Better ECE on its own.
- Improvement on SQuAD only. SQuAD is in-domain for the gate, so it is reported but cannot confirm H1.

## 6. Research intervention (G)

The intervention is **B2 plus four additions**:

1. **Trained sufficiency gate.** A DeBERTa-v3-base cross-encoder fine-tuned on SQuAD 2.0. Answerable (question, gold paragraph) pairs are positives. Two kinds of pair are negatives: unanswerable SQuAD pairs, and *retrieval hard negatives* (answerable questions paired with top-ranked non-gold paragraphs that do not contain the answer). The gate scores each of the top-5 reranked passages. Pooled features are the max and the top-2 mean.
2. **Claim-level verification** of the generated answer. MiniCheck-Flan-T5-Large scores each sentence against the passages it cites, and support is the max over those passages. A 3-class DeBERTa NLI model gives contradiction probabilities between the top passages and between each sentence and its cited passages.
3. **Fusion and calibration.** A logistic regression over at most 9 features (gate, verifier, CE score and margin, contradiction, uncited-sentence flag). It is fitted on SQuAD-cal-RAG and then Platt-recalibrated on course-cal.
4. **Threshold and decision policy.** One threshold τ maximizes utility U(λ=2) on the calibration split and is then frozen. Testable rules map the score to one of four states: *sufficient*, *partial*, *insufficient* or *contradictory*.

**Novelty claim:** none algorithmic. Each component is published:
- SQuAD-style answerability classifiers (Kamath et al. 2020)
- Sufficiency-based selective generation (Joren et al. 2025)
- Grounding verifiers (MiniCheck 2024; HALT-RAG 2025)

The contribution is a *replication-plus-adaptation and controlled evaluation*. It tests whether a small trained gate plus claim verification beats a tuned reranker threshold for a local course tutor, on an independently annotated course set, under stress, with an honest report of what fails.

## 7. Baselines

All systems share the corpus, chunking, top-k, prompt template and generator (`Qwen3-4B-Instruct-2507`, greedy decoding).

| ID | System | Role |
|---|---|---|
| **B0** | Hybrid retrieval + rerank → extractive `deepset/deberta-v3-base-squad2` with no-answer threshold (fitted on cal) | Reference: classic SQuAD 2.0 abstention without generation |
| **B1** | Dense-only (bge-base, top-5) → LLM with "answer only from context, otherwise say you don't know", inline `[C#]` citations | Common deployed default; prompt-only abstention (binary, one operating point) |
| **B2 (strong)** | Hybrid BM25 + dense with RRF → ms-marco-MiniLM rerank top-5 → same LLM and prompt → abstain if top-1 CE score < τ_CE (τ_CE fitted on cal with the same U(λ) rule as G) | Isolates the value of a *trained, fused* gate over a tuned relevance score |
| **G** | B2 retrieval and answers + intervention (§6) | Intervention |

B2 and G receive **identical answers**. Their only difference is the decision score, so ΔAURC measures ranking quality and nothing else.

## 8. Primary metric

**AURC** (Geifman & El-Yaniv 2017) on the locked course test split. Items are ranked by each system's decision score. An item counts as an *error* when the human judge says the answer is incorrect **or** contains a claim not supported by the course corpus. Items whose gold state is insufficient count as an error whenever any substantive answer is given. Lower AURC is better. An always-abstain system cannot game AURC because AURC integrates risk over every coverage level.

## 9. Secondary metrics

- **Abstention**
  - Coverage
  - Selective risk at the operating point
  - Risk@coverage 0.5/0.7
  - Unsupported-answer rate (HwSA) on insufficient items
  - False-abstention cost (FAC) on answerable items
  - Utility U(λ) for λ ∈ {1, 2, 4}
  - Answerability macro-F1 against the gold evidence state
- **Calibration:** ECE (10 bins) and Brier score of the fused probability; reliability diagrams
- **Grounding:**
  - ALCE-style citation precision and recall (human audit; LettuceDetect as secondary automatic estimate)
  - Unsupported-claim rate
  - Citation-ID validity, where 100% is an invariant
- **Retrieval:** Recall@5, Recall@20, MRR, nDCG@10 against gold passage IDs
- **Cost:** p50/p95 latency per stage, peak VRAM, gate training GPU-minutes

## 10. Required ablation

**A1 (−verifier: gate and retrieval features only)** and **A2 (−gate: verifier and retrieval features only)**. A2 is approximately the Gemini dossier's ES-CA design without the span detector. These two ablations answer RQ2.

Additional ablations:

| ID | Change |
|---|---|
| A3 | −calibration: uncalibrated mean of normalized scores, threshold 0.5 |
| A4 | Gate trained without retrieval hard negatives |
| A5 | Untrained gate: the no-answer probability of `deepset/deberta-v3-base-squad2` |

The reranker removal and the generator swap (Qwen2.5-7B-Instruct) are optional.

## 11. Application-specific stress test

**S1 (withheld gold evidence)** is mandatory. For every answerable test item, its gold passages are removed from the BM25 and FAISS indices (`exclude_chunk_ids`) and the full pipeline is re-run. The correct behaviour is abstention, unless another passage genuinely supports the answer; human checks are run on a sample to confirm this. This matches the failure mode a deployed tutor meets most often: the material does not cover the question, but nearby material looks relevant.

S2 (distractor injection), S3 (misleading single-fact edit) and S4 (contradictory pair) are also planned. S3 is **diagnostic**: GRAB-RAG shows that sufficiency checks cannot detect evidence that is sufficient but false.

## 12. Limitations (stated up front)

- **One course corpus, and a provisional public one** (d2l). Transfer to other subjects or to slide-heavy materials is not established.
- **Small course test set** (~100 items). CIs will be wide and per-category estimates are only descriptive.
- **Two student annotators** who also built the system. Mitigations: blind cross-labelling, Cohen's κ, an adjudication log, and faculty escalation for disputes.
- **SQuAD 2.0 unanswerables are paragraph-local and lexically adversarial.** The gate may not transfer, and this is measured, not assumed.
- **Verifiers are untested on math and notation.** Formula items are reported as a separate error slice.
- **Misleading evidence (S3) is expected to remain largely unsolved.**
- **No statistical guarantee on selective risk is claimed.** Calibration and test data are not exchangeable (they come from different sections and partly different domains), and the threshold is chosen by search.
- **Citation correctness is measured; citation faithfulness is probed only indirectly.** Faithfulness means the model actually relied on the cited passage. S1 is the only probe of it (Wallat et al. 2025).
- **Generator-specific results.** The effect may differ for other LLMs; the optional A6 swap partly addresses this.
