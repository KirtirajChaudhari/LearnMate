# Deliverable B: Literature Review Matrix (G06 LearnMate)

Verification status: **V** = identifier/venue checked against a primary page or model card; **PV** = paper exists and venue/identifier consistent across sources, but the specific numbers were not re-read from the primary text. **No number from a PV source is quoted in the paper.** Full audit trail: `research/verified_sources_and_corrections.md`.

| # | Paper (year, venue) | DOI / URL | Method | Dataset | Limitation | Proposed gap for LearnMate | Status |
|---|---|---|---|---|---|---|---|
| 1 | Joren et al., *Sufficient Context: A New Lens on RAG Systems* (ICLR 2025) | arXiv 2411.06037 | Context-sufficiency autorater + self-rated confidence → logistic selective generation | FreshQA, HotpotQA, MuSiQue | Large (24B-class) autorater; open-domain QA, no course setting | Small *trained* local gate, evaluated on course text | PV |
| 2 | Song et al., *Trust-Align* (ICLR 2025) | arXiv 2409.11242 | DPO alignment for grounded citations and refusal; Trust-Score | ASQA, QAMPARI, ELI5, ExpertQA | Needs generator training; not course-specific | Abstention without training the generator | PV |
| 3 | Tang, Laban & Durrett, *MiniCheck* (EMNLP 2024) | 10.18653/v1/2024.emnlp-main.499 | Small fact-checkers on synthetic data; GPT-4-level grounding at about 400× lower cost (per abstract) | LLM-AggreFact | Not tested on notation-heavy course text; binary support only | Used as the claim-level verifier; math slice reported | V |
| 4 | Niu et al., *RAGTruth* (ACL 2024) | 10.18653/v1/2024.acl-long.585 | Human-annotated RAG hallucination corpus; taxonomy incl. *implicit truth* | RAGTruth (QA, summarisation, data-to-text) | General domains, not coursework | Taxonomy used for error analysis | PV |
| 5 | Kovács & Recski, *LettuceDetect* (arXiv 2025) | arXiv 2502.17125 | ModernBERT token-level hallucination detector | RAGTruth | Single benchmark; scores against whole context, so cannot attribute a claim to one citation | Used only as an independent secondary evaluator | V (model card) |
| 6 | Kirichenko et al., *AbstentionBench* (NeurIPS 2025 D&B) | arXiv 2506.09038 | 20-dataset abstention benchmark over 20 LLMs | 20 datasets | Not RAG-specific; no verification pipeline | Motivates not relying on prompt abstention or reasoning models | V |
| 7 | Setiawan, *Prompt-Based Abstention Fails Under Misleading Context* (AACL 2026) | arXiv 2608.22228 | Paired supportive/degraded/missing/misleading contexts on small frozen models | NQ, HotpotQA | No trained/calibrated gate; open-domain | Course-tutor setting with a trained, calibrated gate | V |
| 8 | Peng et al., *Unanswerability Evaluation for RAG, UAEval4RAG* (ACL 2025) | aclanthology 2025.acl-long.415 | Synthesises unanswerable query categories per knowledge base | Any KB | Synthetic, LLM-judged | Category taxonomy used to design missing-detail items | PV |
| 9 | Wallat et al., *Correctness is not Faithfulness in RAG Attributions* (ICTIR 2025) | 10.1145/3731120.3744592 | Separates citation correctness from causal faithfulness | Attributed-RAG evaluation | One model family | Motivates the withheld-gold stress test S1 | PV |
| 10 | Yu et al., *Integrating SLMs with RAG in Computing Education* (SIGCSE 2025) | 10.1145/3641554.3701844 | Local small-model + RAG tutor deployed in CS1 | University course logs | No verification or calibrated abstention | Adds verified citations and abstention | PV |

**Foundational works also cited:** Rajpurkar, Jia & Liang, *SQuAD 2.0* (ACL 2018, arXiv 1806.03822); Gao et al., *ALCE* (EMNLP 2023, 10.18653/v1/2023.emnlp-main.398); Kamath, Jia & Liang, *Selective QA under Domain Shift* (ACL 2020, 10.18653/v1/2020.acl-main.503); Goswami & Kurra, *HALT-RAG* (arXiv 2509.07475); Seo & Jang, *When Retrieval Similarity Hurts* (Findings of EMNLP 2026; anthology entry pending, so not quoted).

## Falsifiable hypothesis (H1)
On the locked course test items, the paired-bootstrap 95% CI of AURC(G) − AURC(B2) is entirely below 0 and answerable coverage drops by at most 10 percentage points. H0: otherwise.

## Proposed gap (stated without a novelty claim)
Sufficiency-based selective generation, claim-level verification and calibrated NLI detectors each exist. We found no study that combines a *small trained* answerability gate with claim-level verification in a *local course-tutor* setting and tests it against a tuned reranker-score threshold under withheld-evidence stress on an independently labelled course set. This is a replication-plus-adaptation and a controlled evaluation, not a new algorithm. A negative result is a valid outcome.
