# Deliverable H: Contribution Statement (G06 LearnMate)

**Fill in what each member actually did, and delete anything that is not true.** Git history (`git shortlog -sn`, `git log --author=...`) is the evidence.

| Task | Member A | Member B |
|---|---|---|
| Colab runs (smoke test, gate training, experiment runs) | ☐ | ☐ |
| Verifying the AI-drafted course items (items authored: A = items `LM-A-*`, B = items `LM-B-*`) | ☐ | ☐ |
| Blind second labelling of the other member's items | ☐ | ☐ |
| Judging system outputs (each member judged the outputs for items the *other* authored) | ☐ | ☐ |
| Instructor communication / corpus approval | ☐ | ☐ |
| Demo recording | ☐ | ☐ |
| Paper sections (list) | ______ | ______ |
| Slides / presentation | ______ | ______ |

## Disclosure of generative-AI assistance (required by handbook §9)
An AI coding assistant (Claude Code, Anthropic) was used to:
- reconcile two research reports and write the specification (`research/`);
- write the software (`learnmate/`, `eval/`, `app/`, `scripts/`, notebooks) and its tests;
- **draft the candidate course evaluation questions and reference answers from the corpus text**. Every item carries `genai_assisted: true`. No item counts unless a group member accepted it (`human_verified`), and members edited or rejected items where needed. The assistant did not see any system output when drafting, and the held-out test set was not used to change any prompt, threshold or model.

- **prepare suggested verdicts for the judging step.** For the 72 outputs to answerable questions, the assistant read the blinded judging sheet (it did not open the system key) and wrote a suggested verdict and reason (`data/annotations/suggestions_test.jsonl`). Each judge saw the suggestion and pressed Enter to accept it or typed a different verdict; 66 were accepted and 6 were overridden (judge A 3, judge B 3), and the judge's choice is the recorded verdict (`verdicts_A.jsonl`, `verdicts_B.jsonl`, fields `ai_suggested` and `overridden`). Judge B first marked seven of the suggested non-"correct" verdicts as correct and re-judged them as partially correct after the assistant flagged them; both versions are in the git history. The verdicts are therefore **AI-suggested, human-confirmed**, not independent human judgments.
- **Known process failures, reported in the paper:** the first blind second-labelling attempt was invalid and not repeated; the pre-registration was regenerated once; gate training time was not measured.

The assistant did **not** produce any experimental number: every number in the paper is computed by the code from logged runs (`results/`) and human judgments (`data/annotations/verdicts_*.jsonl`). Members are responsible for the final text and claims.

**Signatures / date:** ______________________
