# LearnMate (G06): Phase I Research, Literature Review, Technology Survey and Experiment Design

LearnMate should be built as a small, fully local RAG tutor: section-aware chunks from an openly licensed course text, hybrid retrieval with a reranker, and a quantized ~4B open-weight LLM. Its research contribution should be a trained, calibrated "evidence-sufficiency gate". This gate fuses a SQuAD 2.0–fine-tuned answerability cross-encoder with claim-level NLI support checks, and its threshold is set on a calibration split. It should be tested against score-threshold and prompt-only abstention. The individual components are already published. The defensible contribution is therefore a controlled, application-specific evaluation of their integration in a course-tutor setting, under stress tests that include misleading and contradictory evidence. It is not a new algorithm.

## TL;DR
- **Novelty status:** "Evidence agreement + calibrated abstention" is not new as a set of parts. Sufficiency-based selective generation (Joren et al., ICLR 2025), refusal-aware alignment (Trust-Align, ICLR 2025), calibrated NLI hallucination detectors (HALT-RAG) and an evidence-calibrated SQuAD 2.0 RAG study (JTIE 2025) all exist.\[1\]\[2\]\[3\]\[4\] We found no paper that combines a trained answerability gate with claim-level NLI verification of a small-LLM answer and a held-out calibrated threshold, evaluated on an independently annotated course test set. Frame the work as a replication-plus-adaptation and a controlled evaluation.
- **Hypothesis to test (H1):** On a clean held-out course test set, the calibrated fused gate achieves lower AURC (area under the risk–coverage curve) and a lower unsupported-answer rate at matched coverage than (a) prompt-only "say I don't know" RAG and (b) reranker-score-threshold abstention. Significance is judged with paired bootstrap CIs. The strongest current evidence for why this matters is a 2026 controlled study of small frozen RAG models. It found that explicit abstention prompting still answered 41.6% of misleading-context questions, and an NLI verifier traded large coverage losses for safety.\[5\]
- **Recommended stack:** Python, PyTorch and HF Transformers, plus Sentence Transformers. Use bge-small-en-v1.5 as the baseline embedder and Qwen3-Embedding-0.6B as the upgrade, BM25 with dense retrieval fused by RRF in FAISS, and a cross-encoder reranker. The generator is Qwen3-4B (Apache 2.0), quantized and run via llama.cpp or bitsandbytes. A DeBERTa-v3 cross-encoder is fine-tuned on SQuAD 2.0 for answerability, with MiniCheck or DeBERTa-NLI for claim support. The UI is a single-process Streamlit app. The primary corpus is the Dive into Deep Learning text (CC BY-SA 4.0) taken from its Markdown source, which avoids PDF-parsing risk.\[6\]

---

## 1. Assignment requirements summary and compliance checklist

**Problem (handbook):** AI tutors can give plausible but unsupported explanations. The task is to build a course-specific, document-grounded assistant that cites its sources and abstains when the evidence is inadequate. The research question is "Evidence agreement and calibrated abstention". The datasets are SQuAD 2.0 plus approved course materials, with an independently checked course evaluation set.

| Requirement | Mandatory / Suggested | How this plan satisfies it |
|---|---|---|
| Exactly two members; contribution statement (H) | Mandatory | §15: Member A owns retrieval, LLM and UI; Member B owns the gate, annotation and evaluation; both annotate |
| Python with PyTorch/TF; Colab OK | Mandatory | PyTorch + HF; all components fit a free T4 (~15 GB) |
| Public/licensed data with source, version, access date, conditions, preprocessing | Mandatory | Dataset card fields in §11; SQuAD 2.0 and d2l text both CC BY-SA 4.0 |
| ≥2 meaningful baselines (≥1 strong) | Mandatory | B1 extractive, B2 prompt-only RAG, B3 hybrid + reranker + score threshold (strong) |
| One justified change; ablation; ≥1 stressed condition; error analysis | Mandatory | Fused calibrated gate; 5 ablations; 6 stress conditions (§13) |
| One application-specific failure mode | Mandatory | Unsupported answers to out-of-syllabus / partial / misleading-evidence questions |
| Leakage-safe splits; never tune on test | Mandatory | Disjoint dev/calibration/test by course section and SQuAD article (§11) |
| 8–10 paper matrix; falsifiable hypothesis | Mandatory | §4 matrix (10 papers) + H1/H0 (§8) |
| Working demo (UI is not evaluation) | Mandatory | Streamlit demo plus separate evaluation notebook |
| Suggested architectures, metrics, compute cost | Suggested | Sentence Transformers, small LLM and RAG all used; answer support, abstention accuracy, human-checked factuality, AURC, citation precision/recall; latency, VRAM, GPU-hours |
| Package A–H, 4–6 page draft, 3–5 min demo | Mandatory | Milestones M1–M8 (§15) |
| Negative findings; gen-AI transparency; avoid guaranteed-acceptance venues | Mandatory | §13, §15, §16 |

---

## 2. Problem interpretation

**What an "evidence-grounded course tutor" means in practice.** Every substantive claim in an answer is entailed by a stored, approved course passage. Every citation resolves to a real stored passage ID, with document, section/page and character offsets. When the approved corpus does not support an answer, the system says so explicitly and does not fall back on parametric knowledge. The system distinguishes *retrieved* passages (topically relevant) from *supporting* passages (evidentially entailing).

**Stakeholders.**

| Stakeholder | Need | Harm if system fails |
|---|---|---|
| Students | Correct, course-consistent explanations with a pointer into the material | Learning a wrong or off-syllabus explanation with false confidence |
| Instructors | Answers within syllabus and notation; visibility of unanswered questions | Misinformation attributed to the course; correction load |
| Course admins | Copyright compliance; privacy; low cost | Copyright breach; data exposure |
| Academic evaluators | Measurable, reproducible claims; honest negative results | Unverifiable "works well" claims |

**Primary workflow:** instructor approves documents → ingestion with provenance → student asks a question → retrieval and reranking → the gate predicts the evidence state (sufficient / partial / insufficient / contradictory) → if sufficient or partial, the LLM generates a cited answer → claim-level verification removes or flags unsupported sentences → the UI shows the answer, citations and inspectable passages, or an abstention with the nearest relevant sections → the interaction is logged for instructor review.

**Application failure mode to quantify (handbook task 1):** the *unsupported-answer rate on questions the course material cannot fully answer* (out-of-syllabus, partially supported, misleading or contradictory evidence). The paired usefulness metric is the *false-abstention rate on answerable questions*. Existing deployments show this matters but rarely measure it with abstention metrics. Ethel (ETH Zurich; Kortemeyer, arXiv 2407.19452) "was deployed for over 1500 students across six courses during the Spring semester of 2024", running on GPT-4 via Azure at "$7.50 per student per course per semester"; "although the system sometimes provided incorrect answers, a survey revealed that the majority of students still found it helpful." MoodleBot reported 88% accuracy and explicitly called for better automated fact-checking.\[7\] A 2025 deployment found 36.8% of students frustrated when responses extended beyond the constrained knowledge base; this was reported secondhand in a 2026 arXiv paper and is labelled secondary.\[8\]

**Input/Output.** Input: an English question plus an optional section filter. Output: an answer with sentence-level citations, or a typed abstention, an evidence-state label, and inspectable passages. **Constraints:** no paid APIs; free Colab or local GPU; copyright-respecting corpus; 3–4 weeks for two people.

### Functional requirements (validated and refined)

| ID | Requirement | Priority | Acceptance check |
|---|---|---|---|
| FR-01/02 | Ingestion; extraction and normalization | Must (Markdown, PDF) / Could (PPTX, DOCX) | d2l Markdown; PDF via Docling; keep LaTeX math as text |
| FR-03 | Provenance tracking | Must | doc_id, commit, URL, license, section path, page, char offsets, tool version |
| FR-04 | Source-aware chunking | Must | Chunks never cross a section boundary |
| FR-05/06 | Embeddings; retrieval index | Must | Model revision logged; persisted FAISS + BM25; deterministic rebuild |
| FR-07 | Query processing | Should | Normalization; rewrite is ablation-only |
| FR-08 | Evidence retrieval and ranking | Must | Hybrid + RRF + cross-encoder rerank, top-k logged |
| FR-09 | Context-grounded generation | Must | Prompt forbids outside knowledge; passage IDs in context |
| FR-10 | Verifiable citations | Must | Every citation ID must exist in the store; otherwise strip and flag |
| FR-11/12 | Sufficiency assessment; abstention | Must (research core) | Calibrated P(sufficient) plus state; threshold from config fitted on calibration split |
| FR-13/14 | Unsupported and partially supported questions | Must / Should | Typed message plus nearest sections; answer only supported parts; no general-knowledge fill |
| FR-15/16 | UI; cited-passage inspection | Must | Streamlit chat + evidence panel; click a citation to see the stored span |
| FR-17/18 | Logging; reproducible config | Must | Per-query JSONL; one YAML config + seeds + pinned requirements |
| FR-19 (added) | Contradiction state | Should | Pairwise NLI among top passages flags "contradictory" |
| FR-20 (added) | Instructor review export | Could | CSV of abstained questions (content-gap signal) |

### Non-functional requirements with acceptance criteria

Targets marked *[measure-then-set]* deliberately have no invented number. Measure B3 in Week 2, then pre-register the target before running the test set.

| NFR | Acceptance criterion | Justification |
|---|---|---|
| Faithfulness | Unsupported-claim rate of LearnMate < B2 and B3 at matched coverage, paired 95% CI excluding 0 | This is the hypothesis; no absolute number exists for course corpora |
| Citation traceability | 100% of emitted citation IDs resolve to stored passages | Hard engineering invariant |
| Citation correctness | ALCE-style NLI citation precision/recall plus human audit on ≥20% of test items | ALCE's NLI metrics agreed with humans at 85.1% (recall) and 77.6% (precision), so a human audit is still needed\[9\] |
| Abstention usefulness | Answerable-item coverage not below B3 by more than a pre-registered margin *[measure-then-set]* | Prevents "always abstain" wins |
| Latency / resources | p50/p95 latency on T4 *[measure-then-set]*; peak VRAM ≤ 15 GB; gate training fits T4 | Handbook constraint; no edu-specific latency standard found |
| Reproducibility | Fresh Colab run reproduces tables within bootstrap CI | Handbook package D |
| Security / licensing | Allow-listed file types, no macros or network fetch at ingest; license + attribution per document | d2l and SQuAD are CC BY-SA 4.0\[6\] |
| Evaluability | Every test item has gold evidence state + span IDs | Needed for support metrics |
| Failure recovery | Any component failure yields an abstention, never an unverified answer | Fail-closed principle |
| Maintainability | pytest tests for provenance, citation resolution, thresholding | Low-cost assurance |
| UX | Uncalibrated scores never shown as probabilities | GRAB-RAG measured ECE 0.60–0.95 for self-reported confidence under missing/misleading context\[5\] |

---

## 3. State of research (synthesis)

1. **RAG still hallucinates, and errors split by context sufficiency.** Joren et al. (ICLR 2025) found that larger models (Gemini 1.5 Pro, GPT 4o, Claude 3.5) "excel at answering queries when the context is sufficient, but often output incorrect answers instead of abstaining when the context is not". Smaller models "hallucinate or abstain often, even with sufficient context"; the arXiv v3 abstract names Mistral 3 and Gemma 2, while the ICLR page also lists Llama 3.1. Their selective-generation method combines a sufficiency autorater with self-rated confidence and "improves the fraction of correct answers among times where the model responds by 2–10% for Gemini, GPT, and Gemma". Their autorater is FLAMe, a 24B model, which is not Colab-feasible.\[10\] A small trained gate is therefore a meaningful adaptation.
2. **Prompting alone is a weak abstention mechanism.** Trust-Align (ICLR 2025) reports that in-context prompting "fail[s] to effectively adapt LLMs to the RAG task"; its DPO alignment (19K-sample dataset) improves overall Trust-Score in 26 of 27 configurations and yields "substantial improvements in F1_GR" (grounded refusals) across all 27. GRAB-RAG (arXiv 2608.22228, 2026; read in full) tested Phi-4-mini, Llama-3.1-8B and Qwen2.5-7B (Q4_K_M GGUF): with explicit abstention prompting, answer rates stay ≤3% when evidence is missing but reach 13.6–74.3% when a fluent misleading passage is present, and 63% of those answers echo the planted entity.\[5\] AbstentionBench (Kirichenko et al., NeurIPS 2025) evaluated 20 frontier LLMs across 20 datasets and found "reasoning fine-tuning degrades abstention (by 24% on average)"; a "carefully crafted system prompt can boost abstention" but "does not resolve models' fundamental inability to reason about uncertainty".
3. **Dedicated small verifiers are competitive with large LLM judges for grounding.** MiniCheck-FT5 (770M) reaches 74.7% average balanced accuracy on LLM-AggreFact versus 75.3% for GPT-4 (Tang, Laban & Durrett, EMNLP 2024, Table 2), with "almost the same performance as GPT-4 but … more than 400 times cheaper" ($0.24 vs $107 on the 13K test set). HHEM-2.1-Open (110M, Apache 2.0, flan-t5-base) runs on CPU.\[11\]
4. **Sufficiency ≠ correctness.** GRAB-RAG shows that sufficiency checks cannot catch misleading-but-sufficient evidence. Its NLI verifier (DeBERTa-v3-large, argmax contradiction) cut misleading-context answering to 14.0%, but raised false abstention on answerable questions to 31.0% (Q100) and 51.4% (Q50).\[5\] This trade-off is the gap a *calibrated, fused* gate should address.
5. **Calibration and conformal methods are maturing for RAG.** Examples include Conformal-RAG (SIGIR 2025, claim filtering with factuality guarantees) and conformal context filtering (arXiv 2511.17908).\[12\]\[13\] One 2026 paper warns that exchangeability does not hold a priori for retrieval scores at finite retrieval depth.\[14\]
6. **Educational RAG deployments are numerous, but rarely measure abstention rigorously.** Examples are Ethel, MoodleBot, NeuroBot TA, the Motion Picture Engineering AI-TA, ChemTAsk and curriculum SLM assistants. The closest exception is "Cite or Decline" (arXiv 2609.01846, EMNLP 2026 Industry): across 833 messages 70.5% included citations and the chatbot "usually declined" when no lecture evidence matched.\[15\] Its abstention is retrieval-match-based, not a calibrated classifier.

### 3.1 Review method, search log and access limitations

- **Date of all searches:** 23 Nov 2026. **Tools:** web search (18 queries, budget exhausted), one full-text fetch (arXiv 2608.22228), and one sub-agent novelty search (~10 queries/fetches; abstracts and landing pages only).
- **Query topics:** Sufficient Context; Trust-Align; SQuAD 2.0 license/counts; MiniCheck; Know Your Limits; course RAG TA deployments; abstention classifier + NLI fusion + calibrated threshold; conformal RAG; UAEval4RAG; embedding MTEB/licenses; small-LLM licenses; Docling vs PyMuPDF4LLM vs Marker; chunking evaluations; d2l.ai license; ALCE; RAGChecker; HHEM-2.1-Open; BEA 2027. **Sub-agent:** JTIE Evidence-Calibrated RAG, RefusalBench, edu-tutor abstention papers, CRAG/Self-RAG, AbstentionBench.
- **Limitations:** Two planned searches (education-RAG abstention evaluation; FaithEval) failed because the budget was exhausted. FaithEval, RAMDocs, Self-RAG, CRAG details, Kamath et al. 2020, R-Tuning, RGB, AlignScore, FActScore, RAGAS, ARES, semantic entropy and AIED/EDM/L@S deadlines come from prior knowledge or reference lists and are marked **[not re-verified]**. Vendor/blog technology comparisons are marked **[secondary]**. The JTIE PDF was blocked by bot protection.
- **Read level:** **FT** = full text; **AB** = abstract/landing page/snippet; **2nd** = secondary summary.

---

## 4. Verified literature review

### 4.1 Shortlist: 10-paper assignment matrix

| ID | Title (Authors, Year, Venue) | DOI/URL | Architecture / method | Dataset | Reported findings (as reported) | Limitations | Code | Applicability / adoption | Read |
|---|---|---|---|---|---|---|---|---|---|
| P1 | Know What You Don't Know: Unanswerable Questions for SQuAD (Rajpurkar, Jia, Liang, 2018, ACL) | arXiv 1806.03822 | Dataset: 53,775 adversarial unanswerable questions\[16\] | SQuAD 2.0 (CC BY-SA 4.0) | 93% of sampled negatives verified unanswerable; dev/test ~1:1, train ~2:1\[16\]\[17\] | Single passage, Wikipedia, extractive, no retrieval | Data public | Gate training/calibration data. **Adopt** | AB |
| P2 | Sufficient Context: A New Lens on RAG Systems (Joren, Zhang, Ferng, Juan, Taly, Rashtchian, 2025, ICLR) | arXiv 2411.06037 | Sufficiency autorater + self-rated confidence → logistic selective generation | HotpotQA, MuSiQue, others | Autorater 93% accuracy (slides); +2–10% selective accuracy at same coverage\[18\]\[19\] | 24B autorater; not edu | hljoren/sufficientcontext | Closest conceptual precedent. **Adopt idea; replicate small** | AB |
| P3 | Measuring and Enhancing Trustworthiness of LLMs in RAG through Grounded Attributions and Learning to Refuse (Song et al., 2025, ICLR) | arXiv 2409.11242 | DPO alignment (Trust-Align) + Trust-Score | ASQA, QAMPARI, ELI5, ExpertQA | 26/27 configs improved; LLaMA-3-8B beats FRONT on ASQA by 12.56\[3\] | DPO heavy for Colab | declare-lab/trust-align | Refusal and citation metrics. **Adopt metric only** | AB |
| P4 | MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents (Tang, Laban, Durrett, 2024, EMNLP) | 10.18653/v1/2024.emnlp-main.499 | Small fact-checkers on synthetic data | LLM-AggreFact | MiniCheck-FT5 (770M) ≈ GPT-4 at ~400× lower cost\[20\] | Not tuned on course text | Liyan06/MiniCheck | Claim-support verifier. **Adopt** | AB |
| P5 | Enabling LLMs to Generate Text with Citations, ALCE (Gao, Yen, Yu, Chen, 2023, EMNLP) | 10.18653/v1/2023.emnlp-main.398 | NLI citation recall/precision | ASQA, QAMPARI, ELI5 | Accuracy vs humans 85.1% / 77.6%; kappa 0.698 / 0.525 | No partial-support detection | princeton-nlp/ALCE | Citation metrics. **Adopt metric** | AB\[21\] |
| P6 | Know Your Limits: A Survey of Abstention in LLMs (Wen et al., 2025, TACL 13:529–556) | 10.1162/tacl_a_00754 | Survey: query / model / human values\[22\]\[23\] | — | Organizes methods, benchmarks, metrics | Survey | — | Framing. **Cite** | AB |
| P7 | Unanswerability Evaluation for RAG, UAEval4RAG (Peng, Choubey, Xiong, Wu, 2025, ACL) | aclanthology.org/2025.acl-long.415 | Synthesizes 6 unanswerable categories per KB\[24\] | Any KB | Components shift the answerable/unanswerable trade-off\[25\] | Synthetic, LLM-judged | SalesforceAIResearch/Unanswerability_RAGE | Test taxonomy. **Adopt taxonomy** | AB |
| P8 | Prompt-Based Abstention Fails Under Misleading Context: GRAB-RAG (Setiawan, 2026, arXiv) | arXiv 2608.22228 | 5 policies on frozen 3.8–8B models; paired 4-condition design | NQ, HotpotQA (500 each) | Explicit-prompt HwSA@misleading 41.6%; NLI policy 14.0% with FAC@Q100 31.0%; 63% echo\[5\] | Single-author preprint; no trained gate | "Will be made available" | Motivates H1; reuse HwSA/FAC. **Adopt protocol** | **FT** |
| P9 | Evidence-Calibrated RAG for Unanswerable QA (Zhong, Chen, Zhong, Sun, 2025, JTIE 4(2)) | 10.51903/jtie.v4i2.536 | Hybrid retrieval + lexical rerank + extractive answer + sufficiency calibration (threshold 0.59, 43,482 examples)\[1\]\[26\] | SQuAD 2.0 dev (11,873) | 31.65 EM, 34.74 F1, refusal F1 53.71%; hallucination proxy 77.80%→37.49%; AUROC 0.5475, ECE 0.1144\[1\] | Low-tier venue; date inconsistencies; no NLI or LLM | Unknown | Closest direct prior. **Cite with caution** | AB |
| P10 | RefusalBench (Muhamed et al., 2026, EACL) | 10.18653/v1/2026.eacl-long.321 | 176 perturbation strategies, 6 categories\[27\] | RefusalBench-NQ, -GaRAGe | Refusal accuracy "below 50% on multi-document tasks"; scale does not help\[27\] | Benchmark only | Data (secondary) | External stress set. **Optional** | AB |

### 4.2 Broader catalog (grouped)

- **RAG and retrieval:** Lewis et al. 2020 RAG [not re-verified]; Sentence-BERT 2019 [not re-verified]; C-Pack/BGE, SIGIR 2024; Qwen3 Embedding, arXiv 2506.05176; Docling, arXiv 2501.17887; READoc, arXiv 2409.05137; Vectara chunking study, NAACL Findings 2025, arXiv 2410.13070 [2nd].\[28\]
- **Citation:** ALCE; Trust-Align; Self-RAG, arXiv 2310.11511 [not re-verified]; FRONT, arXiv 2408.04568.\[29\]
- **Faithfulness:** MiniCheck; HHEM-2.1-Open (doi 10.57967/hf/3240; Apache 2.0);\[30\] HALT-RAG, arXiv 2509.07475 (dual-NLI ensemble plus calibrated meta-classifier with abstention, very close to the verifier half of the intervention);\[4\] AlignScore, SummaC, FActScore [not re-verified]; RAGChecker, arXiv 2408.08067.\[31\]
- **Abstention and calibration:** Kamath et al. 2020 Selective QA under Domain Shift [not re-verified]; Geifman & El-Yaniv 2017 (AURC); Guo et al. 2017; R-Tuning (NAACL 2024); Don't Hallucinate, Abstain (ACL 2024); Soudani et al. 2025 (ACL Findings); semantic entropy [not re-verified]; AbstentionBench, arXiv 2506.09038; CRAG, arXiv 2401.15884; Conformal-RAG, SIGIR 2025 [2nd]; arXiv 2511.17908.
- **Conflicting evidence:** RGB (AAAI 2024); Longpre et al. 2021; Xie et al. ICLR 2024; Wang et al. COLM 2025; DRUID (ACL 2025); MAGIC (EMNLP Findings 2025); FaithEval [not re-verified].
- **Educational RAG:** Ethel, arXiv 2407.19452; MoodleBot, IEEE Trans. Education 68(1); NeuroBot TA, npj Digital Medicine 8:627; AI-TA MPE, arXiv 2604.04670; MARK, arXiv 2506.23026; SLMs for Curriculum Guidance, arXiv 2510.02347; Cite or Decline, arXiv 2609.01846; arXiv 2609.21600; CS50 duck, Jill Watson [not re-verified].

All catalog items without FT/2nd tags were read at abstract level (AB).

---

## 5. Existing implementation survey

| Repo | Linked paper / license | Mechanism | Suitability |
|---|---|---|---|
| declare-lab/trust-align | P3 / check repo | Trust-Eval: grounded-refusal F1, citation F1 | **Research-backed**; reuse evaluator logic |
| Liyan06/MiniCheck | P4 / check repo | Sentence-level support scores | **Research-backed**; drop-in verifier |
| princeton-nlp/ALCE | P5 / check repo | NLI citation recall/precision | **Research-backed**; metric reference\[32\] |
| SalesforceAIResearch/Unanswerability_RAGE | P7 / check repo | Unanswerable query synthesis | Research-backed; stress generator |
| sigmedia/ai-teaching-assistant | AI-TA MPE / check repo | Course RAG with granular citations | Deployment reference; no abstention metrics |
| vectara/hallucination_evaluation_model | HHEM-2.1-Open / Apache 2.0 | Premise–hypothesis consistency | Cheap secondary verifier\[11\] |

**Patterns to adopt:** passage IDs injected into the prompt and citations validated post hoc against the store; hybrid BM25 + dense with RRF; paired designs on identical questions; McNemar plus paired bootstrap with multiplicity correction; thresholds frozen on a calibration split.

**Recurring mistakes to avoid:** cosine similarity as a faithfulness gate (it measures topical relatedness, not entailment);\[33\] counting citation *presence* as correctness; LLM-as-judge without human audit; tuning thresholds on test data; reporting abstention rate without coverage or utility; AGPL dependencies in network-served demos; treating GitHub stars as validity.

---

## 6. Technology comparison and decision matrix

### 6.1 Survey by component (condensed)

**A. Ingestion.** **Docling** (MIT; PDF, DOCX, PPTX, XLSX, HTML; layout/table models; OCR) is recommended.\[34\] **PyMuPDF/pymupdf4llm** is very fast on born-digital PDFs but AGPL-3.0, so network use triggers obligations.\[35\] **Marker** reconstructs tables/math best in some tests, but its weights carry revenue-threshold terms and it is slow on CPU [2nd].\[36\] **MarkItDown** (MIT) dropped tables in one test [2nd].\[36\] On READoc, average scores were PyMuPDF4LLM 40.55, Docling 58.83 and Marker 64.98, with formula extraction weak for all but Marker (AB).\[37\] Failure modes: multi-column reading order, equations, tables, scanned pages, headers/footers, missing page numbers. **Scope:** primary corpus = d2l Markdown source (no PDF parsing); secondary = born-digital PDFs via Docling; scanned PDFs and PPTX out of scope for LCA-3.

**B. Chunking.** The Vectara NAACL 2025 study found fixed-size chunking competitive with or better than semantic chunking on realistic sets, at lower cost [2nd]; semantic chunks that are too small hurt end-to-end QA [2nd].\[28\] **Recommendation:** section-aware recursive chunks of about 256–512 tokens with small overlap, never crossing headings, each carrying its section path, with the full section stored as a display "parent". Contextual-chunk prefixes and late chunking are optional ablations.

**C. Embeddings** (do not default to the largest):

| Model | Size / dim / max tokens | License | Evidence | Role |
|---|---|---|---|---|
| all-MiniLM-L6-v2 | ~22M / 384 | Apache 2.0 [not re-verified] | Long-standing baseline | Sanity baseline |
| bge-small-en-v1.5 | 33.4M / 384 / 512 | MIT | MTEB Eng v2 retrieval 53.86 [2nd]\[38\] | **B2/B3 default** |
| EmbeddingGemma-300m | 303M / 768 / 2,048 | Gemma Terms | MTEB Eng v2 mean 69.67 (vendor)\[38\]\[39\] | Alternative |
| Qwen3-Embedding-0.6B | 0.6B / 1024 / 32K | Apache 2.0 | MTEB Eng v2 mean 70.70 (model card)\[40\]\[41\] | **Upgrade / ablation** |

**D. Retrieval.** BM25 (rank_bm25) plus dense retrieval, fused with RRF (k=60 is common), then rerank the top 20–50 with a cross-encoder (bge-reranker-base or ms-marco-MiniLM-L-6-v2; verify licenses). Query rewriting, multi-query and HyDE are deferred because they add LLM calls and confound attribution. **Index:** FAISS IndexFlatIP (exact, sufficient for <100k chunks) with a JSONL/SQLite metadata store; Chroma/LanceDB/Qdrant-local are unnecessary; no distributed DB.

**E. Small LLMs.**

| Model | License | Notes for LearnMate |
|---|---|---|
| **Qwen3-4B** | Apache 2.0 | **Primary**; fits a T4 in 4-bit; non-thinking mode\[42\] |
| Qwen2.5-7B-Instruct | Check card | Used in GRAB-RAG (failure evidence available) |
| Llama-3.1-8B-Instruct | Llama Community License | Secondary comparison |
| Phi-4-mini-instruct (3.8B) | Permissive per secondary sources (verify) | GRAB-RAG found it over-abstains\[5\]\[43\] |
| Granite 3.3 2B/8B | Apache 2.0 | RAG-oriented alternative\[44\] |
| Gemma 4 E4B (Apr 2026) | Apache 2.0 [2nd]; Gemma 3 uses non-OSI Gemma Terms | Candidate if card verified\[45\] |

**Runtime:** llama-cpp-python GGUF Q4_K_M (the GRAB-RAG setup on a 12 GB GPU, with grammar-constrained JSON);\[5\] HF transformers + bitsandbytes 4-bit as the alternative; vLLM is unnecessary for single-user demos. "Open weights" ≠ OSI open source; record each model's license.\[46\]

**F. Evidence verification.** Use entailment, not similarity. Options: DeBERTa-v3 NLI cross-encoders, MiniCheck, HHEM-2.1-Open, AlignScore. **Recommendation:** MiniCheck, with DeBERTa-NLI as an ablation. Split answers into sentences with a rule-based splitter. A claim is supported if some *cited* passage entails it (giving citation precision), unsupported otherwise.

**G. Uncertainty and abstention.** Signals with credible evidence: trained answerability probability (SQuAD 2.0 tradition), verifier support scores, reranker scores, sufficiency labels (Joren et al.). Weak signal: LLM verbalized confidence (GRAB-RAG ECE 0.60–0.95 under missing/misleading contexts; Soudani et al. argue uncertainty methods fall short in RAG).\[5\] Calibrate with temperature/Platt/isotonic on the calibration split; report ECE (10 bins) and Brier score. Choose thresholds on the calibration split for a target selective risk or maximum utility at a pre-registered λ. Split-conformal risk control is optional, with the exchangeability caveat. Semantic entropy is a deferred ablation.

**H. Training and evaluation tooling.** Fine-tune a **cross-encoder answerability classifier** ([CLS] question [SEP] passage(s) → P(sufficient)); do not train a generative LLM. Implement core metrics directly and reuse Trust-Eval and ALCE logic; RAGAS/DeepEval/TruLens are optional because their LLM judges must be audited.

### 6.2 Decision matrix (final stack)

| Layer | Recommended | Runner-up | Why recommended | Key risk |
|---|---|---|---|---|
| Framework | Python 3.11, PyTorch, HF Transformers | TensorFlow | Ecosystem for all listed models | Version drift; pin |
| Parser | d2l Markdown → custom parser; Docling for PDF | PyMuPDF4LLM (AGPL) | MIT, multi-format, structure | Docling slower on CPU |
| Chunking | Section-aware recursive 256–512 tok | Contextual prefix (ablation) | Competitive; preserves citation spans | Long sections split mid-derivation |
| Embedder | bge-small-en-v1.5 → Qwen3-Embedding-0.6B | EmbeddingGemma-300m | MIT/Apache, small, strong | Domain shift on math text |
| Sparse + index | rank_bm25 + FAISS flat + JSONL/SQLite | Pyserini; Chroma | Exact, simple, persistent | Math-symbol tokenization |
| Reranker | bge-reranker-base (verify license) | ms-marco-MiniLM-L-6-v2 | Strong, T4-feasible | Latency at top-50 |
| Generator | Qwen3-4B Q4_K_M via llama-cpp-python | Llama-3.1-8B / Granite 3.3 8B | Apache 2.0, small, constrained JSON | Thinking-mode verbosity |
| Gate (trained) | DeBERTa-v3-base cross-encoder on SQuAD 2.0 + hard negatives | ELECTRA-base / MiniLM-L12 | Strong encoder; Colab-trainable | T4 training time; fp16 stability |
| Verifier | MiniCheck | DeBERTa-v3 NLI; HHEM-2.1-Open | Grounding-specific; small | Math/notation claims |
| Calibration | Logistic fusion + isotonic/temperature (sklearn) | Split-conformal | Simple, auditable | Small calibration set |
| UI / tests / tracking | Streamlit; pytest; CSV/JSONL (+ local MLflow) | Gradio; W&B free | Fast; no accounts | UI is not an evaluation |

---

## 7. Practical research gap

**Refined problem:** *For a small, locally deployable course tutor, can a lightweight trained and calibrated evidence-sufficiency gate, which combines answerability classification with claim-level entailment, withhold unsupported answers more reliably than prompt-only or retrieval-score abstention, without destroying usefulness on answerable questions, when course evidence is missing, partial, distracting or misleading?*

**Why this is a research gap, not a feature request.** Joren et al. use a 24B autorater on open-domain QA.\[10\] JTIE uses lexical calibration that reached only AUROC 0.5475, with an extractive answerer and no NLI.\[1\] GRAB-RAG shows that prompt and NLI policies trade safety against coverage badly, but tests no trained or calibrated gate.\[5\] Educational deployments report accuracy or refusal anecdotes, not risk–coverage evaluation on an annotated course set. The open, testable question is whether *fusion + calibration* improves the risk–coverage frontier in a course setting. A negative result (no improvement over a reranker threshold) would also be publishable-grade evidence.

**Candidate gaps ranked by testability in 3–4 weeks:** (1) insufficient evidence / out-of-syllabus questions (core); (2) partially supported questions; (3) over-abstention; (4) misleading/contradictory evidence (stress); (5) citation incorrectness (secondary); (6) retrieval degradation (stress). Calibration is measured throughout.

**Objectives:** O1 build B1–B3; O2 train and calibrate the gate; O3 build an independently annotated course test set; O4 compare under stress with ablations; O5 release a reproducible package.

**Research questions:** RQ1: Does the fused calibrated gate lower AURC vs B2/B3? RQ2: Which signal (answerability vs NLI) contributes most? RQ3: Does a gate trained on SQuAD 2.0 transfer to course text? RQ4: How do all systems behave under misleading/contradictory evidence?

---

## 8. Recommended hypothesis

- **H1:** On the held-out LearnMate course test set, the calibrated fused gate (G) yields lower AURC *and* a lower unsupported-answer rate at matched coverage than B3 (hybrid + reranker + reranker-score threshold fitted on the same calibration split). The paired-bootstrap 95% CIs of the differences must exclude zero, and G's answerable-question coverage must not fall more than a pre-registered margin below B3's.
- **H0:** No difference in AURC or unsupported-answer rate at matched coverage between G and B3 (CI includes zero), or G achieves its gains only by exceeding the coverage-loss margin.
- **Secondary H1b (vs B2 prompt-only):** G reduces HwSA (answer rate when it should abstain) on out-of-syllabus and misleading-evidence stress items.
- **Success:** H1 supported on the course test set, with direction-consistent results on the SQuAD-derived stress set. **Failure:** H0 not rejected; report it as a negative finding, with an ablation showing which signal failed.
- **Pre-registration:** Freeze H1, the margin, λ for utility and all thresholds in a Week 2 commit before the test set is opened.

---

## 9. Proposed deep-learning approach (intervention G)

1. **Answerability cross-encoder (trained).** Base: microsoft/deberta-v3-base (fallback ELECTRA-base or MiniLM-L12). Input: question + top-k reranked passages concatenated (max 512 tokens), or per-passage scoring with max-pooling; compare both on dev. Labels: positives are SQuAD 2.0 answerable (question, gold paragraph); negatives are SQuAD 2.0 adversarial unanswerable (question, same paragraph) plus **retrieval hard negatives** (an answerable question paired with top-ranked non-gold paragraphs containing no answer string), which teach "retrieved ≠ sufficient" and narrow the SQuAD-to-RAG gap. Objective: binary cross-entropy; AdamW, lr ~2e-5, 1–2 epochs, 10% warmup, fp16 if stable, fixed seeds. Subsample (e.g., 30–60k pairs) if T4 time requires; measure training time in Week 2 rather than assuming it. Splits: SQuAD train for training; SQuAD dev split *by article title* into gate-dev and SQuAD-calibration halves; course dev split for transfer checks.
2. **Claim-level evidence agreement.** Split the generated answer into sentences; for each sentence compute MiniCheck support against each cited passage and take the max. Features: min support, mean support, fraction of supported sentences, and any-contradiction (pairwise NLI among top-3 passages).
3. **Fusion and calibration.** Logistic regression (or a 2-layer MLP if it underfits) over answerability probability, min/mean claim support, top reranker score, rerank margin (top1–top2) and BM25/dense agreement. Fit on the **course calibration split + SQuAD-calibration half**; apply isotonic or temperature scaling. Choose τ to maximize U = (#correct supported answers − λ·#unsupported answers)/N at a pre-registered λ (report λ ∈ {1, 2, 4}), or to meet a target selective risk. Optional: conformal risk control.
4. **Decision states:** **sufficient** → answer; **partial** → answer only verified sentences and mark the rest "not covered in course material"; **insufficient** → abstain and show the nearest sections; **contradictory** → show both passages, do not adjudicate, flag for the instructor. Never fill gaps with general knowledge.
5. **Compute:** one extra cross-encoder pass plus k×sentences small verifier passes at inference; measure and report latency overhead. Gate training is the only GPU-training step.

**Honest framing:** this is an adaptation of Kamath-style calibrated selective QA, Joren-style sufficiency selective generation and MiniCheck/HALT-RAG verification, combined and evaluated in a course-tutor setting. It is not a new method.

---

## 10. Baselines

| ID | System | Why it is fair and defensible |
|---|---|---|
| B1 | Retrieval + extractive QA (SQuAD2-style reader with no-answer head) showing source span | Classic SQuAD 2.0 abstention; cheapest; tests whether generation is needed |
| B2 | Dense RAG (bge-small + FAISS top-5) + Qwen3-4B + "answer only from context; otherwise say you don't know" + citation IDs | Standard default; prompt-only abstention, which GRAB-RAG and AbstentionBench show is weak |
| B3 (strong) | Hybrid BM25+dense RRF + cross-encoder rerank + same LLM + reranker-score threshold (τ fitted on calibration split) | Isolates the value of the *trained, fused* gate over a tuned retrieval-score gate |
| G | B3 + trained answerability gate + claim-level verification + calibrated fusion | Intervention |

The same generator, prompt template, top-k and corpus are used across B2, B3 and G. B3 and G share retrieval exactly, so the only difference is the decision mechanism.

---

## 11. Dataset and annotation strategy

**SQuAD 2.0 (audit facts).** Wikipedia paragraphs with extractive answers, plus 53,775 new adversarial unanswerable questions written by crowdworkers to be relevant and to contain a plausible answer.\[47\] Train has roughly 2:1 answerable:unanswerable; dev/test roughly 1:1; the test set is hidden.\[16\] Secondary counts: train 130,319 questions (86,821 answerable / 43,498 unanswerable); dev 11,873 (5,928 / 5,945).\[48\] License CC BY-SA 4.0 (paper and HF card).\[16\]\[49\] **Limitations as a course proxy:** single passage and no retrieval; encyclopedic domain; extractive spans, not explanations; paragraph-local unanswerables with lexical-overlap artifacts; the JTIE AUROC of 0.5475 shows how hard calibration is on it.\[1\] Train is used for gate training; dev only for calibration/stress.

**Course corpus (default pending faculty approval):** *Dive into Deep Learning* (d2l.ai). The text is CC BY-SA 4.0 and the code is under a modified MIT (MIT-0) license; a 2026 second edition is listed with the same licensing.\[6\] Use a pinned GitHub commit of the Markdown source. ShareAlike means any released evaluation set quoting d2l passages must be CC BY-SA 4.0, which is compatible with SQuAD-derived items.\[50\] Alternatives (verify licenses): OpenStax (commonly CC BY), MIT OCW (commonly CC BY-NC-SA); faculty slides only with written permission.

**Provenance fields (dataset card):** doc_id, title, edition/commit hash, source URL, license, attribution, access date, permissions note, section path, page (PDF only), char start/end, extraction tool and version, extraction-quality flag (ok/math-loss/table-loss), chunk_id, parent_section_id, preprocessing steps.

**Course test set design (independently checked).** Categories: grounded answerable (single section); multi-section answerable; partially supported; out-of-syllabus (plausible deep-learning question not covered by the corpus subset); ambiguous/underspecified; contradictory (an edited passage copy, e.g., a swapped formula sign or value, GRAB-RAG-style, used only in the stress index). Use the UAEval4RAG taxonomy as a checklist. Per-item labels: question, evidence state, gold evidence passage IDs and spans, short reference answer, required-claims list (partial items), difficulty, author, and failure tags (assigned after the system runs).

**Annotation protocol:** (1) Member A writes items for sections X, Member B for sections Y. (2) Each member independently labels the other's items for evidence state and spans, blind to the author's label. (3) Compute Cohen's κ on evidence state (and span-overlap F1). (4) Resolve disagreements by discussion with a logged rationale; unresolved items go to faculty or are dropped. (5) Gen-AI may draft candidate questions only if disclosed, and every item must be human-verified against the corpus.

**Realistic size: about 150–300 course items in total.** At roughly 3–6 minutes per item to write and mark evidence, and similar time for the second label, 200 items cost about 20–40 person-hours, which is feasible alongside engineering in 3–4 weeks. Below ~150, CIs on per-category rates become very wide; above ~300 it crowds out engineering. SQuAD dev supplements volume for calibration and stress.

**Splits and leakage controls:** Split course items by **section** (not item): about 30% dev, 20% calibration, 50% test; questions about the same section never straddle splits. SQuAD dev is split by article title. The test set is frozen with a hash at the end of Week 2 and opened once in Week 3; no prompt or threshold edits after opening, and any post-hoc change is reported as exploratory.

---

## 12. Proposed architecture and ADR

| Aspect | Design A: single-process Python (recommended) | Design B: modular services |
|---|---|---|
| Components | Streamlit app importing a `learnmate` package: ingest → index (FAISS + BM25 + SQLite/JSONL) → retrieve/rerank → gate → generate (llama-cpp) → verify → render | FastAPI retrieval service + model server + gate service + UI |
| Metadata and citations | Passage objects carry IDs end-to-end in memory; post-generation validator against the SQLite store | IDs serialized across APIs |
| Failure handling / reproducibility | try/except → fail-closed abstention; one YAML config, requirements.txt, seeds; gate trained in a separate notebook | Per-service timeouts; Docker compose |
| Colab feasibility / complexity | High / Low | Low / High; not needed for the assignment |

**ADR-001 (Accepted): Adopt Design A.** *Context:* two-person team, 3–4 weeks, free Colab/T4, single-user demo, evaluation as the priority. *Decision:* single-process Python package plus a separate evaluation notebook; llama-cpp-python for generation, FAISS + rank_bm25 for retrieval, SQLite/JSONL metadata, YAML config, JSONL logs. *Consequences:* fast iteration and identical code paths for demo and evaluation; not multi-user scalable; Design B deferred to the extension only if a deployment study is approved. *Invariants:* (1) a citation ID must exist in the store, or it is stripped and logged; (2) retrieved ≠ supporting, so only verifier-passed passages are rendered as "supporting"; (3) typed abstention states; (4) no probability displays unless calibrated with ECE reported, otherwise show the evidence state; (5) fail-closed on any component error.

---

## 13. Evaluation and stress-test design

**Metrics:**

| Metric | Definition | Labels needed | Failure revealed |
|---|---|---|---|
| Recall@k, MRR, nDCG@10 | Gold passage in top-k | Gold passage IDs | Retrieval misses |
| Coverage; selective accuracy/risk | Fraction answered; accuracy/error among answered | Correctness | Over-abstention; wrong answers |
| AURC | Area under risk–coverage curve over gate score (lower is better) | Correctness | Gate ranking quality |
| Unsupported-answer rate (HwSA) | Answer rate on items whose gold state is insufficient/contradictory | Evidence state | Core failure mode |
| False-abstention cost (FAC) | Abstention rate on answerable items the generator answers correctly with gold context | Correctness | Usefulness loss |
| Answerability P/R/F1, abstention accuracy | Gate decision vs gold state | Evidence state | — |
| Unsupported-claim rate | Answer sentences not entailed by cited passages (verifier + human audit) | Human audit subset | Hallucination inside answers |
| Citation precision/recall | ALCE definitions | Human audit subset | Wrong or irrelevant citations\[51\] |
| ECE (10 bins), Brier | On gate probabilities | Evidence state | Miscalibration |
| Utility U(λ) | (+1 correct supported answer, 0 abstain, −λ unsupported/wrong)/N | All | Prevents always-abstain wins |
| Latency p50/p95, peak VRAM, training GPU-hours | System cost | — | Feasibility |

An always-abstain system gets coverage 0, U = 0 and FAC = 100%, so it cannot win when coverage and U are reported alongside safety metrics. Correctness on course items is judged by a human rubric (correct / partially correct / incorrect against reference answer plus evidence); an LLM judge may assist only if its agreement with humans is measured on a sample.

**Stress conditions (applied identically to B2, B3 and G on paired items):**

| ID | Condition | Construction | Targets |
|---|---|---|---|
| S1 | Missing evidence | Remove gold sections from the index | Insufficient detection |
| S2 | Distractor retrieval | Replace 2 of 5 contexts with high-ranked non-answer passages | Robustness / FAC |
| S3 | Misleading evidence | Entity/number/formula swap in one gold passage copy | Sufficiency ≠ correctness (GRAB-RAG condition) |
| S4 | Contradictory sources | Keep original + edited copy | Contradiction state |
| S5 | Out-of-syllabus | Plausible DL questions absent from the corpus subset | Core failure mode |
| S6 | Paraphrase/held-out domain | Paraphrased questions; SQuAD-dev-derived open-retrieval set | Transfer (RQ3) |

**Ablations (on G):** −NLI verifier (answerability only); −answerability (NLI + reranker only); −calibration (raw scores, 0.5 threshold); −reranker; −hard negatives in gate training; optional embedder swap (bge-small vs Qwen3-Embedding-0.6B).

**Statistics:** paired bootstrap (10k resamples) for differences in AURC, HwSA, FAC and U; exact McNemar on per-item correct decisions; Holm correction across primary comparisons; report all results, including nulls.

**Error analysis:** tag failures as retrieval miss / gate false-accept / gate false-reject / verifier false-support (e.g., notation/math) / generator unfaithful / citation mismatch. Present 5–10 qualitative failure cases in the demo and paper.

---

## 14. Feasibility

- **Compute:** all inference components (4B Q4 LLM, small embedder, cross-encoders) fit a single T4; GRAB-RAG ran 3.8–8B Q4_K_M models on a 12 GB consumer GPU.\[5\] Gate training on subsampled SQuAD 2.0 is the heaviest step; measure it in Week 2 and subsample if needed.
- **Data and people:** no paid access (SQuAD and d2l are openly licensed); annotation (~20–40 person-hours) is the main labor cost. Checkpoint often to survive Colab session limits.

---

## 15. Milestones (plan only)

| Milestone | Mandatory? | Depends on | Owner |
|---|---|---|---|
| M1 Dataset & corpus prep (dataset card, provenance, SQuAD audit, corpus subset) | Mandatory | Faculty corpus approval | B (+A) |
| M2 Retrieval baseline (BM25, dense, hybrid, rerank; Recall@k) | Mandatory | M1 | A |
| M3 Grounded QA (B1, B2, B3; citation validator) | Mandatory | M2 | A |
| M4 Intervention (gate training, verifier, fusion, calibration) | Mandatory | M1, M3 | B |
| M5 Evaluation (baselines, S1–S6, ablations, stats, error analysis) | Mandatory | M3, M4, frozen test | B (+A) |
| M6 UI (Streamlit, evidence panel, typed abstentions) | Mandatory | M3 | A |
| M7 Reproducibility (requirements, seeds, YAML, notebook, model/dataset cards) | Mandatory | All | Both |
| M8 Academic deliverables (A–H, 4–6 page draft, demo video) | Mandatory | M5 | Both |
| Embedder upgrade, contextual chunks, conformal control, semantic entropy | Optional | M5 | — |

**3–4 week sequence aligned to the handbook:**
- **Week 1:** requirement spec (A) and dataset card draft (C); corpus approval request (d2l default); SQuAD audit; 5-paper initial review (P1, P2, P3, P4, P8); research question + H1 draft; start writing course items.
- **Week 2:** ingestion + index; B1/B2/B3 running with initial metrics; split audit; gate training run 1; finish annotation + κ; **freeze test set, H1, margin, λ and thresholds (pre-registration commit).**
- **Week 3:** calibrate on the calibration split; run all systems once on test + S1–S6 + ablations; bootstrap/McNemar; error analysis; baseline failure analysis write-up.
- **Week 4:** demo polish; plots (risk–coverage curves, reliability diagrams); reproducibility check on a fresh Colab; paper outline + contribution statements; LCA-3 presentation.

**Publication extension (Weeks 5–10, subject to approval):** enlarge the course test set and add a second course corpus (transfer); add RefusalBench/UAEval4RAG external stress sets; conformal risk control; optional small student pilot (needs ethics approval); full 4–6 page paper.

**Candidate venues (reputable, non-predatory; verify deadlines):** **BEA 2027** (22nd Workshop on Innovative Use of NLP for Building Educational Applications), which SIGEDU announced on 14 Oct 2026 will be held at NAACL 2027 in San Francisco;\[52\] its deadline is not yet found (BEA 2026's was 5 March 2026).\[53\] Other options [deadlines not verified]: AIED 2027, EDM 2027, ACM L@S 2027, ACL/EMNLP Findings or Industry tracks (Cite or Decline went to EMNLP 2026 Industry),\[15\] and the UncertaiNLP workshop. Avoid low-tier venues with irregular metadata; the JTIE paper's inconsistent submission/publication dates are an example.\[1\]

---

## 16. Research uncertainties

- **SQuAD-to-course transfer:** a gate trained on SQuAD 2.0 may not calibrate on course text, because SQuAD unanswerables are paragraph-local and lexically adversarial. Measure ECE on the course calibration split before trusting thresholds.
- **Verifier on maths:** MiniCheck/NLI on notation-heavy deep-learning content is unverified; math claims may be under-supported (false abstention).
- **Misleading evidence may stay unsolved:** GRAB-RAG shows no policy closes it without coverage loss.\[5\] Treat S3 as diagnostic, not as a success criterion.
- **Statistical power:** small course test sets give wide CIs; rely on paired tests and report effect sizes with CIs.
- **Licenses:** model-card licenses (rerankers, Phi-4-mini, Gemma 4) must be confirmed from live cards before freezing the stack.

## 17. Risks requiring user decisions

| Decision | Options | Recommendation |
|---|---|---|
| Course material | d2l.ai (CC BY-SA), OpenStax, MIT OCW, faculty slides with written permission | d2l subset (e.g., 6–10 chapters) unless faculty provide licensed materials; record ShareAlike obligations |
| Compute | Free Colab T4 vs local GPU | Free T4 baseline; checkpoint gate training; local GPU if available |
| Annotation effort | 150 vs 300 items | Target ~200; stop at the Week 2 freeze regardless |
| LLM-as-judge | None / assistive with audit | Human rubric primary; any judge only with a measured agreement sample |
| Coverage-loss margin and λ | Team- and faculty-set | Decide with the instructor in Week 1 and pre-register |
| Generator license | Apache (Qwen3, Granite) vs community (Llama) vs Gemma terms | Qwen3-4B primary; document licenses in model cards\[43\] |
| Gen-AI use in drafting items | Allowed with disclosure / forbidden | Allowed only for candidate drafting, with full human verification and disclosure |
| Publication path | BEA 2027 vs AIED/EDM/L@S | Target BEA 2027 if deadlines align; confirm faculty approval |

## Sources

1. [Evidence-Calibrated RAG for Unanswerable Question Answering: Retrieval Coverage, Abstention Calibration, and Hallucination-Proxy Analysis on SQuAD 2.0 | Journal of Technology Informatics and Engineering](https://jtie.stekom.ac.id/index.php/jtie/article/view/536)
2. [ICLR Poster Sufficient Context: A New Lens on Retrieval Augmented Generation Systems](https://iclr.cc/virtual/2025/poster/30092)
3. [Measuring and Enhancing Trustworthiness of LLMs in RAG through Grounded Attributions and Learning to Refuse](https://proceedings.iclr.cc/paper_files/paper/2025/hash/4c88827decab6c046b881a2c3a99c76f-Abstract-Conference.html)
4. [HALT-RAG: A Task-Adaptable Framework for Hallucination Detection with Calibrated NLI Ensembles and Abstention](https://arxiv.org/html/2509.07475)
5. [Prompt-Based Abstention Fails Under Misleading Context: A Controlled Study of Small Frozen RAG Models](https://arxiv.org/pdf/2608.22228)
6. [Dive into Deep Learning](https://d2l.smola.org/)
7. [ERIC - EJ1460241 - An LLM-Driven Chatbot in Higher Education for Databases and Information Systems, IEEE Transactions on Education, 2025-Feb](https://eric.ed.gov/?id=EJ1460241)
8. [Retrieval-Augmented Tutoring for Algorithm Tracing and Problem-Solving in AI Education](https://arxiv.org/html/2605.12988v1)
9. [Enabling Large Language Models to Generate Text with Citations](https://arxiv.org/html/2305.14627v1)
10. [(PDF) Sufficient Context: A New Lens on Retrieval Augmented Generation Systems](https://www.researchgate.net/publication/385721878_Sufficient_Context_A_New_Lens_on_Retrieval_Augmented_Generation_Systems)
11. [hallucination\_evaluation\_model](https://www.promptlayer.com/models/hallucinationevaluationmodel/)
12. [\[2511.17908\] Principled Context Engineering for RAG: Statistical Guarantees via Conformal Prediction](https://arxiv.org/abs/2511.17908)
13. [Response Quality Assessment for Retrieval-Augmented Generation via Conditional Conformal Factuality — Lacuna](https://lacuna.tiptreesystems.com/work/response-quality-assessment-for-retrieval-augmented-generation-via-conditional/wrk_942b6742456ad87d7a58e5317a732b67)
14. [Towards Dependable Retrieval-Augmented Generation Using Factual Confidence Prediction](https://arxiv.org/html/2605.05244)
15. [Cite or Decline: A Strict Course-Grounded Chatbot for STEM Lecture Videos](https://arxiv.org/abs/2609.01846)
16. [Know What You Don’t Know: Unanswerable Questions for SQuAD Pranav Rajpurkar∗ |](https://arxiv.org/pdf/1806.03822)
17. [Know What You Don’t Know: Unanswerable Questions for SQuAD](https://arxiv.org/html/1806.03822.pdf)
18. [GitHub - hljoren/sufficientcontext: Official page for ICLR 2025 paper "Sufficient Context: A New Lens on Retrieval Augmented Generation Systems" · GitHub](https://github.com/hljoren/sufficientcontext)
19. [Sufficient Context](https://iclr.cc/media/iclr-2025/Slides/30092_7awcPDv.pdf)
20. [MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents](https://arxiv.org/pdf/2404.10774)
21. [Enabling Large Language Models to Generate Text with Citations Tianyu Gao](https://arxiv.org/pdf/2305.14627v1)
22. [\[2407.18418\] Know Your Limits: A Survey of Abstention in Large Language Models](https://arxiv.org/abs/2407.18418)
23. [Know Your Limits: A Survey of Abstention in Large Language Models](https://www.researchgate.net/publication/393331033_Know_Your_Limits_A_Survey_of_Abstention_in_Large_Language_Models)
24. [Unanswerability Evaluation for Retrieval Augmented Generation - ACL Anthology](https://aclanthology.org/2025.acl-long.415/)
25. [Unanswerability Evaluation for Retrieval Augmented Generation](https://arxiv.org/pdf/2412.12300)
26. [Evidence-Calibrated RAG for Unanswerable Question ...](https://jtie.stekom.ac.id/index.php/jtie/article/download/536/347)
27. [RefusalBench: Generative Evaluation of Selective Refusal in Grounded Language Models](https://aclanthology.org/2026.eacl-long.321/)
28. [RAG Chunking Strategies: The 2026 Benchmark Guide](https://www.premai.io/blog/rag-chunking-strategies-the-2026-benchmark-guide/)
29. [Learning Fine-Grained Grounded Citations for Attributed Large Language Models](https://arxiv.org/pdf/2408.04568)
30. [vectara/hallucination\_evaluation\_model · Hugging Face](https://huggingface.co/vectara/hallucination_evaluation_model)
31. [GitHub - amazon-science/RAGChecker: RAGChecker: A Fine-grained Framework For Diagnosing RAG · GitHub](https://github.com/amazon-science/RAGChecker)
32. [GitHub - princeton-nlp/ALCE: \[EMNLP 2023\] Enabling Large Language Models to Generate Text with Citations. Paper: https://arxiv.org/abs/2305.14627 · GitHub](https://github.com/princeton-nlp/ALCE)
33. [RAG Citations and Fallbacks: Grounding, Abstention, and the Feedback Loop in 2026](https://heycc.cn/en/posts/rag-citations-and-fallbacks/)
34. [Best PDF to Markdown Converters, Tested on Real PDFs (2026) - Parsebridge](https://parsebridge.com/blog/best-pdf-to-markdown-converters/)
35. [PDF Parsing for RAG 2026: MinerU vs Docling vs Marker](https://builderai.tools/blog/pdf-parsing-for-rag-mineru-docling-marker-compared)
36. [Docling vs Marker, MinerU, PyMuPDF4LLM, MarkItDown & Unstructured (Tested 2026)](https://docling.org/compare/)
37. [READoc: A Unified Benchmark for Realistic Document Structured Extraction](https://arxiv.org/pdf/2409.05137)
38. [Best free open-source embedding models 2026](https://supermemory.ai/blog/best-open-source-embedding-models-benchmarked-and-ranked/)
39. [Embedding models comparison: OpenAI, Google, Qwen, Nomic, more](https://surrealdb.com/blog/embedding-models-comparison)
40. [Qwen/Qwen3-Embedding-0.6B · Hugging Face](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
41. [Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models](https://arxiv.org/pdf/2506.05176)
42. [GitHub - phlx0/awesome-open-weight-models: The practitioner's guide to open-weight LLMs — benchmarks, licensing, hardware, deployment, fine-tuning · GitHub](https://github.com/phlx0/awesome-open-weight-models)
43. [The Best Open Source and Open-Weight LLM Models to Run Locally in 2026](https://huggingface.co/blog/daya-shankar/open-source-llm-models-to-run-locally)
44. [Open-Source LLMs for Developers: Models, Agents & Local AI](https://codetocloud.io/blog/open-source-llms-developers/)
45. [Gemma (language model)](<https://en.wikipedia.org/wiki/Gemma_(language_model)>)
46. [Open Weights: The Ultimate Guide (2026 Edition)](https://blog.prompt20.com/posts/open-weights-ultimate-guide/)
47. [Know What You Don’t Know: Unanswerable Questions for SQuAD Pranav Rajpurkar∗](https://nlp.stanford.edu/pubs/rajpurkar2018squad.pdf)
48. [SQuAD v2.0 Dataset (complete excel file)](https://www.kaggle.com/datasets/pragyakatyayan/squad-v20-dataset-complete-excel-file)
49. [README.md · rajpurkar/squad\_v2 at main](https://huggingface.co/datasets/rajpurkar/squad_v2/blob/main/README.md)
50. [d2l-en/LICENSE at master · d2l-ai/d2l-en · GitHub](https://github.com/d2l-ai/d2l-en/blob/master/LICENSE)
51. [Training Language Models to Generate Text with Citations via Fine-grained Rewards](https://arxiv.org/pdf/2402.04315)
52. [ACL SIGEDU - SIGEDU](https://sig-edu.org/)
53. [BEA 2026 : 21st Workshop on Innovative Use of NLP for Building Educational Applications](http://wikicfp.com/cfp/servlet/event.showcfp?eventid=191789)
