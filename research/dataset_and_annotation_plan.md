# Dataset and Annotation Plan

There are three data sources:
1. SQuAD 2.0
2. The approved course corpus (provisional: d2l)
3. The independently checked LearnMate course evaluation set

**Retrieval access is separate from question partitioning.** The retrieval index always holds the whole course corpus subset. The dev, calibration and test splits divide the evaluation questions only. The corpus text itself is never split.

---

## 1. SQuAD 2.0

| Field | Value (verified 23 Nov 2026) |
|---|---|
| Source | `rajpurkar/squad_v2` (HF), mirror of https://rajpurkar.github.io/SQuAD-explorer/ |
| License | CC BY-SA 4.0 |
| Train | 130,319 Qs (86,821 answerable / 43,498 unanswerable); 442 articles; 19,029 paragraphs |
| Dev | 11,873 Qs (5,928 / 5,945); **35 articles**; 1,204 paragraphs |
| Test | Hidden (not used) |
| Version pinning | Record the HF dataset revision hash and the SHA-256 of the parquet files in the dataset card |

**Partitioning.** All splits are by article title, assigned by a seeded shuffle (seed 2026). Exact counts go into `data/manifests/squad_splits.json` with SHA-256.

| Partition | Source | Use |
|---|---|---|
| `gate-train` | 420 train articles | Gate training pairs, including hard negatives mined within this pool only |
| `gate-dev` | 22 held-out train articles | Gate early stopping, aggregation choice, sanity AUROC |
| `squad-cal` | 12 dev articles | Generate B2/G answers in an open-retrieval setting over the paragraphs of these 12 articles. Fit the fusion LR |
| `squad-test` | 23 dev articles | Secondary confirmatory test (H1c). Open retrieval over these articles' paragraphs. Locked |

**SQuAD-RAG construction.** Each question retrieves over *all paragraphs of its partition*, not over its oracle paragraph. Gold passage = the source paragraph. Automatic correctness labels:
- Answerable items: correct if the normalized answer contains any gold answer string, or token-F1 ≥ 0.5.
- Unanswerable items: any non-abstention is an error.
- A 100-item human audit measures how accurate these automatic labels are.

**Item budget.** About 1,500 questions are sampled from squad-cal and about 1,500 from squad-test, stratified 1:1 answerable:unanswerable, to bound generation time. Each split needs roughly 1–2 T4 hours of generation (to be measured).

**Known limitations** (for the dataset card):
- Wikipedia domain.
- Extractive short answers.
- Unanswerables are paragraph-local and lexically adversarial (crowd-written).
- In open retrieval, another paragraph can occasionally answer a "no-answer" question. These cases are sampled in the audit.
- SQuAD-test is in-domain for the gate, so it is never used as primary evidence.

## 2. Course corpus (provisional)

| Field | Value |
|---|---|
| Source | `github.com/d2l-ai/d2l-en`, Markdown sources, **commit pinned at ingest** (recorded in the manifest) |
| License | Text CC BY-SA 4.0; sample code modified MIT (LICENSE-SAMPLECODE). Both verified |
| Attribution | "Zhang, Lipton, Li, Smola — Dive into Deep Learning" with link and license, shown on every cited passage in the UI |
| Approval status | **Pending faculty approval.** It is not an approved course material until signed off on handbook §10 |
| Indexed subset (proposal) | Roughly 8 chapters matching an M.Tech DL syllabus: preliminaries, linear regression, MLPs, builders' guide, CNNs, modern CNNs, RNNs, attention/transformers, optimization. The chapter list is frozen in config |
| Held-out chapters | E.g., GANs, recommender systems, reinforcement learning, NLP applications. Not indexed; source of out-of-syllabus questions (ADR-013) |
| Preprocessing | Keep the heading tree and LaTeX. Keep PyTorch code tabs only. Strip d2l directives. Chunk ≤ 400 tokens with 50-token overlap, never crossing a heading. Record SHA-256 per chunk |
| Faculty files (if supplied) | `data/raw/faculty/` → Docling → same schema. Record the permission note and the redistribution terms. Never commit to a public repo without written permission |

## 3. LearnMate course evaluation set

### 3.1 Size: reconciling the two reports

| | GEM | MDR | **Final** |
|---|---|---|---|
| Total | 180–240 | 150–300 (target ~200) | **200 (hard floor 150)** |
| Splits | Cal 60–80 / Test 120–160 (no dev) | 30% dev / 20% cal / 50% test | **Dev 40 / Cal 60 / Test 100** |
| Split unit | Module | Section | **Section** of the gold evidence (d2l subsection). Out-of-syllabus items are split by held-out chapter |

**Rationale.**
- A dev split is needed so that prompts, chunk size, κ_c and aggregation can be tuned without touching cal or test.
- Cal needs enough items of each type for Platt scaling and choosing τ. At 60 items, roughly 30 are answerable and 30 are not.
- At 100 test items, a paired bootstrap can detect a moderate ΔAURC. Per-category rates will have wide CIs and are therefore descriptive only.

### 3.2 Categories (clean test; contradictions are stress-only)

| Code | Category | Gold state | Share | ~Count of 200 |
|---|---|---|---|---|
| A1 | Single-section answerable | sufficient | 35% | 70 |
| A2 | Multi-section answerable (synthesis) | sufficient | 10% | 20 |
| P | Partially answerable (one part covered, one not) | partial | 15% | 30 |
| U1 | In-domain missing detail (course terminology, plausible, but the specific fact is absent) | insufficient | 20% | 40 |
| U2 | Out-of-syllabus (topic in held-out chapters; world-true answer exists) | insufficient | 20% | 40 |

Overall, 45% of items are fully answerable and 55% are partial or insufficient, close to SQuAD dev's 1:1. The UAEval4RAG taxonomy is used as a checklist so that U1 items vary (underspecified, false-premise and missing-fact variants). About 15% of items should involve formulas, tagged `has_math`, to support the math error slice.

### 3.3 Item schema (`data/annotations/course_items.jsonl`)
```json
{"item_id":"LM-0001","question":"...","category":"A1|A2|P|U1|U2",
 "gold_state":"sufficient|partial|insufficient",
 "gold_chunk_ids":["..."],"gold_spans":[{"chunk_id":"...","char_start":0,"char_end":0}],
 "reference_answer":"...","required_claims":["...","..."],"uncovered_claims":["..."],
 "section_path":"...","split":"dev|cal|test","has_math":false,"difficulty":"easy|med|hard",
 "author":"A|B","label_b":{"gold_state":"...","gold_chunk_ids":["..."]},
 "adjudication":{"final":"...","rationale":"..."},"genai_assisted":false,"license":"CC BY-SA 4.0"}
```
Chunk IDs are assigned after ingestion is frozen. If the corpus is rebuilt, a migration script maps spans to new IDs using character offsets.

### 3.4 Judgment schema (outputs, after systems run; test only)
```json
{"item_id":"...","system":"B1|B2G","condition":"clean|S1|S2|S3|S4",
 "verdict":"correct_supported|partially_correct|incorrect|unsupported|abstained",
 "sentence_labels":[{"idx":0,"label":"supported|unsupported|contradicted","citation_ok":true}],
 "judge":"A|B","second_judge":"...","notes":"..."}
```
B2 and G share answers, so one judgment covers both (`B2G`).

## 4. Annotation protocol (independent checking)

1. **Authoring.** Sections are partitioned between Member A and Member B (A: chapters 1–4; B: chapters 5–8 plus held-out chapters for U2, split evenly). Each member writes about 100 items with gold spans, working **from the corpus text, not from system outputs**. Generative AI may draft candidate question wordings only if the use is disclosed (`genai_assisted=true`); every item is verified by a human against the corpus.
2. **Blind second labelling.** Each member labels the partner's items for `gold_state` and `gold_chunk_ids` using the corpus browser. They see neither the author's labels nor any system output.
3. **Agreement.** Report Cohen's κ on `gold_state` (3 classes) and span-overlap F1 on gold chunks. Target κ ≥ 0.70. If κ < 0.6, revise the guideline and re-label the disputed category.
4. **Adjudication.** Disagreements are discussed and the rationale is logged. Unresolved items go to faculty or the TA, or are dropped. The drop count is reported.
5. **Freeze.** At the end of Week 2, `course_items.jsonl` is hashed. The test split file and the pre-registration document are committed together (see `experimental_protocol.md` §1).
6. **Output judgments** (Week 3). Each test output is judged by one member with the system identity hidden. Outputs are shuffled and the system label is removed. 25% of outputs are double-judged for κ. A judge never grades outputs for items they authored, where feasible.

## 5. Annotation burden (two students)

| Task | Per item | Volume per student | Hours per student |
|---|---|---|---|
| Author item + gold spans | ~5 min | 100 | ~8.5 |
| Blind second label | ~3 min | 100 | ~5 |
| Adjudication + guideline | — | — | ~2 |
| Output judgments, clean test (B1 + B2G answers, 200 outputs total) | ~2 min | 100 | ~3.5 |
| Stress S1–S4 judgments (sampled, ~160 outputs total) | ~2 min | 80 | ~2.7 |
| Double-judging 25% + sentence-level citation audit (≥ 20% of answered items) | — | — | ~3 |
| SQuAD automatic-label audit (100 items) | ~1 min | 50 | ~1 |
| **Total** | | | **≈ 25 h per student** |

This is feasible alongside engineering in 3–4 weeks only if authoring starts in Week 1. If the budget slips, the fallback is the 150-item floor (dev 30 / cal 45 / test 75) with a wider CI, which must be acknowledged.

## 6. Stress-set construction (test items only; built after the freeze, by script)

| ID | Construction | Applies to | Correct behaviour |
|---|---|---|---|
| S1 | Remove the item's `gold_chunk_ids` from both indices | Answerable test items (A1, A2, P) | Abstain, unless another chunk truly supports the answer (human check) |
| S2 | Replace 2 of the top-5 reranked passages with high-ranked non-gold passages from the same chapter | A1/A2 test items | Still answer correctly with supported citations |
| S3 | Edit one fact in a gold chunk copy (number, sign, entity or formula term) and substitute it for the original in the index. Edits are recorded in `stress_edits.jsonl` | ~30 A1 test items | Diagnostic: report the answer rate on the edited fact |
| S4 | Keep the original **and** add the edited copy | Same ~30 items | `contradictory` state |

The dev versions of S3 and S4 (about 15 dev items) are built in Week 2 to fit κ_c. Test versions are never used for tuning.

## 7. Leakage prevention checklist (automated in `tests/test_splits.py`)

- No course item section appears in two splits.
- No SQuAD article appears in two partitions. Gate hard negatives come only from `gate-train` articles.
- Near-duplicate questions across splits are flagged (bge cosine > 0.92) and reviewed.
- The gate never sees course text (logged training manifest).
- Thresholds are written only by the calibration script, from cal predictions. The test runner refuses to run unless the frozen thresholds file and the pre-registration hash exist.
- Prompt, chunking and model revisions are frozen in the pre-registration commit. Any later change is labelled *exploratory* in all reports.

## 8. Dataset card (Deliverable C) fields

For each dataset, record:
- Name and version (commit or revision)
- Source URL, access date, license and attribution
- Permissions note
- Size, labels and categories
- Splits with exact counts and split rule
- Preprocessing steps and tool versions
- Annotation process and κ
- Known biases, including:
  - Annotator-built questions
  - English only
  - Single textbook
  - Math under-representation
  - SQuAD Wikipedia and crowdworker artifacts
- Intended use and prohibited use
