# LearnMate Pre-registration

STATUS: FROZEN

- Frozen at (UTC): 2026-11-24T01:55:09+00:00
- Code commit: 68a6bdc23bf38fb460bd23cfa79a33c621663aa3
- Course items manifest sha256: b87927b0c8a86610e613dcfeb41712c69e3e344ae4de3d73365d1c35076516c2  (57 items; splits {'test': 57}; kappa(gold state) = None)
- Frozen thresholds sha256: 80a629cbadd4962c63122e238f323e4c9c3ba5112033facdae81d4783983e879
- Threshold profile: deadline: fusion, tau and B2/B0 thresholds fitted on squad-cal only (no course-cal, no Platt)
- Prompt: P_v1 / hash 56cdaceabf3e
- Generator: Qwen/Qwen3-4B-Instruct-2507 @ cdbee75f17, dtype float16, greedy decoding
- Gate checkpoint: models/gate-v1/best  (train_log sha256 966c44d6698a69a4aea7de3641f350844ee80506991f546192e3caa69d6be5a6)
- Analysis code: eval/analyze.py (commit above)

## Hypothesis (research/final_research_problem.md section 5, unchanged)
H1: on the course test items, the paired-bootstrap 95% CI (10,000 resamples, seed 2026) of AURC(G) - AURC(B2) lies entirely
below 0, AND answerable-coverage(G) >= answerable-coverage(B2) - m.
H1 is evaluated once, on course-test, condition `clean`. Everything else is secondary/descriptive.

## Fixed values
- m = 10 percentage points (team-set; instructor confirmation: pending)
- lambda = 2.0 for threshold selection; reported lambda in {1, 2, 4}
- s_min = 0.5; kappa_c = None (None = contradiction state disabled: no dev S4 items were built)
- Error definition: strict (partially_correct counts as an error)

## Documented deviations from the frozen specification (time-compressed submission profile)
1. Course set is smaller than the 150-item floor and is used entirely as the locked test set (no course-dev / course-cal).
2. Fusion weights, tau, tau_CE and tau_B0 are fitted on squad-cal ONLY, in-sample, without Platt recalibration; they are applied to course-test with no domain adaptation.
3. Gate trained on a reduced pair budget (see train_log.json); ablation A4 (no hard negatives) not run.
4. SQuAD-RAG sets use {'squad-cal': 300, 'squad-test': 200} questions instead of 1,500 per split.
5. Stress conditions S3, S4 not run; S2 not run (no judging capacity); S1 is run. Human judging was done by one member per output (the member who did not author the item), without double-judging.
6. Course items were drafted by an AI assistant from the corpus text and then verified, edited or rejected by the two members, each of whom also labelled the other's items blind (disclosed per item: genai_assisted=true).

## Runs executed once after this commit
course-test x {clean, S1}; squad-test x clean. Systems B1, B2, G, A1, A2, A3, A5 (+B0 on SQuAD). Anything else is exploratory.
