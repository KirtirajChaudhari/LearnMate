# LearnMate: A Trained Evidence-Sufficiency Gate with Claim-Level Verification for Calibrated Abstention in a Local Course Tutor (Preliminary Study)

*Deliverable G (4–6 pages), numbers filled from `results/runs/course-test__*/analysis*.json`. Convert to the venue template after choosing a venue.*

**Abstract.** AI tutors answer fluently even when the course material does not support the answer. We study abstention in LearnMate, a fully local retrieval-augmented tutor built on an openly licensed textbook. We compare (B1) prompt-only abstention, (B2) a tuned reranker-score threshold, and (G) a gate that fuses a DeBERTa-v3 sufficiency classifier trained on SQuAD 2.0 with retrieval hard negatives, claim-level support verification (MiniCheck) and contradiction detection, calibrated on held-out SQuAD data. On 57 course questions (36 answerable, 21 outside the syllabus), G did **not** lower the area under the risk–coverage curve relative to B2 (ΔAURC = +0.079, 95% CI [−0.002, 0.181]; H1 not supported). G abstained on 20 of 21 out-of-syllabus questions, as did the prompt-only baseline B1, but it refused 42% of answerable questions whose answer was judged correct. Under stress S1 (gold passages withheld) G produced 6 unsupported answers against 32 for B1. The study is preliminary: the course set is small and the thresholds were fitted on out-of-domain data. We report all limitations.

## 1. Introduction
Course tutors built on large language models are attractive, but a tutor that answers from memory when the syllabus is silent creates curriculum misalignment and unauditable claims. Retrieval does not remove the problem: giving a model topically related but insufficient passages can make it *less* willing to abstain (Joren et al., 2025), model scale and reasoning fine-tuning do not fix abstention (Kirichenko et al., 2025), and with explicit abstention prompts small models still answered 41.6% of questions that came with a misleading passage (Setiawan, 2026). Retrieval scores measure relevance, not sufficiency, and citation presence is not citation correctness (Wallat et al., 2025).

We ask whether a small, locally trainable gate that estimates *evidence sufficiency* and verifies *claim support* can decide when to answer better than a tuned reranker-score threshold, in a course-tutor setting and without simply abstaining more. Contributions: (i) a fully local tutor with provenance-checked citations; (ii) a controlled comparison of three abstention mechanisms on identical retrieval and identical answers; (iii) an independently labelled course evaluation set with withheld-evidence stress. We make **no claim of algorithmic novelty**: each component exists in prior work; the contribution is the integration and its controlled evaluation.

## 2. Related Work
**Sufficiency and selective generation.** Joren et al. (2025) combine a context-sufficiency autorater with model confidence to raise selective accuracy; their autorater is a large model. We train a small local classifier instead. **Refusal and abstention.** Trust-Align (Song et al., 2025) aligns generators for grounded refusal; AbstentionBench (Kirichenko et al., 2025) shows that scale and reasoning fine-tuning do not fix abstention; GRAB-RAG (Setiawan, 2026) shows prompt-based abstention fails under misleading context and that an NLI verifier trades coverage for safety. **Grounding verification.** MiniCheck (Tang et al., 2024) gives GPT-4-level sentence grounding with a 770M model; RAGTruth (Niu et al., 2024) supplies a hallucination taxonomy including *implicit truth*, true statements the context does not support; LettuceDetect (Kovács and Recski, 2025) detects unsupported spans. **Attribution.** ALCE (Gao et al., 2023) defines citation precision and recall; Wallat et al. (2025) separate correctness from faithfulness. **Educational RAG.** Yu et al. (2025) deploy a local small model with RAG in a CS1 course but do not verify claims or evaluate abstention. Answerability classifiers go back to SQuAD 2.0 (Rajpurkar et al., 2018) and selective QA under domain shift (Kamath et al., 2020).

## 3. Problem Formulation and Hypothesis
Given a question *q* and an approved corpus, the system returns either a cited answer or a typed abstention. An answer is *safe* if it is correct and every claim is entailed by a cited course passage; a world-true claim the passages do not support counts as an error. We define *relevant* (topically related), *sufficient* (the passages together entail an answer) and *supported* (a sentence is entailed by the passage it cites) as separate notions. Items are ranked by a decision score; risk is the error rate among answered items at a given coverage; **AURC** is the mean risk over all coverages (lower is better), so abstaining on everything cannot win.

**H1 (pre-registered).** On the locked course test items, the paired-bootstrap 95% CI of AURC(G) − AURC(B2) lies below zero, and G's coverage of answerable items is at most 10 percentage points below B2's. H0 is the complement. Secondary analyses are descriptive.

## 4. Method
**Corpus and retrieval.** *Dive into Deep Learning* (CC BY-SA 4.0; commit `23d7a5a`) parsed from Markdown into 1,242 section-aware chunks (≤400 tokens, never crossing a heading, exact source offsets). Hybrid retrieval: BM25 and `bge-base-en-v1.5` fused by reciprocal rank fusion, then `ms-marco-MiniLM-L-6-v2` reranking to the top 5. **Generation.** `Qwen3-4B-Instruct-2507`, greedy decoding, passages labelled [C1]–[C5], inline citations required, an explicit `INSUFFICIENT_EVIDENCE` option; citations are validated against the chunk store and unresolved ones are removed.

**Systems.** *B1:* dense top-5 and the prompt's own abstention. *B2:* the same answers as G, abstaining when the top reranker probability is below τ_CE. *G:* the same answers, plus (a) a **sufficiency gate**: `deberta-v3-base` fine-tuned on SQuAD 2.0 answerable vs. unanswerable pairs and *retrieval hard negatives* (answerable questions paired with top-ranked BM25 paragraphs that contain no gold answer), scored on each top-5 passage and aggregated by max and top-2 mean; (b) **claim-level support**: MiniCheck-Flan-T5-Large scores each answer sentence against the passages it cites; a 3-class NLI model gives a claim-level conflict score; (c) a **logistic fusion** of nine features, fitted on SQuAD calibration data, with a threshold chosen to maximise utility U = (correct − 2·errors)/N. B2 and G share retrieval and answers, so AURC differences isolate the decision score. A typed policy maps the score to *sufficient, partial, insufficient, contradictory* or *system error* (fail closed).

## 5. Experimental Setup
**Data.** SQuAD 2.0 (CC BY-SA 4.0): 130,319 train and 11,873 dev questions; all splits are by article (gate train 420 articles, gate-dev 22, calibration 12, test 23 articles). SQuAD-RAG sets retrieve over all paragraphs of their partition. Course set: 57 questions (A1 25, A2 4, P 7, U1 11, U2 10) in five categories (single-section, multi-section, partially covered, missing detail, out-of-syllabus from chapters not indexed). Items were drafted by an AI assistant from the corpus text and then verified, edited or rejected by both members (disclosed per item); each member also attempted a blind second label of the other's items, but the first attempt was invalid (every item labelled "sufficient", κ = 0) and was not repeated, so **no inter-annotator agreement is reported**. All course items form one locked test set. **Evaluation.** Human judges (one per output, the member who did not author the item, blind to the system; each judge saw an AI-suggested verdict that they accepted or overrode, see Disclosure) label each answer `correct_supported / partially_correct / incorrect / unsupported`; partial correctness counts as error. SQuAD answers use automatic labels (answer containment or token-F1 ≥ 0.5). MiniCheck is a decision component and is never used as an evaluator. **Statistics.** 10,000-resample paired bootstrap over items (seed 2026); exact McNemar tests; Clopper–Pearson intervals are descriptive only. **Ablations:** A1 without the verifier features, A2 without the gate, A3 without calibration, A5 with an untrained gate (off-the-shelf SQuAD-2.0 no-answer score). **Stress:** S1 withholds the gold passages from the index. **Compute:** free Colab T4; generator fp16 peak VRAM 8.13 GB (4.03 GB with NF4), one 14-token answer in 1.6 s, MiniCheck 3.3 GB (`results/m0_smoke_gpu_t4.json`); gate training wall-clock and training VRAM were **not measured** (a zero-step resume overwrote the log; implementation log D18); the gate reached gate-dev AUROC 0.954.

## 6. Results
All numbers come from `results/runs/course-test__{clean,S1}/analysis*.json`; the course test set is 57 items (36 answerable, 21 gold-insufficient). The primary analysis is **strict** (partially correct = error), as registered; the lenient analysis is the registered sensitivity check. The SQuAD test run did not complete in the time available and is not reported.

**Table 1, retrieval** (SQuAD calibration partition): Recall@5 / MRR for dense, hybrid, hybrid+cross-encoder = 0.943/0.824, 0.968/0.884, **0.988/0.935** (`results/retrieval_squad-cal.json`).

**Table 2, main comparison, course test, strict (lenient in brackets).** "Unsupp." is the share of out-of-syllabus questions that were answered (lower is better); "FAC" is the share of correctly answerable questions that were refused (lower is better).

| System | Answered | Selective risk | Unsupp. (of 21) | FAC | U(λ=2) | AURC | ECE |
|---|---|---|---|---|---|---|---|
| B1 prompt-only | 37 | 0.135 (0.027) | 1 (0.048) | 0.00 | 0.386 (0.597) | n/a | n/a |
| B2 CE threshold | 2 | 0.000 (0.000) | 0 | 0.94 | 0.035 (0.035) | 0.062 (0.023) | n/a |
| **G (fused)** | 21 | 0.095 (0.048) | 1 (0.048) | 0.42 | 0.263 (0.316) | 0.141 (0.092) | 0.255 (0.334) |

**H1.** ΔAURC(G − B2) = **+0.079**, 95% CI [−0.002, 0.181] (strict) and +0.069, [0.000, 0.169] (lenient). The coverage condition holds (answerable coverage 55.6% vs 5.6%, margin 10 pp), but the CI does not lie below zero, so **H1 is not supported**. The point estimate favours B2, which has a lower AURC only because it answers two questions in total: its risk is 0 on almost nothing.

**What the data does and does not show.** (i) Both G and B1 abstain on 20 of 21 out-of-syllabus questions; G offers no advantage there. (ii) G answers fewer questions than B1 (21 vs 37) and makes fewer judged errors (2 vs 5, strict), but it achieves a *lower* utility at λ=2 because it refuses 42% of answerable questions that B1 answers correctly. (iii) With so few errors overall (0 to 5 per system) every AURC difference is driven by the rank of one to three items; no ordering of systems should be read from them. (iv) The ECE of G (0.25 strict) shows that the calibration transferred from SQuAD to course text only partly.

**Table 3, ablations** (course test, strict; descriptive, no ablation was tested for significance):

| Variant | Answered | Selective risk | Unsupp. | FAC | AURC |
|---|---|---|---|---|---|
| A1 without verifier features | 12 | 0.000 | 0 | 0.64 | 0.086 |
| A2 without gate | 16 | 0.125 | 1 | 0.58 | 0.158 |
| A3 without calibration | 34 | 0.147 | 2 | 0.12 | 0.125 |
| A5 untrained gate | 18 | 0.111 | 1 | 0.52 | 0.091 |
| G | 21 | 0.095 | 1 | 0.42 | 0.141 |

Removing the verifier features (A1) gave a lower AURC and no errors, at the cost of more refusals; so on this set the verifier is not shown to help. Removing calibration (A3) raises coverage at a higher error rate and doubles the unsupported answers (2 vs 1). These differences amount to one or two items.

**Table 4, stress S1 (gold passages withheld; every answer to an answerable question is unsupported).**

| System | Answered | Of which unsupported | U(λ=2) |
|---|---|---|---|
| B1 | 32 | 32 | −1.123 |
| B2 | 0 | 0 | 0.000 |
| G | 6 | 6 | −0.211 |

G produced about five times fewer unsupported answers than B1 (6 vs 32) and answered one out-of-syllabus question, as B1 did. AURC is identical for all systems (0.910) in this condition and therefore uninformative. This is the one condition in which G clearly improves on the prompt-only baseline, but it is a single stress on 57 items.

**Figures:** risk–coverage curves, reliability diagram and stress bars are produced by `scripts/make_figures.py` (`results/figures`).

## 7. Error Analysis
Every output with a non-"correct" verdict was inspected (system identities were read from the key only after judging was complete). There are seven, all judged "partially correct", by one judge (B); the other judge (A) rated all 38 of their outputs correct, so judge strictness and item author are confounded (see Limitations). The seven outputs are two systems' answers to four questions:

1. **Unsupported detail added to a correct core** (warmup, LM-A-0013; B1 and G): the answers state that the learning rate increases to its maximum, then add claims about random initialisation and very deep networks that the shown passages do not contain. Generator unfaithfulness of the "implicit truth" type: plausible and probably true, but not in the evidence. The same generator output appears under both systems.
2. **Unsupported fact for a partially covered question** (head count of the original Transformer, LM-A-0016; B1 and G): the answer states a number of heads that the course does not give (the demo model in the course differs from the original paper). The correct behaviour is to answer the covered part and say the rest is not covered; neither system did so cleanly.
3. **Extra claim beyond the covered part** (max-pooling vs. average pooling with a missing FLOP count, LM-A-0018; B1 and G): both answers flag that the count is missing but add an unsupported claim about object recognition.
4. **Wrong computation** (padding for a 5×3 kernel, LM-A-0004; B1 only): width padding stated incorrectly; the hybrid pipeline's answer to the same question was judged correct.

All seven are generator faithfulness errors on answerable or partially covered questions; we did not classify retrieval misses, gate false accepts or verifier false supports per item, and we did not analyse the 14 answerable questions with a correct answer that G withheld (FAC 0.42, strict). A full error taxonomy per system is future work.

## 8. Limitations
One textbook, English, provisional corpus pending faculty approval. A small course set (57 items, of which only 2 to 5 outputs per system were judged as errors), so confidence intervals are wide and per-category numbers are descriptive. Fusion weights and thresholds were fitted on SQuAD only and applied to course text without domain adaptation; we measure the transfer and make no guarantee. Questions were AI-drafted and human-verified, which may bias difficulty; one judge per output, so judge strictness is confounded with item author (judge A rated all 38 of their outputs correct, judge B rated 7 of 37 partially correct), and no inter-annotator agreement is available because the blind second labelling was invalid. Judges saw an AI-suggested verdict, which may have anchored them. The SQuAD test run, S2–S4, the no-hard-negative ablation and the formal timing/VRAM measurement of gate training were not completed. Verifiers are untested on mathematical notation, so formula items are reported separately. Stress conditions S2–S4 and the no-hard-negative ablation were not run. We make no formal selective-risk guarantee: calibration and test data are not exchangeable and the threshold is chosen by search. Misleading evidence is not solved by sufficiency checks (Setiawan, 2026).

## 9. Conclusion
On a 57-question course test the fused sufficiency-and-verification gate did not meet the registered criterion (H1 not supported): it did not reduce AURC relative to a tuned reranker threshold, and it did not improve out-of-syllabus abstention over a prompt-only baseline, which already abstained on 20 of 21 such questions with this generator. Its measurable benefit is robustness when the supporting passages are removed (S1: 6 unsupported answers vs 32 for prompt-only), at the price of refusing 42% of answerable questions. With one to five judged errors per system the study cannot separate the components, and a larger, independently labelled course set is the main next step.

## Reproducibility and disclosure
Code, configurations, pinned model revisions, seeds and notebooks: the project repository (branch `claude/wonderful-bohr-1idsaa`). Generative-AI assistance is disclosed in Deliverable H. Deviations and failures: the 57 course questions were drafted by an AI assistant and verified by the members; the first blind second-labelling attempt was invalid and not repeated (D20); the pre-registration file was regenerated once after an interrupted first test run, with only `scripts/where_am_i.py` changing between the two commits (D19); gate training time was not measured (D18); the 72 verdicts for answerable outputs were prepared as AI suggestions from the blinded sheet only (the key was not opened), 66 were accepted and 6 overridden by the judges (A 3, B 3; B first marked seven outputs correct and re-judged them as partially correct after the assistant flagged those overrides as unsupported or wrong), and the judges' final verdicts are used. The SQuAD test run and stress conditions S2–S4 were not completed.

## References
Use `submission/B_literature_matrix.md` (DOIs and URLs) plus: Reimers & Gurevych 2019 (SBERT); Cormack et al. 2009 (RRF); Geifman & El-Yaniv 2017 (AURC); Zhang, Lipton, Li & Smola, *Dive into Deep Learning*; model cards for Qwen3-4B-Instruct-2507, bge-base-en-v1.5, ms-marco-MiniLM-L-6-v2, DeBERTa-v3 and MiniCheck-Flan-T5-Large.
