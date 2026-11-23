# LearnMate Pre-registration (copy to research/preregistration.md, fill, then set STATUS: FROZEN)

STATUS: DRAFT            <!-- change to "STATUS: FROZEN" only at the freeze commit; eval.run checks this line -->

- Date / commit: ______
- Course items manifest sha256 (data/manifests/course_items_manifest.json): ______
- Frozen thresholds sha256 (configs/frozen/thresholds.json): ______
- Prompt version / hash (learnmate.prompts.prompt_hash()): P_v1 / ______
- Generator: Qwen/Qwen3-4B-Instruct-2507 @ cdbee75f…, runtime: hf / dtype ______ (fp16 or nf4, from M0)
- Gate checkpoint: models/gate-v1/best (train_log.json sha256 ______)
- Analysis code: eval/analyze.py @ commit ______

## Hypotheses (unchanged from research/final_research_problem.md §5)
- **H1 (primary):** on course-test, paired-bootstrap 95% CI (10,000 resamples, seed 2026) of AURC(G) − AURC(B2) lies
  entirely below 0, AND answerable-coverage(G) ≥ answerable-coverage(B2) − m.
- H1b, H1c, H1d as specified; Holm correction over {H1b, H1c, H1d}.

## Fixed values
- m (coverage-loss margin) = ____ pp   (default 10; instructor-confirmed? Y/N)
- λ (utility, threshold selection) = ____ (default 2); reported λ ∈ {1, 2, 4}
- s_min = 0.5; κ_c = ____ (from dev S4)
- Error definition: strict (partially_correct = error); lenient reported as sensitivity analysis.

## Runs that will be executed once
course-test × {clean, S1, S2, S3, S4}; squad-test × clean. Systems B1, B2, G, A1–A5 (+B0 on squad-test).
Any analysis not listed here will be labelled **exploratory**.
