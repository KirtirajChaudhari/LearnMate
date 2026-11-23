# Dataset Card: LearnMate (G06), Deliverable C (draft v0.2, 23 Nov 2026)

All numbers below are produced by code and recorded in `data/manifests/`. Fields marked **TBD** are filled at the Week-2 freeze, and only from real data.

## 1. SQuAD 2.0

| Field | Value |
|---|---|
| Source | Hugging Face `rajpurkar/squad_v2` (revision `3ffb306f725f7d2ce8394bc1873b24868140c412`), official parquet conversion of https://rajpurkar.github.io/SQuAD-explorer/ |
| Access date | 23 Nov 2026 |
| License | CC BY-SA 4.0 (dataset card). Cite Rajpurkar, Jia & Liang, ACL 2018 |
| Files (SHA-256) | train `f6da32ff…abf291`, validation `0560174a…dd24cb` |
| Size | train 130,319 Qs (86,821 answerable / 43,498 unanswerable), 442 articles, 19,029 paragraphs. dev 11,873 Qs (5,928 / 5,945), 35 articles, 1,204 paragraphs. Official test set hidden (not used) |
| Labels | Extractive answer spans, or empty (`is_impossible`) |

**Splits.** All splits are made by article title, with seed 2026 (`data/manifests/squad_splits.json`):

| Partition | Source | Articles | Questions (ans / unans) | Paragraphs | Use |
|---|---|---|---|---|---|
| gate-train | train | 420 | 123,116 (82,096 / 41,020) | 18,017 | Gate training pairs, including hard negatives mined only here |
| gate-dev | train (held out) | 22 | 7,203 (4,725 / 2,478) | 1,012 | Gate early stopping and AUROC |
| squad-cal | dev | 12 | 3,678 (1,830 / 1,848) | 360 | Fusion fit (open retrieval over these 360 paragraphs) |
| squad-test | dev | 23 | 8,195 (4,098 / 4,097) | 844 | Secondary test (locked) |

**SQuAD-RAG sets.** For squad-cal and squad-test, 1,500 questions per split are sampled 1:1 (750 answerable / 750 unanswerable). Each question retrieves over all paragraphs of its own partition, not over its oracle paragraph.

**Preprocessing.** None beyond the official answer normalization, which is used only for automatic correctness labels (containment or token-F1 ≥ 0.5). Those labels are audited by humans on 100 items (**TBD**).

**Known biases and limits.**
- Wikipedia domain; crowdworker-written questions.
- Short extractive answers.
- Unanswerable questions are paragraph-local and lexically adversarial.
- In open retrieval, another paragraph can occasionally answer a "no-answer" question. This is sampled in the audit.
- squad-test is in-domain for the gate, so it is secondary evidence only.

## 2. Course corpus (provisional)

| Field | Value |
|---|---|
| Source | `github.com/d2l-ai/d2l-en`, Markdown sources, commit `23d7a5aecceee57d1292c56e90cce307f183bb0a` (16 Mar 2024) |
| Access date | 23 Nov 2026 |
| License | Text CC BY-SA 4.0 (`LICENSE`); sample code modified MIT (`LICENSE-SAMPLECODE`) |
| Attribution | Zhang, Lipton, Li & Smola, *Dive into Deep Learning* (d2l.ai) |
| Approval | **PENDING faculty approval** (handbook §10). This is not yet an "approved course material" |
| Indexed (syllabus) chapters | preliminaries (121 chunks), linear-regression (112), linear-classification (114), multilayer-perceptrons (99), convolutional-neural-networks (77), convolutional-modern (151), recurrent-neural-networks (117), recurrent-modern (122), attention-mechanisms-and-transformers (142), optimization (187) |
| Size | 654 sections → **1,242 chunks**. Mean 267.5 tokens, max 400 (bge tokenizer). 659 chunks contain math, 458 contain code |
| Held-out chapters (not indexed) | generative-adversarial-networks, recommender-systems, reinforcement-learning, gaussian-processes, hyperparameter-optimization, natural-language-processing-pretraining, computer-vision. 355 sections; source of out-of-syllabus items only |
| Chunk store | `data/processed/chunks.jsonl`, SHA-256 `c86ed73f…88263` (`data/manifests/corpus_manifest.json`) |

**Preprocessing** (`learnmate.ingest.d2l_md`, v0.1.0):
- Only PyTorch code cells (`%%tab pytorch|all`) are kept.
- MXNet, TensorFlow and JAX code and prose tabs (`:begin_tab:`) are dropped and flagged.
- Directives are handled as follows: `:label:`/`:eqlabel:` removed; `:numref:` becomes the section title; `:eqref:` becomes the equation label; `:cite*:` removed; figures become "Figure: caption"; `toc` blocks are dropped.
- LaTeX math is kept verbatim.
- Chunks are section-aware: at most 400 tokens, 50-token overlap, never crossing a heading.
- Each chunk's text equals its parent section's text at `[char_start, char_end]`, and a check enforces this.

**Known biases and limits.**
- A single textbook, English only.
- Notation-heavy: verifiers are untested on math, so a math error slice is reported.
- Figures are reduced to their captions.
- Code is kept for one framework only.

## 3. LearnMate course evaluation set

| Field | Value |
|---|---|
| Authors | The two group members (A, B). Independent blind cross-labelling (`annotation/GUIDELINES.md`) |
| Target size | 200 items (floor 150). Categories A1 35%, A2 10%, P 15%, U1 20%, U2 20% |
| Splits | Assigned by whole section: dev 20% / cal 30% / test 50% |
| Agreement | Cohen's κ on gold state, plus span-overlap F1: **TBD** |
| Final counts | **TBD** at freeze (`data/manifests/course_items_manifest.json`) |
| License | CC BY-SA 4.0 (ShareAlike: items quote d2l) |
| Gen-AI use | Allowed only for drafting wording; disclosed per item (`genai_assisted`) and human-verified |
| Biases | Questions are written by the people who built the system (mitigated by blind cross-labelling and judging blinded to system identity); student-level difficulty is assumed |
