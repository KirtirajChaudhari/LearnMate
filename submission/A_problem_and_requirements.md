# Deliverable A: Problem Statement and Requirement Specification (G06 LearnMate)

**Groups/Members:** ______ and ______  **Course:** Deep Learning Networks, M.Tech. AI–ML  **Date:** ______

## 1. Problem
AI tutors can give plausible but unsupported explanations. LearnMate is a course-specific, document-grounded assistant. It answers student questions **only** from approved course material, shows citations the student can check, and **abstains** when the material does not contain adequate evidence.

**Application failure mode we quantify.** *Unsupported answers to questions the course material cannot fully answer*: out-of-syllabus questions, questions missing a specific fact, and partially covered questions. Its paired cost is *false abstention on answerable questions*. Metrics: unsupported-answer rate (answer rate on questions the course does not cover), coverage, and risk–coverage (AURC).

## 2. Stakeholders and workflow
| Stakeholder | Need | Harm if the system fails |
|---|---|---|
| Students | Correct, course-consistent explanations with a pointer into the text | Learning a wrong or off-syllabus explanation with false confidence |
| Instructors | Answers within syllabus and notation; a view of which questions went unanswered | Misinformation attributed to the course |
| Evaluators | Reproducible, honestly reported claims | Unverifiable "works well" claims |

**Workflow.** Instructor approves the course documents → ingestion with provenance → student asks a question → hybrid retrieval and reranking → a trained gate and claim-level verifier decide *answer / partial / abstain / contradictory* → the cited answer, or an abstention with the nearest *related, not supporting* sections, is shown → the interaction is logged.

## 3. Inputs, outputs, constraints
- **Input:** an English question. **Output:** an answer with sentence-level citations (each resolving to a stored passage with section path and source link), or a typed abstention with the nearest sections.
- **Constraints:** no paid APIs; free Colab T4 or a laptop; open licences (SQuAD 2.0 and *Dive into Deep Learning*, CC BY-SA 4.0); two students; 3–4 weeks.
- **Corpus:** *Dive into Deep Learning* chapters (provisional, pending faculty approval): 1,242 passages from 10 chapters.

## 4. Functional requirements (must)
| ID | Requirement | Acceptance check |
|---|---|---|
| FR-1 | Provenance-tracked ingestion and section-aware chunking | Every chunk reproduces its source span; no chunk crosses a heading (automated check) |
| FR-2 | Hybrid retrieval with reranking | Recall@5 reported on real gold labels |
| FR-3 | Grounded generation that forbids outside knowledge | Prompt P_v1; citations required on factual sentences |
| FR-4 | Every displayed citation resolves to a stored passage | Property test; 100% |
| FR-5 | Cited ≠ supported: a sentence counts as supported only if its cited passage entails it | MiniCheck support ≥ 0.5 |
| FR-6 | Typed policy for sufficient / partial / insufficient / contradictory | Unit tests reach every state |
| FR-7 | Fail closed: any component error → abstain | Test |
| FR-8 | Demo UI showing citations, passages and abstentions | Streamlit app |

## 5. Non-functional requirements
Reproducibility (pinned model revisions, seeds, cached greedy decoding); licence compliance; peak VRAM ≤ 15 GB on a T4 (measured, `results/m0_smoke.json`); no probabilities displayed unless calibrated.

## 6. Measurable success criterion (pre-registered)
**H1:** on the course test items, the 95% paired-bootstrap CI of AURC(LearnMate gate) − AURC(reranker-score-threshold baseline B2) lies below 0, and answerable-question coverage does not drop by more than 10 percentage points. This is a hypothesis, not an expected result. A null result is reported as a finding.
