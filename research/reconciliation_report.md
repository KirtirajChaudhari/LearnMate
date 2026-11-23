# LearnMate (G06) — Research Reconciliation Report

**Status:** Phase I reconciliation complete · **Date:** 23 Nov 2026 · **Scope:** Stage 1 of the Phase II handoff

**Inputs (preserved unchanged in `research/inputs/`, SHA-256 in `SHA256SUMS`):**

| Code | Document | Role |
|---|---|---|
| **HB** | `CCA2_LCA3_MTech_Deep_Learning_Research_Challenges.pdf` | Authoritative for assignment requirements |
| **GEM** | `LearnMate_Grounded_AI_Tutor_Research.docx` (Gemini dossier, "LearnMate ES-CA") | Research input, not authoritative |
| **MDR** | `LearnMate_Calibrated_Evidence-Sufficiency_Gating_...md` (coding-agent report, "calibrated fused gate") | Research input, not authoritative |

Decision rule used throughout: **HB decides compliance. Verified primary evidence plus engineering feasibility decide implementation.** Neither report is treated as correct by default. Verification details and the correction audit trail are in `verified_sources_and_corrections.md`.

---

## 1. Executive comparison

The two reports agree on most of the system: a local RAG tutor; hybrid BM25 + dense retrieval fused with RRF; cross-encoder reranking; a small open-weight instruct LLM; a calibrated answer/abstain gate fitted on a disjoint calibration split; AURC/coverage-aware metrics; stress tests that remove gold evidence; human-audited factuality; and an honest "incremental, not novel" framing. They differ on five substantive points (Conflicts A–E below) and on citation hygiene.

| Dimension | GEM | MDR | Overall assessment |
|---|---|---|---|
| Research framing | Post-generation "dual evidence auditor" + logistic gate + Clopper–Pearson risk bound | **Trained** pre-generation answerability gate + claim-level verification + calibrated fusion | MDR's intervention contains the handbook's required deep-learning component and actually uses SQuAD 2.0 for training. GEM uses SQuAD only for evaluation and trains nothing |
| Generator | Qwen2.5-7B-Instruct (4-bit) | Qwen3-4B (4-bit) | Neither choice is exact. Adopt **Qwen3-4B-Instruct-2507**, the non-thinking-only checkpoint (Conflict A) |
| Verifier | LettuceDetect-large + 3-class DeBERTa NLI | MiniCheck (or DeBERTa NLI) | GEM's main reason for rejecting MiniCheck (licensing) is **contradicted** by primary sources (Conflict B) |
| Statistical guarantees | Promises finite-sample Clopper–Pearson risk control | Optional conformal risk control, with an exchangeability caveat | GEM's guarantee does not survive this design's distribution shift and threshold search. No guarantee will be claimed |
| Course corpus | Waits for faculty files; open DL notes only as a "stub" | d2l.ai Markdown (CC BY-SA 4.0) as the default | Prepare d2l now as a **provisional** corpus and request approval (Conflict D) |
| Literature hygiene | Rich, but with extraction artifacts (`[span_N](start_span)`), one broken table, at least one mislabeled source, unverifiable anthology IDs | Explicit read-level tags (FT/AB/2nd); fewer artifacts; some "[not re-verified]" items | MDR is more auditable. GEM contributes valuable sources MDR lacks (RAGTruth, LettuceDetect, Wallat et al., Yu et al. SIGCSE 2025) |
| Factual data errors | SQuAD 2.0 dev = "78 articles" (**wrong**: 35) | SQuAD counts correct (secondary at the time; now programmatically verified) | Use the verified counts (§4.D) |

---

## 2. Research Reconciliation Matrix

Legend: ✅ agreement · ⚠️ partial conflict · ❌ direct conflict · **Res.** = resolution adopted in the frozen specification.

| # | Topic | GEM recommendation | MDR recommendation | Evidence / conflict | Technical assessment | Res. |
|---|---|---|---|---|---|---|
| 1 | Central problem | Unsupported answering when retrieval is relevant but insufficient; prompt and score thresholds miscalibrate | Same, plus misleading and contradictory evidence | ✅ Both rely on Joren et al. (ICLR 2025) | Sound and well motivated | Keep. Relevance ≠ sufficiency ≠ correctness is stated explicitly |
| 2 | Hypothesis | ES-CA reduces AURC and UAR vs B1 and B2 on SQuAD-RAG **and** course test; p<0.05 | Fused gate reduces AURC and unsupported rate at matched coverage vs B3 (score threshold); paired-bootstrap CIs; coverage-loss margin; pre-registered | ⚠️ GEM's H1 is a conjunction across two datasets and five metrics, which makes it hard to falsify cleanly | MDR's version is sharper: one primary comparison and a margin that blocks the "always abstain" win | MDR form with one primary endpoint (ΔAURC on the course test vs the strong baseline). See `final_research_problem.md` |
| 3 | SOTA findings | Context lowers abstention; scale and reasoning don't fix it; CE > NLI for passage weighting; encoders ≈ GPT-4 for verification | Same core, plus GRAB-RAG (prompt abstention fails under misleading context; NLI over-abstains) | ✅ Complementary | GEM's Seo & Jang claim concerns *document weighting*, not abstention. Its use is limited to justifying "CE for ranking, NLI not for ranking" | Merge both. GRAB-RAG (now AACL 2026) motivates the misleading-evidence stress test |
| 4 | Literature accuracy | Many verified DOIs, but extraction artifacts, a mislabeled "COLM 2026" source, Seo & Jang anthology ID/pages unverifiable, AbstentionBench venue wrong | Read levels tagged; a few items unverified | See `verified_sources_and_corrections.md` | MDR more reliable; GEM needs a correction pass | 10-paper matrix rebuilt from verified items |
| 5 | Course dataset | 180–240 Qs, 6 slices incl. 10% conflicting; split by module into Cal (60–80) / Test (120–160); no dev split | 150–300 (target ~200); split by section 30% dev / 20% cal / 50% test; contradictions only in stress index | ⚠️ Sizes overlap. GEM has no dev split, so prompts and chunking would be tuned on cal or test | A dev split is necessary. Natural contradictions do not exist in an approved corpus, so they belong in a constructed stress set | **200 items (floor 150), split by section: dev 40 / cal 60 / test 100.** Contradiction only in stress set S4 |
| 6 | Ingestion | Docling for PDF/DOCX/PPTX | d2l Markdown parser primary; Docling for PDFs | ⚠️ GEM assumes PDFs | Markdown avoids parse-error confounds. Docling (MIT, verified) remains the path for faculty PDFs | Markdown parser = MVP; Docling = Should (for faculty files) |
| 7 | Chunking & provenance | Structure-aware, 300–450 tok, 50 overlap; slide-atomic; SHA-256 | Section-aware 256–512 tok, never cross headings; full provenance fields | ✅ Same idea | — | Section-aware, ≤400 tokens, 50 overlap, never crossing a heading; provenance schema merged |
| 8 | Embeddings | bge-base-en-v1.5 (MIT) | bge-small-en-v1.5 → Qwen3-Embedding-0.6B upgrade | ⚠️ | Retrieval is not the research variable; a stronger, still cheap default makes baselines fairer. Both licenses verified | **bge-base-en-v1.5**; bge-small = CPU fallback; embedder swap = optional ablation |
| 9 | Sparse/dense/hybrid | BM25 + FAISS RRF k=60, top-20 each | Same | ✅ | — | Adopt |
| 10 | Reranker | ms-marco-MiniLM-L-6-v2 (Apache-2.0) | bge-reranker-base or ms-marco-MiniLM | ⚠️ minor | ms-marco-MiniLM: 22.7M params, Apache-2.0 verified, fast | **cross-encoder/ms-marco-MiniLM-L-6-v2** |
| 11 | Generator & quantization | Qwen2.5-7B-Instruct NF4; Phi-4-mini ablation | Qwen3-4B Q4_K_M via llama.cpp | ❌ **Conflict A** | See §3.A | **Qwen/Qwen3-4B-Instruct-2507** |
| 12 | Pre-generation sufficiency | CE top-1 score and margin as features (no training) | Trained DeBERTa-v3 answerability cross-encoder on SQuAD 2.0 + retrieval hard negatives | ❌ **Conflict C** | See §3.C | **Trained gate adopted** (the DL component) |
| 13 | Post-generation verification | LettuceDetect-large (span) + DeBERTa-NLI (per citation, contradiction) | MiniCheck sentence-vs-cited-passage support (+ pairwise NLI contradiction) | ❌ **Conflict B** | See §3.B | **MiniCheck-Flan-T5-Large** for support; **DeBERTa-v3-base NLI** for contradiction; **LettuceDetect** moved to the evaluator role |
| 14 | Contradiction detection | 3-class NLI, top-3 pairwise + per citation | Pairwise NLI among top-3 | ✅ | — | Adopt pairwise top-3 NLI (both directions) |
| 15 | Calibration | L2 logistic on D_cal | Logistic + isotonic/temperature; SQuAD-cal + course-cal | ⚠️ How to pool domains | ~60 course-cal items cannot support a 9-feature fit | Fit LR weights on SQuAD-cal-RAG; **Platt-recalibrate on course-cal**; ablate course-only fitting |
| 16 | Threshold selection | Out-of-fold Clopper–Pearson UCB at α∈{0.05,0.10} | Maximize utility U(λ) at pre-registered λ or target risk; conformal optional | ❌ Guarantee validity | CP-UCB is valid only for a fixed threshold, or with multiplicity control (e.g., Learn-then-Test), and under exchangeability. Section-split course data and SQuAD→course shift break exchangeability | **τ = argmax U(λ=2) on cal** (λ∈{1,2,4} reported). CP intervals only as *descriptive* CIs on test. **No guarantee claimed** |
| 17 | Baselines | B0 extractive DeBERTa-SQuAD2; B1 dense + prompt; B2 hybrid+CE + calibrated CE threshold | B1 extractive; B2 dense+prompt; B3 hybrid+rerank+score threshold | ✅ Identical set, different names | — | **B0 (reference), B1 prompt-only, B2 strong CE-threshold** (GEM naming) |
| 18 | Stress tests | Withheld gold; distractors; out-of-curriculum; conflicts | Missing; distractor; misleading (entity/number swap); contradictory; out-of-syllabus; paraphrase/SQuAD | ✅ MDR adds *misleading* (GRAB-RAG) | Out-of-syllabus is better as a clean-test category than a stress test | **S1 withheld gold (mandatory), S2 distractors, S3 misleading edit, S4 contradiction pair**; out-of-syllabus = test category |
| 19 | Ablations | No reranker; no verifier; no calibration; Phi-4-mini swap | −NLI; −answerability; −calibration; −reranker; −hard negatives; embedder swap | ⚠️ | The ablation must isolate the two halves of the intervention | **A1 −verifier, A2 −gate (≈ GEM's ES-CA core), A3 −calibration, A4 −hard negatives, A5 untrained gate**; reranker / generator swaps optional |
| 20 | Metrics | AURC, UAR, Risk@cov, Cit-P/R/F1, ECE, human factuality, latency, VRAM | AURC, HwSA, FAC, U(λ), ECE/Brier, Cit-P/R, human audit, latency, VRAM | ✅ | — | Union. **Primary = ΔAURC (course test, G vs B2)** |
| 21 | Evaluator independence | "Never use LettuceDetect to grade ES-CA", but LettuceDetect is its decision component | Human audit primary | ✅ Principle shared | Adopted design: decision verifier = MiniCheck; human = primary judge; LettuceDetect = independent secondary auto-evaluator (its agreement with humans reported) | Adopt |
| 22 | Compute | Co-host everything on T4 (~10 GB est.) | Fits T4; measure | ⚠️ | This container has **no GPU** (4 CPU, 15 GB RAM). Experiments are staged (generate → unload → verify), so co-hosting is needed only for the demo | Tiered hardware plan (`final_architecture.md` §5) |
| 23 | Interface | Gradio or Streamlit | Streamlit | ✅ | — | **Streamlit**, single process |
| 24 | Reproducibility | Seeds, greedy decoding, JSONL caching, hash manifests | Same + pre-registration commit | ✅ | — | Adopt both, plus a dependency lockfile (transformers is now 5.x; see ADR-010) |
| 25 | Deliverables A–H | Full checklist | Milestones M1–M8 | ✅ | — | `requirements_traceability.md` |

---

## 3. Conflict analyses

### Conflict A: Generator (Qwen2.5-7B-Instruct vs Qwen3-4B)

| Criterion | Qwen2.5-7B-Instruct | Qwen3-4B (hybrid) | **Qwen3-4B-Instruct-2507** |
|---|---|---|---|
| License (HF card, verified) | Apache-2.0, ungated | Apache-2.0, ungated | Apache-2.0, ungated |
| Params (safetensors, verified) | 7.62B | 4.02B | 4.02B |
| Thinking behaviour | None | **Thinking on by default** (`enable_thinking=True`) | **Non-thinking only**; no `<think>` blocks (card) |
| Runtime requirement | transformers ≥4.37 | transformers ≥4.51 | transformers ≥4.51 (card) |
| fp16 weight memory (est. = params × 2 B) | ~15.2 GB, too large for a T4 without quantization | ~8.0 GB | ~8.0 GB, fits a T4 unquantized |
| 4-bit weight memory (est.) | ~4.5–5.5 GB | ~2.5–3 GB | ~2.5–3 GB |
| Relative decode cost | ~1.9× the 4B model (parameter ratio) | 1× | 1× |
| Evidence for grounded/abstention behaviour | Failure evidence exists: GRAB-RAG (answers misleading context under abstention prompts); used in VeriCite | None specific | None specific (vendor instruction-following benchmarks only) |

**Assessment.** Bigger is not automatically better here, for three reasons. (1) The research variable is the *decision gate*, not generator quality. B1, B2 and G share one generator, so any reasonable instruct model gives a fair test. (2) Generator throughput limits the experimental budget: roughly 3 × (≈200 course items + stress copies + ~1–2k SQuAD-RAG items). On a free T4 the 4B model roughly halves generation time, and it can run *unquantized* in fp16, which removes a quantization confound. (3) AbstentionBench (NeurIPS 2025 D&B) reports that reasoning fine-tuning degrades abstention by 24% on average. The checkpoint MDR literally names, `Qwen/Qwen3-4B`, thinks by default. That is a real defect in MDR's recommendation. The **2507 Instruct** checkpoint is non-thinking by construction.

**Resolution.** Primary generator: **`Qwen/Qwen3-4B-Instruct-2507`**, greedy decoding, run through HF transformers in fp16 on GPU, with bitsandbytes NF4 as a fallback decided by an M0 smoke test. **Optional generator-swap ablation:** `Qwen/Qwen2.5-7B-Instruct` (NF4). It is the model GRAB-RAG studied, so it allows a cross-model robustness check. `microsoft/Phi-4-mini-instruct` (MIT, verified) is the fallback if the Qwen weights become inaccessible. One runtime is frozen for all evaluation runs. GGUF/llama.cpp (`unsloth/Qwen3-4B-Instruct-2507-GGUF`, Apache-2.0) is used **only** for a CPU demo, and results from it are never mixed with GPU results.

### Conflict B: Evidence verification (LettuceDetect + NLI vs MiniCheck/NLI)

| Criterion | LettuceDetect-large-v1 | MiniCheck-Flan-T5-Large | DeBERTa-v3-base-mnli-fever-anli |
|---|---|---|---|
| Weights license (HF, verified) | MIT | **MIT** | MIT |
| Code license (GitHub, verified) | MIT | **Apache-2.0** | n/a (transformers) |
| GEM's licensing claim | — | "academic/non-permissive" — **contradicted**. Only `Bespoke-MiniCheck-7B` is CC BY-NC 4.0 | — |
| Params | 396M (ModernBERT-large) | 770M | 184M |
| Granularity | Token/span over whole [context, question, answer] | Sentence vs document (chunked, max over chunks) | Premise–hypothesis 3-class |
| Context window | 8,192 tokens (card) | Chunked internally | 512 tokens |
| Native per-citation scoring | No (scores against the full context) | **Yes** (sentence vs its cited passage) | Yes |
| Contradiction class | No | No | **Yes** |
| Evaluation evidence | RAGTruth test example-F1 79.22% (card; single benchmark: news/QA/data-to-text) | LLM-AggreFact (11 human-labeled datasets), ≈GPT-4 balanced accuracy at ~400× lower cost (EMNLP 2024) | MNLI/FEVER/ANLI. GRAB-RAG: NLI-based policy over-abstains (31–51% false abstention) |
| Domain transfer to technical coursework | Untested | Untested; third-party report of weak math performance concerns the different *Bespoke-7B* model | Untested |
| Install | `lettucedetect` 0.2.3 (PyPI, MIT, requires transformers ≥4.48.3) | Git install per card. The PyPI `minicheck` 0.4.0 has no project URL, so its provenance is unverified. **Pin a git commit** | transformers |

**Assessment.** For LearnMate the verifier must answer: "Is *this sentence* supported by *the passage it cites*?" That question defines citation precision/recall and the supported-vs-cited distinction the brief requires. MiniCheck is built for exactly this task and has the broadest independent grounding evaluation. LettuceDetect judges against the whole retrieved context, so it cannot tell a correct citation from a wrong one. Its evidence is a single benchmark. Contradiction still needs a 3-class NLI model.

**Resolution.** *Decision-time verifier:* **MiniCheck-Flan-T5-Large** (sentence × cited passages; max over cited passages) plus **DeBERTa-v3-base-mnli-fever-anli** (pairwise passage contradiction, and sentence-vs-cited contradiction). *Independent secondary auto-evaluator:* **LettuceDetect-large**. It never feeds a decision. Its agreement with the human audit is reported. This satisfies the requirement that the decision verifier must not also be the sole evaluator, and it keeps GEM's strongest component in a role where it adds value.

### Conflict C: Research intervention (pre-generation trained gate vs post-generation calibrated verification)

| Option | DL training? | Uses SQuAD 2.0 meaningfully? | Effort | Isolable? | Risk |
|---|---|---|---|---|---|
| 1. Trained pre-generation sufficiency classifier only | Yes (DeBERTa-v3-base fine-tune, ~1 T4-hour, to be measured) | Yes (training data) | Medium | Yes | SQuAD→course transfer; cannot see generator hallucination under sufficient context |
| 2. Post-generation verification + calibrated abstention only (GEM) | **No.** Only logistic regression on frozen models | Evaluation only | Low–Medium | Yes | Weak "deep learning component" for a DL course; NLI-style verifiers over-abstain (GRAB-RAG) |
| 3. **Limited combination** (MDR) | Yes | Yes | Medium (+~2–3 days over option 2) | **Yes, by A1/A2 ablations** | Two signal families to debug |

**Assessment.** The handbook (§3 Task 4, §5 G06) asks for a justified change tested with an ablation, in a *Deep Learning Networks* course, with SQuAD 2.0 as a named dataset. Option 2 meets the letter of "evidence agreement" but contains no trained network. The literature shows the two signals catch different failures. Pre-generation sufficiency catches "relevant but missing the decisive fact" (Joren et al.). Post-generation support catches hallucination under sufficient context and implicit-truth leaks (RAGTruth taxonomy). Neither catches misleading-but-sufficient evidence well (GRAB-RAG). The extra cost of option 3 is one fine-tuning notebook. The two ablations A1 (−verifier) and A2 (−gate) isolate each half, and A2 is approximately GEM's ES-CA. The combination therefore also tests experimentally which report's intervention carries the effect.

**Resolution: Option 3, kept deliberately limited.** One trained cross-encoder gate (no LLM training, no LoRA). One off-the-shelf support verifier. One NLI model for contradiction. A fusion layer that is a logistic regression with ≤9 features. Answer-level decisions are the primary experiment. Sentence-level pruning for partial answers is a product feature evaluated secondarily, so it cannot confound AURC.

### Conflict D: Dataset and course corpus

* **Available now (openly licensed, verified):** SQuAD 2.0 (CC BY-SA 4.0; 130,319 train / 11,873 dev, programmatically counted). *Dive into Deep Learning* `d2l-ai/d2l-en`: text CC BY-SA 4.0, sample code modified MIT (MIT-0) — both verified from the LICENSE files on GitHub.
* **Needs explicit faculty approval:** (a) whether a d2l chapter subset is an acceptable "approved course material" for G06. The handbook says "approved course materials", and §10 of HB has a "Dataset access and license verified: Yes/No/Pending" sign-off. (b) Any institution-owned slides or notes, plus redistribution permission. (c) The coverage-loss margin and λ.
* **Resolution.** Build everything on a pinned d2l commit labelled **"provisional public course corpus — pending faculty approval"** in every artifact. The ingestion code supports Markdown (d2l) and PDF/DOCX/PPTX via Docling, so faculty files can replace or join it. The research question is unchanged if the corpus changes. Only the course item set must be re-authored for the new corpus.

### Conflict E: Runtime and deployment

* GEM assumes all models are co-hosted on a 16 GB T4 (~10 GB estimated). MDR assumes llama.cpp Q4 on a T4. Neither measured anything.
* **This environment has no GPU** (4 vCPU, 15 GB RAM). Colab's free T4 exposes ~15 GB usable VRAM, and availability is not guaranteed.
* **Resolution.** (1) Evaluation is **staged**: each model is loaded, run over all items, its outputs cached to JSONL, then unloaded. Peak VRAM ≈ the largest single model, so nothing is co-hosted during experiments. (2) Only the demo co-hosts models. Estimated fp16 total for generator + gate + MiniCheck + NLI + embedder + CE is ≈11 GB on a T4; it must be measured in M0. NF4 generator fallback ≈ 6 GB. (3) CPU-only fallback: GGUF Q4 generator for the demo and a reduced course-only evaluation (§5 of `final_architecture.md`). (4) A single-process Streamlit app, with no services, agents or paid APIs.

---

## 4. Verified quantitative facts that change the plan

| Fact | Source of verification | Effect |
|---|---|---|
| SQuAD 2.0 train: 130,319 Qs (86,821 ans / 43,498 unans), 442 articles, 19,029 paragraphs | Counted from HF `rajpurkar/squad_v2` parquet | Gate training pool |
| SQuAD 2.0 dev: 11,873 Qs (5,928 / 5,945), **35 articles**, 1,204 paragraphs | Counted from HF parquet | GEM's "78 articles → 30/48 split" is impossible. Gate-dev is taken from **held-out train articles**; dev articles go to SQuAD-cal (12) / SQuAD-test (23) |
| Qwen3-4B (base name) thinks by default; 2507-Instruct is non-thinking only; transformers ≥4.51 | HF model cards | Generator ID choice |
| MiniCheck code Apache-2.0, FT5/DeBERTa/RoBERTa weights MIT; Bespoke-MiniCheck-7B CC BY-NC 4.0 | GitHub LICENSE, HF cards | Verifier choice |
| transformers latest = 5.24.0; sentence-transformers 6.x requires transformers ≥5; Phi-4-mini card pins 4.49 | PyPI, HF cards | Pin the stack to a tested lockfile (ADR-010) |

---

## 5. What each report contributes to the final plan

* **From MDR:** trained SQuAD 2.0 gate; dev/cal/test split with a dev split; pre-registration; utility U(λ); FAC/HwSA; misleading-evidence stress (GRAB-RAG); the "retrieved ≠ supporting" invariant; fail-closed principle; d2l corpus; honest novelty framing; read-level tagging.
* **From GEM:** bge-base and ms-marco-MiniLM defaults; deterministic caching discipline; evaluator-independence principle; withheld-gold stress design with `exclude_chunk_ids`; citation-correctness vs citation-faithfulness distinction (Wallat et al.); RAGTruth hallucination taxonomy for error analysis; LettuceDetect (as evaluator); Yu et al. (SIGCSE 2025) local-SLM tutoring evidence; detailed rubric mapping.
* **Rejected from both:** GEM's finite-sample guarantee claims; GEM's "78 dev articles" split; MDR's `Qwen3-4B` thinking-default checkpoint; llama.cpp as the *evaluation* runtime (GPU transformers is simpler on Colab, and GGUF is kept for the demo); any multi-pass LLM regeneration (VeriCite-style) in the core.
