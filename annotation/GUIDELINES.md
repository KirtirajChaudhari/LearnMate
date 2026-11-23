# LearnMate Course-Item Annotation Guideline (v1)

**Who:** the two group members only (Member A, Member B). **What:** ~200 questions about the indexed d2l chapters
plus out-of-syllabus questions about held-out chapters. Spec: `research/dataset_and_annotation_plan.md`.

> Items must be written **from the course text**, never from LearnMate outputs. Do not run the system on an item
> before the test set is frozen. Generative AI may only suggest *wordings*; if used, set `"genai_assisted": true`
> and `"human_verified": true` after you check the item against the corpus yourself.

## 1. Find evidence
Browse chunks with:
```bash
python scripts/browse_corpus.py "forget gate"          # BM25 search over chunks -> chunk_id, section, text
python scripts/browse_corpus.py --chunk c_657289ff451a  # show one chunk with provenance
```

## 2. Categories (targets for 200 items)
| Code | Write a question that… | gold_state | ~n |
|---|---|---|---|
| A1 | is fully answered by **one** subsection | sufficient | 70 |
| A2 | needs **two or more** subsections (synthesis) | sufficient | 20 |
| P  | has one part answered by the text and one part **not** covered anywhere in the indexed chapters | partial | 30 |
| U1 | uses course terminology and sounds answerable, but the specific fact is **absent** (e.g. asks for a number, year, variant or comparison the text never gives) | insufficient | 40 |
| U2 | is about a topic of a **held-out** chapter (GANs, recommender systems, RL, GPs, HPO, NLP pretraining, CV) | insufficient | 40 |

Tag `has_math: true` when the answer involves a formula (aim for ~15% overall).
For U1, before saving, search the corpus with 2–3 phrasings to confirm the fact is truly absent.
For U2, record the held-out section in `section_path` (e.g. `Generative Adversarial Networks > Generative Adversarial Networks`).

## 3. Item format (`data/annotations/course_items.jsonl`, one JSON per line)
```json
{"item_id":"LM-A-0001","question":"What does the forget gate of an LSTM control?","category":"A1",
 "gold_state":"sufficient","gold_chunk_ids":["c_657289ff451a"],
 "gold_spans":[{"chunk_id":"c_657289ff451a","char_start":0,"char_end":0}],
 "reference_answer":"Whether to keep the current value of the memory cell or flush it.",
 "required_claims":["forget gate decides how much of the old memory cell state to retain"],
 "uncovered_claims":[], "section_path":"Modern Recurrent Neural Networks > Long Short-Term Memory (LSTM) > Gated Memory Cell",
 "has_math":false,"difficulty":"easy","author":"A","genai_assisted":false,"human_verified":true,"status":"final"}
```
`item_id`: `LM-<author>-<nnnn>`. `gold_chunk_ids`: **all** chunks that support the answer (any one suffices for A1).
For P items: `required_claims` = covered part(s); `uncovered_claims` = the part the course does not cover.

## 4. Independent second label (blind)
```bash
python -m learnmate.annotation blind-sheet --for B --out data/annotations/second_label_B.jsonl
```
Member B fills `label_b.gold_state` and `label_b.gold_chunk_ids` for Member A's items **without** looking at A's labels
(and vice-versa). Merge the `label_b` fields into `course_items.jsonl`, then:
```bash
python -m learnmate.annotation kappa         # target kappa >= 0.70; < 0.60 -> revise guideline for that category
```
Disagreements: discuss, write `adjudication: {"final": ..., "rationale": ...}`; unresolved -> TA/faculty or drop.

## 5. Splits and freeze (end of Week 2)
```bash
python -m learnmate.annotation validate
python -m learnmate.annotation assign-splits   # whole sections -> dev 20% / cal 30% / test 50%
python -m learnmate.annotation freeze          # hashes items, writes data/manifests/course_items_manifest.json
```
After `freeze`, items are read-only. Then write and commit `research/preregistration.md` (template in
`research/preregistration_TEMPLATE.md`) and tag `prereg-v1`.

## 6. Judging system outputs (cal: Week 3 start; test: after pre-registration)
```bash
python -m learnmate.annotation judge-sheet --run results/runs/course-test__clean --out data/annotations/judge_test.jsonl
```
The sheet hides which system produced each answer. For each output set `verdict` to one of:
`correct_supported` · `partially_correct` · `incorrect` · `unsupported` (claims not in the course text, even if true in the world) · `abstained`.
For ≥ 20% of answered outputs also fill `sentence_labels`: `[{"idx":0,"label":"supported|unsupported|contradicted","citation_ok":true}]`.
Do **not** open the `_KEY_DO_NOT_OPEN.jsonl` file. Then merge:
```bash
python -m learnmate.annotation merge --sheet data/annotations/judge_test.jsonl \
   --key data/annotations/judge_test_KEY_DO_NOT_OPEN.jsonl --out data/annotations/judgments_test.jsonl
```
25% of outputs are judged by both members (report kappa). Avoid judging outputs for items you authored where possible.
