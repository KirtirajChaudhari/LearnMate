# Requirements Traceability (Handbook → Specification → Evidence)

HB = `research/inputs/CCA2_LCA3_MTech_Deep_Learning_Research_Challenges.pdf`. "Spec" points to documents in `research/`. Status: ☐ planned · ◐ in progress · ☑ done.

## 1. Handbook rules and tasks

| ID | Handbook requirement (section) | Where satisfied (spec) | Evidence artifact | Milestone | Status |
|---|---|---|---|---|---|
| R1 | Exactly two members; one challenge (§2) | Owner split A/B in roadmap | Deliverable H contribution statement | M9 | ☐ |
| R2 | LCA-3 in 3–4 weeks; extension 6–8 weeks subject to approval (§2, §8) | `implementation_roadmap.md` | Milestone tags | M0–M9 | ☐ |
| R3 | Python + PyTorch/TF; Colab OK (§2) | ADR-001/003; `final_architecture.md` §5 | `requirements.lock`, notebooks | M0 | ☐ |
| R4 | UI (Streamlit/Gradio) not a substitute for evaluation (§2) | ADR-011; C11 vs C12 separation | Streamlit app + separate eval harness | M8/M7 | ☐ |
| R5 | Public/licensed data; record source, version, access date, conditions, preprocessing (§2, §7C) | `dataset_and_annotation_plan.md` §1–2, §8 | Dataset card; manifests with SHA-256 | M1/M9 | ◐ (licenses verified) |
| R6 | ≥2 meaningful baselines where feasible (§2, §3 T3) | B1 prompt-only, B2 strong CE-threshold, B0 reference | Table 2 | M3/M7 | ☐ |
| R7 | Test one application-specific failure mode (§2) | Unsupported answering on insufficient-evidence questions; S1 withheld gold | E1/E3 results | M7 | ☐ |
| R8 | Novelty is a hypothesis, no guaranteed publication (§2, §9) | `final_research_problem.md` §6 (no algorithmic novelty claim) | Paper framing | M9 | ◐ |
| R9 | T1 problem definition: stakeholders, use case, I/O, constraints, measurable success criterion (§3) | `final_research_problem.md` §1, §5, §8; MDR §2 stakeholder table (reused) | Deliverable A | M1 | ☐ |
| R10 | T2 8–10 papers (2024–26), matrix, one falsifiable hypothesis (§3) | `verified_sources_and_corrections.md` §6; H1/H0 | Deliverable B | M1 | ◐ |
| R11 | T3 licensing, leakage-safe train/val/test splits, ≥1 strong baseline (§3) | Dataset plan §1, §3, §7; B2 | Split manifests + leakage tests | M1/M5 | ☐ |
| R12 | T4 one justified change; controlled stress test; ablation; error analysis (§3) | Intervention G; S1–S4; A1–A5; error taxonomy | Tables 3, 4, 6 | M4–M7 | ☐ |
| R13 | T5 working prototype, reproducible notebook, results tables, 4–6 page draft (§3) | Roadmap M8/M9 | App, notebooks, draft | M8/M9 | ☐ |
| R14 | G06: course-specific document-grounded assistant that cites sources and abstains (§5) | C7, C9, C10 policy | Demo + citation-validity invariant | M3/M6/M8 | ☐ |
| R15 | G06 suggested archs: Sentence Transformers, small LLM, RAG (§5) | bge-base (Sentence Transformers), Qwen3-4B, RAG | Code | M2/M3 | ☐ |
| R16 | G06 research direction: evidence agreement & calibrated abstention (§5) | Verifier (agreement) + calibrated fusion (abstention) | E1, ECE | M6/M7 | ☐ |
| R17 | G06 datasets: SQuAD 2.0 + approved course materials (§5) | SQuAD (gate training, cal, secondary test); d2l provisional | Dataset card | M1 | ◐ (approval pending) |
| R18 | G06 feasibility: independently checked course evaluation set (§5) | Dataset plan §4 (blind cross-labelling, κ, adjudication) | κ report | M5 | ☐ |
| R19 | G06 T1 quantify failure mode (§5) | HwSA/FAC on baselines (W2–W3) | Baseline failure analysis | M3/M7 | ☐ |
| R20 | G06 T2 justify two baselines among suggested approaches (§5) | `final_research_problem.md` §7 | Paper §Baselines | M9 | ◐ |
| R21 | G06 T3 audit SQuAD 2.0 + materials: labels, split, leakage, limitations (§5) | Dataset plan | Dataset card | M1 | ◐ (counts verified) |
| R22 | G06 T4 ablation + ≥1 held-out or stressed condition (§5) | A1–A5; S1 (+S2–S4); squad-test held-out | Tables 3–4 | M7 | ☐ |
| R23 | G06 T5 prototype, metrics, limitations, reproducibility, paper outline (§5) | Roadmap M8/M9 | All | M9 | ☐ |
| R24 | Suggested RAG metrics: answer support, abstention accuracy, human-checked factuality; compute cost (§6) | Protocol §5, §9 | Table 2 | M7 | ☐ |
| R25 | Report all experiments truthfully incl. negative findings (§9) | Protocol §1, §6 | Results incl. nulls | M7/M9 | ☐ |
| R26 | Cite datasets, code, models; respect licenses/privacy (§9) | VS §1–3; attribution in UI | References, model/dataset cards | M9 | ◐ |
| R27 | Do not tune on final test set; group-aware splits (§9) | Pre-registration; section/article splits; test-run guard | `prereg-v1` tag, guard test | M5–M7 | ☐ |
| R28 | Transparent generative-AI use (§9) | `genai_assisted` field; disclosure section | Paper + README | M9 | ☐ |
| R29 | Reputable venues; avoid guaranteed-acceptance venues (§9) | Roadmap extension; JTIE excluded from matrix | Venue note | Ext. | ◐ |
| R30 | Faculty approval sheet: dataset access/licence, gap, compute (§10) | `development_readiness.md` blockers | Signed sheet | W1 | ☐ |

## 2. Mandatory submission package (§7)

| Deliverable | Content | Produced from | Milestone |
|---|---|---|---|
| A | Problem statement + 1-page requirement spec (PDF) | `final_research_problem.md` §1–2, MDR §2 FR/NFR tables | M1 |
| B | Literature matrix 8–10 papers (DOI/URL, method, dataset, limitation, gap) | VS §6 matrix, expanded with method/dataset/limitation columns | M1 |
| C | Dataset card | Dataset plan §8 + real counts | M1→M9 |
| D | Code/Colab notebook, requirements, seeds, run instructions | Repo + `requirements.lock` + notebooks | M0→M9 |
| E | Results: baseline comparison, failure/stress test, ablation, plots, error analysis | `results/test_v1` + protocol §10 | M7 |
| F | Demo (live or 3–5 min video) | Streamlit app | M8/M9 |
| G | 4–6 page conference-style draft | Results JSON only | M9 |
| H | Contribution statement per member | Git history + roadmap owners | M9 |

## 3. Rubric alignment (§6, 30 marks)

| Criterion | Marks | Primary evidence |
|---|---|---|
| Problem framing & requirements | 4 | Deliverable A; failure-mode quantification on baselines |
| Literature & justified gap | 6 | Deliverable B; reconciliation + corrections (shows verification) |
| Dataset audit & baseline implementation | 8 | Dataset card with verified counts; B1/B2 (+B0) working; leakage tests |
| Stress testing, metrics, preliminary analysis | 7 | S1–S4, A1–A5, AURC/HwSA/ECE, error taxonomy |
| Prototype demo, reproducibility, paper outline | 5 | Streamlit demo, fresh-Colab reproduction, draft |

## 4. User-brief invariants (Phase II handoff)

| Invariant | Mechanism | Test |
|---|---|---|
| Every displayed citation resolves to an indexed passage | C9 validator + provenance store | `tests/test_citations.py` property test |
| Cited ≠ supporting distinguished | MiniCheck support ≥ s_min required for "supported" badge | `tests/test_policy.py` |
| Unsupported claims flagged/handled | Partial state pruning; insufficient abstention | `tests/test_policy.py` |
| No parametric knowledge presented as course-supported | Prompt + verifier; U2 out-of-syllabus category measured | E1 HwSA on U2 |
| Policy for sufficient/insufficient/partial/contradictory | C10 rules | Each state reachable test |
| Not relying only on "say I don't know" | Trained gate + verifier + calibrated threshold | A1/A2/A3 ablations |
| Same model not both decision component and sole evaluator | MiniCheck decides; humans judge; LettuceDetect secondary | Protocol §4 |
| No success by frequent abstention | AURC primary; coverage margin m; U(λ) | H1 definition |
