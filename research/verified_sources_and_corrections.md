# Verified Sources and Corrections (Audit Trail)

**Verification date:** 23 Nov 2026. **Method:** targeted checks of claims that change implementation, not a repeat of the literature search.

**Channels used:**
- Hugging Face Hub API and model cards (`huggingface.co/api/models/...`, `raw/main/README.md`)
- GitHub raw LICENSE and README files
- PyPI JSON API
- Programmatic counts on the `rajpurkar/squad_v2` parquet files
- Web search, for paper existence and venue

**Access limits:** arxiv.org, aclanthology.org and openreview.net could not be reached directly from this container. Paper-level claims checked only by web search are marked *partially verified* when the exact numbers could not be read from the primary PDF.

**Status codes:**

| Code | Meaning |
|---|---|
| **V** | Verified from a primary source |
| **PV** | Partially verified: the source exists, but the specific number or venue was not read from the primary text |
| **C** | Contradicted |
| **U** | Unresolved |

---

## 1. Models: identifiers, licenses, availability

| HF ID | License (card) | Gated | Params | Notes | Status |
|---|---|---|---|---|---|
| `Qwen/Qwen3-4B-Instruct-2507` | apache-2.0 | no | 4.02B | Non-thinking only, no `<think>`; transformers ≥4.51; 262,144-token native context | V |
| `Qwen/Qwen3-4B` | apache-2.0 | no | 4.02B | `enable_thinking=True` by default | V |
| `Qwen/Qwen2.5-7B-Instruct` | apache-2.0 | no | 7.62B | — | V |
| `Qwen/Qwen2.5-3B-Instruct` | other (qwen-research) | no | 3.09B | Not permissive; excluded | V |
| `microsoft/Phi-4-mini-instruct` | mit | no | 3.84B | 128K context; card pins transformers 4.49.0 | V |
| `unsloth/Qwen3-4B-Instruct-2507-GGUF` | apache-2.0 | no | — | CPU demo runtime only. `Qwen/Qwen3-4B-Instruct-2507-GGUF` returned 401 | V |
| `BAAI/bge-base-en-v1.5` | mit | no | 109M | — | V |
| `BAAI/bge-small-en-v1.5` | mit | no | 33M | — | V |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | apache-2.0 | no | 22.7M | Alias `...L6-v2` also resolves | V |
| `BAAI/bge-reranker-base` | mit | no | 278M | MDR said "verify license" → MIT | V |
| `microsoft/deberta-v3-base` | mit | no | ~184M | Gate backbone | V |
| `deepset/deberta-v3-base-squad2` | cc-by-4.0 | no | 184M | B0 extractive reference; attribution required | V |
| `lytang/MiniCheck-Flan-T5-Large` | mit | no | 770M | Code repo Liyan06/MiniCheck is Apache-2.0 | V |
| `lytang/MiniCheck-DeBERTa-v3-Large`, `...-RoBERTa-Large` | mit | no | ~0.4B | Lighter fallbacks | V |
| `bespokelabs/Bespoke-MiniCheck-7B` | CC BY-NC 4.0 (README) | no | 7.7B | Excluded | V |
| `KRLabsOrg/lettucedect-large-modernbert-en-v1` | mit | no | 396M | 8,192 context; RAGTruth F1 79.22% (card). Hub metadata lists `ModernBERT-base` as base despite the large size: metadata inconsistency, no effect on use | V |
| `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` | mit | no | 184M | 3-class NLI | V |
| `vectara/hallucination_evaluation_model` | apache-2.0 | no | 110M | Optional CPU checker | V |
| `Qwen/Qwen3-Embedding-0.6B` | apache-2.0 | no | 596M | Optional embedder ablation | V |
| `google/embeddinggemma-300m` | gemma (gated) | manual | 303M | Excluded (gated) | V |

## 2. Packages and code licenses

| Package / repo | Version (PyPI, 23 Nov 2026) | License | Notes | Status |
|---|---|---|---|---|
| transformers | 5.24.0 | Apache-2.0 | **Major version 5.** Both reports assume 4.x APIs → pin and lock in M0 | V |
| sentence-transformers | 6.3.0 | Apache-2.0 | Requires `transformers>=5,<6`. Pin an older major if the stack needs transformers 4.x | V |
| lettucedetect | 0.2.3 | MIT | Requires transformers ≥4.48.3, torch ≥2.6, numpy ≥2.2.2 | V |
| minicheck (PyPI) | 0.4.0 | MIT (declared) | **No project URL on PyPI; provenance unverified** → install from the GitHub repo at a pinned commit, as the HF card instructs | U |
| Liyan06/MiniCheck (GitHub) | — | Apache-2.0 | requirements: torch, transformers, datasets, nltk, pandas, numpy, openai | V |
| docling | 2.152.0 | MIT | Python ≥3.10 | V |
| faiss-cpu 1.16.0 (MIT), rank-bm25 0.2.2 (Apache-2.0), streamlit 1.67.0 (Apache-2.0), bitsandbytes 0.50.2 (MIT), llama-cpp-python 0.3.38 (MIT), scikit-learn 1.9.1 (BSD-3), torch 2.15.0 | — | — | Most require Python ≥3.11 | V |
| facebookresearch/AbstentionBench | — | CC BY-NC 4.0 | Cite only; do not redistribute code | V |
| pymupdf4llm | — | AGPL-3.0 (both reports) | Excluded | Not re-checked |

## 3. Datasets and corpus

| Claim | Finding | Status |
|---|---|---|
| SQuAD 2.0 license CC BY-SA 4.0 | HF dataset card: `cc-by-sa-4.0` | V |
| Train 130,319 Qs; 86,821 answerable / 43,498 unanswerable; 442 articles | Counted from parquet: identical; 19,029 unique paragraphs | V |
| Dev 11,873; 5,928 / 5,945 | Counted: identical | V |
| **GEM: dev has 78 articles, split ~30/~48** | **Dev has 35 articles (1,204 paragraphs).** 78 is not the SQuAD 2.0 dev article count | **C** |
| GEM §66: train negatives "42,720 vs 43,498" unresolved | 43,498 unanswerable in train (programmatic) | V (resolved) |
| d2l text CC BY-SA 4.0; code modified MIT | `d2l-ai/d2l-en` LICENSE = CC BY-SA 4.0; LICENSE-SAMPLECODE = MIT-style ("Copyright 2019 Amazon.com"); README summary confirms | V |
| d2l "second edition 2026" (MDR) | Not checked; irrelevant once a commit is pinned | U (irrelevant) |

## 4. Publications (high-impact claims only)

| Item | Claim used | Finding | Status |
|---|---|---|---|
| Joren et al., *Sufficient Context*, ICLR 2025, arXiv 2411.06037 | Context lowers abstention; sufficiency + confidence selective generation +2–10% | Both reports agree; MDR cites the ICLR virtual page | PV (venue V; numbers taken from reports, consistent between them) |
| Kirichenko et al., *AbstentionBench* | Reasoning fine-tuning degrades abstention ~24%; scale helps little | **NeurIPS 2025 Datasets & Benchmarks Track** (proceedings page). GEM's "ICML 2025 Workshop" and DOI-as-venue are **wrong**. Note: an ICML 2025 workshop page also exists, but the archival venue is NeurIPS 2025 D&B | V (finding); **C** (GEM venue) |
| Setiawan, *Prompt-Based Abstention Fails Under Misleading Context* (GRAB-RAG), arXiv 2608.22228 | 41.6% answer rate under misleading context with explicit abstention prompt; 63% echo planted entity | Confirmed. **Now published at AACL-IJCNLP 2026** (aclanthology `2026.aacl-long.153`). MDR's "single-author preprint" label is outdated | V (update venue) |
| Seo & Jang, *When Retrieval Similarity Hurts*, Findings EMNLP 2026 | CE weighting improves EM 9/9 cells; NLI weighting fails | Paper exists (authors' GitHub `DONGJUSEO/rag-document-weighting`, Zenodo DOI 10.5281/zenodo.22054839). README says "**ACL Anthology entry to appear**", so GEM's ID `2026.findings-emnlp.594`, pp. 12534–12558 and "full PDF extracted" **cannot be verified**. Specific numbers unverified. Claim concerns *document weighting*, not abstention | PV / U (IDs, numbers) |
| GEM "COLM 2026 (OpenReview PWv1RIS6QK)" risk-controlled selective evaluation | Clopper–Pearson UCB bounds selective FDR | GEM's own works-cited titles this *"Uncertainty-Guarded LLM Judging with Provable Risk Guarantees"*: Badshah, Emami, Sajjad, arXiv 2608.17994 (*Judge, Retrieve, or Abstain*). It concerns **LLM-as-judge**, not RAG answer abstention. COLM venue unverified. The CP-UCB math is standard, but GEM mislabels its application | **C** (mislabeled) / U (venue) |
| MiniCheck, Tang, Laban & Durrett, EMNLP 2024, doi 10.18653/v1/2024.emnlp-main.499 | GPT-4-level grounding accuracy at ~400× lower cost | Confirmed from abstract. MDR's exact 74.7 vs 75.3 BAcc not re-read from the table | V / PV (exact BAcc) |
| LettuceDetect, Kovács & Recski, arXiv 2502.17125 | RAGTruth F1 79.22%; GPT-4 63.4%; Llama-2-13B 78.7% | Confirmed on HF model card | V |
| HALT-RAG, arXiv 2509.07475 | Dual-NLI ensemble + calibrated meta-classifier + abstention | Confirmed (Goswami & Kurra, Sep 2025) | V |
| Cite or Decline, arXiv 2609.01846 | 833 messages, 70.5% with citations; usually declined without evidence | Confirmed via mirror; arxiv.org not reached | PV |
| Trust-Align (ICLR 2025); ALCE (EMNLP 2023); RAGTruth (ACL 2024); SQuAD 2.0 (ACL 2018); Kamath et al. (ACL 2020); Wallat et al. (ICTIR 2025); Yu et al. (SIGCSE 2025); VeriCite (SIGIR-AP 2025) | As cited in the reports | DOIs consistent across reports or well established; not re-fetched in this pass | PV |
| JTIE "Evidence-Calibrated RAG" (MDR P9) | AUROC 0.5475 etc. | Not re-checked. MDR already flags the venue as low-tier → **removed from the 10-paper matrix**; cite at most as related work | U |
| Lewis 2020, SBERT, BM25, RRF, DPR | Foundational | Well established | — |

## 5. Corrections log (what changes in the downstream documents)

| ID | Location | Original statement | Correction | Basis |
|---|---|---|---|---|
| CR-01 | GEM Table G, Handoff §5 | SQuAD dev = 78 articles; Cal ~30 / Test ~48 articles | 35 articles. Gate-dev from held-out **train** articles; dev → SQuAD-cal 12 / SQuAD-test 23 articles | Programmatic count |
| CR-02 | GEM §16, Table D, Table I | MiniCheck "academic/non-permissive" license | Code Apache-2.0; FT5/DeBERTa/RoBERTa weights MIT; only Bespoke-7B is CC BY-NC | GitHub LICENSE, HF cards |
| CR-03 | GEM Table D | MiniCheck "not on PyPI" | A `minicheck` package exists on PyPI with unverified provenance; use the git install | PyPI |
| CR-04 | GEM §15, C08, bib [8] | AbstentionBench = ICML 2025 Workshop | NeurIPS 2025 Datasets & Benchmarks Track | NeurIPS proceedings |
| CR-05 | GEM §19, §32, §42, CL-10 | "COLM 2026" paper establishes finite-sample selective-FDR control for this setting | Source is an LLM-judging paper (arXiv 2608.17994). CP-UCB validity additionally requires (i) a threshold fixed independently of the calibration data, or multiplicity-controlled selection, and (ii) exchangeable calibration/test data. Neither holds in this design → **no guarantee claimed** | Source title; standard theory |
| CR-06 | GEM §5, Table C, bib [5] | Seo & Jang ACL ID/pages; "full PDF extracted" | Anthology entry "to appear"; cite as Findings of EMNLP 2026 with repo/Zenodo DOI; do not quote the unverified numbers | Authors' README |
| CR-07 | MDR §6.1E, §6.2 | "Qwen3-4B … non-thinking mode" | Use `Qwen/Qwen3-4B-Instruct-2507` (non-thinking only). Plain `Qwen3-4B` thinks by default | HF cards |
| CR-08 | MDR P8 | GRAB-RAG "single-author preprint" | Published at AACL-IJCNLP 2026 (`2026.aacl-long.153`) | Web search |
| CR-09 | MDR §6.2 | bge-reranker-base "verify license" | MIT (but ms-marco-MiniLM chosen) | HF |
| CR-10 | MDR §6.1E | Phi-4-mini license "verify" | MIT | HF |
| CR-11 | GEM throughout | Extraction artifacts `[span_N](start_span)[span_N](end_span)` inside text, model names and URLs (e.g., "Phi-4[span_48]…-mini", "torc[span_76]…h") | Ignore the artifacts. Every identifier was re-derived from the HF/PyPI checks above | Text inspection |
| CR-12 | GEM Table G | Markdown table rendered as escaped pipes (unreadable) | Content re-expressed in `dataset_and_annotation_plan.md` | Text inspection |
| CR-13 | GEM §30 | VRAM co-hosting "~9.5–10.5 GB" presented as a plan | Estimate only. Experiments are staged; demo VRAM is measured in M0 | Engineering |
| CR-14 | GEM §14, §29 | Seo & Jang cited as evidence that the CE score is a strong *abstention* signal | It evaluates document weighting for EM. Using CE as an abstention baseline is reasonable, but that claim needs its own test (B2) | Scope |
| CR-15 | GEM Table J | Several items marked "Fully Verified" from "full PDF extracted" | Treated as PV unless re-verified here (see §4) | Audit policy |
| CR-16 | Both | Dependency stack implicitly assumes transformers 4.x | transformers 5.x is current; lock versions (ADR-010) | PyPI |
| CR-17 | GEM §40 | Conflicting/ambiguous items (10%) in the clean course test | Approved course material should not contain contradictions; contradictions are constructed in stress set S4 | Design rationale |

## 6. Revised 10-paper matrix (Deliverable B core)

Selection rule: recent (2024–2026), verified at least at the PV level, directly relevant, reputable venue. Foundational works (SQuAD 2.0, Kamath 2020, ALCE 2023) are cited in addition.

| # | Paper | Venue | Role in LearnMate | Status |
|---|---|---|---|---|
| P1 | Joren et al., Sufficient Context | ICLR 2025 | Closest conceptual precedent (sufficiency-based selective generation) | PV |
| P2 | Song et al., Trust-Align | ICLR 2025 | Grounded-refusal metrics; prompting insufficient | PV |
| P3 | Tang et al., MiniCheck | EMNLP 2024 | Decision-time support verifier | V |
| P4 | Niu et al., RAGTruth | ACL 2024 | Hallucination taxonomy (incl. implicit truth) for error analysis | PV |
| P5 | Kovács & Recski, LettuceDetect | arXiv 2025 | Independent auto-evaluator | V (card) |
| P6 | Kirichenko et al., AbstentionBench | NeurIPS 2025 D&B | Non-reasoning generator choice; prompt abstention weak | V |
| P7 | Setiawan, GRAB-RAG | AACL 2026 | Misleading-evidence stress; NLI over-abstention | V |
| P8 | Peng et al., UAEval4RAG | ACL 2025 | Unanswerable-question taxonomy for course items | PV |
| P9 | Wallat et al., Correctness is not Faithfulness | ICTIR 2025 | Citation correctness ≠ faithfulness; withheld-gold test | PV |
| P10 | Yu et al., SLMs + RAG in Computing Education | SIGCSE TS 2025 | Local small-model course tutor precedent | PV |

Related (cite in text, not in the matrix): HALT-RAG (2025), Seo & Jang (Findings EMNLP 2026; anthology pending), VeriCite (SIGIR-AP 2025), Ethel (arXiv 2024), Cite or Decline (arXiv 2026), Know Your Limits survey (TACL 2025), RefusalBench (EACL 2026), O'Regan & Kokaram (IEEE SPM 2026).

**Rule for the paper draft:** quote no number from a PV/U source until it has been read from the primary PDF. Re-verify on the student's network, where arXiv and ACL Anthology are reachable.
