# LearnMate (G06) — Project Status

**Phase:** II (development) in progress. **Last updated:** 23 Nov 2026
**Code status:** The full pipeline and evaluation harness are implemented and tested (35 passing tests). The pipeline runs end to end on real data, so far only as CPU smoke runs.
**Blocked on:**
1. A GPU runtime for reportable runs.
2. Human authoring and judging of the course evaluation set.
3. Faculty approval of the corpus.

No experimental results exist yet, and none have been fabricated.

## Specification
The frozen specification v1.0 is in `research/`. Every deviation from it is recorded with its reason in [`research/implementation_log.md`](research/implementation_log.md) (D1–D15).

## Milestones

| Milestone | Code | Real run | Notes |
|---|---|---|---|
| M0 Setup and smoke | ☑ | ◐ | CPU: 6 models verified (`results/m0_smoke.json`), CPU lockfile. **GPU:** generator fp16 vs NF4 and GPU lockfile still to run (notebook 00) |
| M1 Data and ingestion | ☑ | ☑ | d2l @ `23d7a5a` → 1,242 chunks. SQuAD splits audited (dev = 35 articles). Dataset card v0.2 (`docs/dataset_card.md`) |
| M2 Retrieval | ☑ | ☑ | squad-cal, 750 answerable: hybrid+CE R@5 **0.988**, MRR **0.935**; dense R@5 0.943 (`results/retrieval_squad-cal.json`). Course-dev retrieval eval awaits course items |
| M3 Generation, B0/B1/B2 | ☑ | ◐ | Prompt P_v1, HF and llama.cpp backends, cache, citation validator, verbal-abstention detection. CPU smoke only (`results/smoke/generation_smoke.json`) |
| M4 Gate and verifier | ☑ | ◐ | MiniCheck reimplementation matches the official package to 1e-7. Gate training pipeline runs on CPU (smoke). **The real DeBERTa-v3-base training needs a GPU** (notebook 01) |
| M5 Annotation freeze and pre-registration | ☑ tooling | ☐ | `annotation/GUIDELINES.md` and `python -m learnmate.annotation …`. **The ~200 items must be written by the two members** |
| M6 Calibration | ☑ | ☐ | `eval.calibrate`. Needs squad-cal and course-cal runs plus course-cal judgments |
| M7 Experiments | ☑ | ☐ | `eval.run` (staged, stress S1–S4, pre-registration guard), `eval.analyze` (H1, ablations, McNemar, Holm), figures |
| M8 UI | ☑ | ◐ | Streamlit app, tested with a mocked pipeline. G mode needs the trained gate and frozen thresholds, and fails closed until they exist |
| M9 Reproducibility and deliverables | ◐ | ☐ | README, Colab notebooks 00–02, dataset card, lockfile. Paper, video and contribution statement come after results |

## Next actions, in order
1. **GPU:** open `notebooks/00_smoke_colab.ipynb` on a Colab T4. It records VRAM and latency, decides fp16 vs NF4, and writes `requirements.lock`.
2. **GPU:** run `notebooks/01_gate_training.ipynb` to train `gate-v1` and `gate-noHN`. Training time and VRAM are logged.
3. **Both members, starting now:** author course items following `annotation/GUIDELINES.md` (target 200, floor 150), then blind cross-label and compute κ.
4. **Instructor:** approve the d2l chapter subset or supply materials; confirm m = 10 pp and λ = 2.
5. **GPU:** run notebook 02 part 1 (squad-cal, course-dev and course-cal runs), judge course-cal outputs, calibrate.
6. Freeze: run `annotation freeze`, write `research/preregistration.md` with `STATUS: FROZEN`, and tag `prereg-v1`.
7. **GPU:** run the locked test runs once, judge them blind, run `eval.analyze` and `scripts/make_figures.py`, then the paper draft.

## Measured facts (not experimental results)
Retrieval quality on squad-cal, CPU latencies (generation ≈ 30–50 s per answer on 4 vCPU) and parity checks are listed in `research/implementation_log.md`.
