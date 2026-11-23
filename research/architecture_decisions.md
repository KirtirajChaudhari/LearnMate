# Architecture Decision Records (ADR)

Format: Context → Decision → Alternatives → Consequences.
Status is **Accepted** unless marked otherwise.
Evidence references point to `verified_sources_and_corrections.md` (VS) and `reconciliation_report.md` (RR).

---

### ADR-001: Single-process Python package
- **Context:** Two students, 3–4 weeks, a free Colab GPU, a single-user demo. Evaluation is the priority.
- **Decision:** Build a single-process `learnmate` package, separate evaluation notebooks and a Streamlit app.
- **Alternatives:** FastAPI microservices. Agent frameworks (LangChain/LlamaIndex). Forking Kotaemon or Verba (Verba is archived).
- **Consequences:**
  - The demo and the evaluation share one code path.
  - The design does not scale to many users.
  - Microservices are deferred.

### ADR-002: Provisional corpus = d2l Markdown at a pinned commit
- **Context:**
  - The handbook requires "approved course materials", and faculty have not supplied any yet.
  - d2l text is CC BY-SA 4.0 and its code is MIT-style (VS §3).
- **Decision:**
  - Ingest a chapter subset of `d2l-ai/d2l-en` at a pinned commit.
  - Label it "provisional, pending faculty approval" in every artifact.
  - Chapters left out of the index supply the out-of-syllabus questions.
- **Alternatives:** Wait for faculty material, which blocks Weeks 1–2. OpenStax or MIT OCW (licenses vary; OCW is often NC).
- **Consequences:**
  - ShareAlike applies: released course items that quote d2l must be CC BY-SA 4.0. This is compatible with SQuAD's license.
  - If faculty supply other material, the course items must be re-authored. The code and the research question do not change.

### ADR-003: Generator = `Qwen/Qwen3-4B-Instruct-2507`, greedy decoding, frozen runtime
- **Context:** Conflict A (RR §3.A).
- **Decision:**
  - Use HF transformers in fp16 on GPU.
  - If the M0 smoke test shows instability or OOM, fall back to NF4.
  - Use the same runtime for all evaluation.
  - GGUF Q4 is for the CPU demo only.
- **Alternatives:**
  - Qwen2.5-7B-Instruct: about 1.9× the compute; optional swap A6.
  - Qwen3-4B: thinking is on by default.
  - Phi-4-mini-instruct: MIT; kept as the fallback.
- **Consequences:**
  - Requires transformers ≥ 4.51.
  - Citation-format compliance must be monitored (a format-compliance rate is logged).

### ADR-004: Intervention = trained gate + claim verification + calibrated fusion
- **Context:** Conflict C. The handbook requires a deep-learning component, and SQuAD 2.0 is a named dataset.
- **Decision:**
  - Fine-tune DeBERTa-v3-base on SQuAD 2.0 plus retrieval hard negatives.
  - Add MiniCheck support features and NLI contradiction features.
  - Fuse everything with a logistic regression of ≤ 9 features.
  - Isolate the two halves with ablations A1 and A2.
- **Alternatives:**
  - Post-generation only (Gemini's ES-CA): no trained network.
  - Gate only: does not detect hallucination when the context is sufficient.
  - LoRA or DPO on the generator: infeasible in 3–4 weeks.
- **Consequences:**
  - One training notebook (estimated ≤ 1.5 T4-hours; to be measured).
  - Risk: SQuAD→course transfer. This is measured, and A5 is the untrained control.

### ADR-005: Decision verifier = MiniCheck-Flan-T5-Large; contradiction = DeBERTa-v3-base NLI; evaluator = LettuceDetect-large + humans
- **Context:**
  - Conflict B.
  - The verifier used for decisions must not be the sole judge of correctness.
- **Decision:** As in the title.
  - MiniCheck is installed from git at a pinned commit, because the provenance of the PyPI `minicheck` package is unverified.
- **Alternatives:**
  - LettuceDetect as the decision verifier: it scores against the whole context, so it cannot attribute a claim to a specific citation.
  - NLI-only verification: over-abstains (GRAB-RAG).
  - Bespoke-MiniCheck-7B: CC BY-NC and too large.
- **Consequences:**
  - Three verifier-family models are needed, but never all at once during experiments.
  - The agreement of LettuceDetect with human labels becomes a reported result.

### ADR-006: Retrieval = BM25 + bge-base-en-v1.5 (FAISS flat) → RRF(k=60) → ms-marco-MiniLM-L-6-v2 top-5; B1 is dense-only
- **Context:** Both reports agree on hybrid retrieval with RRF.
- **Decision:** As in the title.
  - Use `IndexFlatIP` (exact search) because the corpus is under 100k chunks.
- **Alternatives:** bge-small (CPU fallback). Qwen3-Embedding-0.6B (optional ablation). bge-reranker-base. Chroma.
- **Consequences:** Retrieval is held fixed between B2 and G, so ΔAURC isolates the decision mechanism.

### ADR-007: Threshold selection by utility; no statistical guarantee claimed
- **Context:**
  - Gemini proposes Clopper–Pearson UCB risk control.
  - The calibration and test splits come from different sections and partly from a different domain (SQuAD vs course), so they are not exchangeable.
  - A threshold chosen by search needs multiplicity control (VS CR-05).
- **Decision:**
  - Set τ = argmax U(λ=2) on course-cal, and use the same rule for every baseline threshold.
  - Report λ ∈ {1, 2, 4}.
  - Report Clopper–Pearson intervals only as descriptive CIs at the frozen τ.
- **Alternatives:** Learn-then-Test fixed-sequence testing; kept as an optional extension. Split-conformal risk control.
- **Consequences:**
  - Claims are limited to empirical comparisons.
  - The no-guarantee stance is stated in the paper.

### ADR-008: Calibration pooling = LR weights on SQuAD-cal-RAG, Platt recalibration on course-cal
- **Context:** About 60 course-cal items cannot support fitting 9 weights.
- **Decision:** As in the title.
  - Ablation: fit the LR on course-cal only, with strong L2 regularization.
- **Consequences:**
  - SQuAD-cal-RAG needs generations and automatic correctness labels: gold answer containment or token-F1 ≥ 0.5, with unanswerable items treated as errors whenever answered.
  - A 100-item human audit checks the accuracy of those automatic labels.

### ADR-009: Evaluation is staged and cached; one model on the GPU at a time
- **Context:** No co-hosting has been measured, Colab sessions disconnect, and this container has no GPU.
- **Decision:**
  - Each pipeline stage writes JSONL keyed by item, configuration and model revision, and can resume after an interruption.
  - Stages unload their model before the next stage runs.
- **Consequences:**
  - Peak VRAM ≈ the largest single model.
  - Calibration, statistics and plots re-run on CPU in minutes.

### ADR-010: Dependency pinning around the transformers 5.x transition
- **Context:**
  - transformers 5.24.0 is current.
  - sentence-transformers 6.x requires transformers ≥ 5.
  - The MiniCheck and LettuceDetect code was written against 4.x.
  - The Phi-4-mini card pins 4.49.
- **Decision:**
  - In M0, try the newest compatible set first.
  - If MiniCheck, LettuceDetect or DeBERTa tokenization breaks, pin `transformers>=4.51,<5` with a matching `sentence-transformers<6`.
  - Freeze the result in `requirements.lock`, with Python 3.11 on Colab.
- **Consequences:**
  - M0 includes an import-and-forward smoke test for every model.
  - The lockfile is committed.

### ADR-011: UI = Streamlit; uncalibrated scores never shown as probabilities
- **Decision:**
  - The UI shows a state badge, verified citations and a "related, not supporting" panel.
  - A probability is shown only after ECE has been reported.
- **Alternatives:** Gradio, which is equivalent; Streamlit is chosen for consistency.

### ADR-012: Fail-closed and typed abstentions
- **Decision:** Any exception in retrieval, gating, generation, verification or citation validation produces a `system_error` abstention. The system never shows an unverified answer.
- **Consequence:** `system_error` counts as an abstention in coverage and is reported separately, so that crashes cannot inflate safety metrics.

### ADR-013: Out-of-syllabus items come from un-indexed d2l chapters
- **Decision:** Hold out whole chapters from the index. Questions written about them are true in the world but not covered by the course, which makes them implicit-truth traps.
- **Consequence:** The ground truth for "should abstain" is verifiable, because the answer exists in the held-out text but not in the index.

### ADR-014 (Proposed, needs instructor): coverage-loss margin m = 10 pp, λ = 2
- **Status:** Proposed. Must be confirmed with the instructor in Week 1, then frozen in the pre-registration commit.
