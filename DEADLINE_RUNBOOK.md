# Deadline Runbook: reduced but honest submission

**Rule: no number goes into the paper unless it comes from a file produced by these steps.** Results will be *preliminary*: about 55 course items means wide confidence intervals, and the paper says so.

Times are relative to when you start (T+0). Total: about 10 h of work for each of you spread over about 20 h, with most GPU time unattended. **A** and **B** are the two group members. If anything fails, paste me the exact error and I'll fix it.

## T+0: start the GPU immediately (one person, ~45 min of waiting)
1. Colab → File → Open notebook → GitHub → `KirtirajChaudhari/LearnMate`, branch `claude/wonderful-bohr-1idsaa`. If the repo is private, put a read-only token in the clone URL. Runtime → **T4 GPU**.
2. Run `notebooks/00_smoke_colab.ipynb` top to bottom. It writes `results/m0_smoke.json` (VRAM and speed per model; it tells us fp16 vs NF4).
3. Immediately open `notebooks/03_deadline_run.ipynb`, run **all cells down to the first STOP**:
   - builds indices;
   - trains the gate (~24k pairs, 1 epoch, ≈ 10–30 min, unmeasured);
   - runs the 300-question SQuAD calibration set;
   - calibrates and writes the thresholds.
   About 2–3 h, unattended. If Colab disconnects, rerun the *same* cell; everything resumes from cache.

## T+0 to T+1.5 h: both of you verify your items (≈ 1 h each, in parallel)
57 questions were drafted by an AI assistant from the course text (disclosed in the data and in the paper). **They only count after a human accepts them.**
```bash
git pull
python scripts/review.py verify --member A      # B runs it with --member B
```
For each item:
- **Accept** if the question is clear and the reference answer is true according to the shown course text.
- **Edit** if a wording fix is enough.
- **Reject** anything dubious. For partial and out-of-syllabus items, also check that the `NEAR` passages do **not** answer it.

Then push only your decisions file:
```bash
git add data/annotations/decisions_A.jsonl && git commit -m "A: verified items" && git pull --rebase && git push
```

## T+1.5 to T+3 h: blind second labels (≈ 40 min each)
This is the "independently checked" part. You label the *other* member's items without seeing their labels.
```bash
git pull
python scripts/review.py second-label --member A     # labels B's items; B labels A's
git add data/annotations/labels_A.jsonl && git commit -m "A: blind labels" && git pull --rebase && git push
```
Then anyone: `git pull && python scripts/review.py apply && python -m learnmate.annotation kappa` → note κ. If κ is low, **don't redo**. Report it and discuss the disagreements.

## T+3 to T+6 h: freeze and the locked test runs (Colab, mostly unattended)
Push everything, then run the notebook-03 cells after STOP, in order. They:
1. pull and merge the decisions;
2. validate (every item must be accepted or rejected, or freezing refuses);
3. assign all items to the **test** split;
4. freeze the items and write `research/preregistration.md` (**after this the test runs are unlocked and nothing may be tuned**);
5. run course-test (`clean`, `S1`) and squad-test, ≈ 1–2 h.

## T+6 to T+8 h: judge the test outputs (≈ 1 h each)
The notebook creates `data/annotations/judge_test.jsonl` plus a `_KEY_DO_NOT_OPEN` file. Commit and push both (do not open the key), then:
```bash
git pull
python scripts/review.py judge --sheet data/annotations/judge_test.jsonl --member A     # B: --member B
git add data/annotations/verdicts_A.jsonl && git commit -m "A: verdicts" && git pull --rebase && git push
```
You can't see which system wrote an answer. Each output is assigned to the member who did **not** author the item. Then run the merge and analysis cells in notebook 03.

## T+8 h: send me these files and I'll write the results
- `results/runs/course-test__clean/analysis.json`, `course-test__S1/analysis.json`, `squad-test__clean/analysis.json`
- `models/gate-v1/train_log.json`, `results/m0_smoke.json`, `data/manifests/course_items_manifest.json`

I'll then fill the results, ablation and error-analysis sections in `submission/G_paper_draft.md`, with the figures.

## In parallel while the GPU runs and between judging sessions
- **Paper:** read `submission/G_paper_draft.md`. Sections 1–5 and 8 are already written and don't depend on results.
- **Demo video (3–5 min):** run the last cell of notebook 03 (Streamlit via a tunnel), then screen-record:
  1. a normal question with citations, and click a citation to open the stored passage;
  2. an out-of-syllabus question (e.g. "How does a GAN train its discriminator?") → abstention with "related, not supporting" sections;
  3. the same question under B1 (prompt-only), to show the difference;
  4. one real failure case from your error analysis.
- **Deliverables A, B, H:** drafts are in `submission/`. Fill names and dates. H must state the work you **actually** did.

## What is deliberately not in this submission, and is stated as a limitation
Fewer than the planned 150–200 items; no dev/calibration split on course items; thresholds fitted on SQuAD only; stress conditions S2–S4 not run; ablation A4 (no hard negatives) not run; one judge per output with no double-judging; no formal selective-risk guarantee. These are listed in `research/preregistration.md` once frozen.

## If you run out of time, cut in this order
1. squad-test run. 2. S1. 3. Figures other than risk–coverage. **Never cut:** judging course-test, the H1 analysis, ablations A1/A2/A3/A5 (these cost nothing: they are feature subsets).
