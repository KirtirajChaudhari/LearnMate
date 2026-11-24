# LearnMate G06 (short deck): speaker notes

Two presenters: agree the split yourselves; nothing here assigns sections.

## Slide 1: Course
documents

Open by stating the status: the system is built and evaluated once on a locked test set; the headline result is a preliminary null on our registered hypothesis, and the deck is honest about that. Placeholders in brackets (institution, names, guide, date) must be filled before presenting. Two presenters: agree the split between you in advance; nothing in this deck assigns sections to either member.

## Slide 2: A plausible answer is not the same as a supported answer

Explain the three cases. Case 1 is the goal: the course passage entails the answer and it is cited. Case 2 is the subtle failure: the statement may be true in the world, but the course text shown to the student does not say it, so for a course tutor it is unsupported. Case 3 is the dangerous one: an out-of-syllabus question that should be refused with pointers to related sections. Examples are drawn from our own evaluation set and smoke test, shown for illustration only. Transition: the handbook makes exactly this the assigned challenge.

## Slide 3: The assigned research challenge: G06 LearnMate

This slide is traceable to page 5 of the handbook. Read the problem statement, then point out the split: the left column is what the prototype must do; the right column is what the research must show. The handbook also says to check whether the approach is already published, which is why our framing is a controlled evaluation and not a novelty claim. Transition: what has the literature established?

## Slide 4: Literature review: key studies and what they leave open

Pick two rows to talk through. Joren et al. propose using context sufficiency to guide selective generation, with large autoraters; we ask whether a small trained local gate transfers to course text. Setiawan shows prompt-only abstention is fragile under misleading context, which is exactly our B1 baseline. Wallat separates citation correctness from faithfulness, motivating our withheld-gold stress test. The full 10-paper matrix is in Deliverable B. Be explicit that we did not re-read numbers from the primary texts for every source; no quantitative claim from those papers is used in this deck.

## Slide 5: Research gap: a controlled evaluation, not a new algorithm

State the gap precisely and modestly. Each ingredient exists: sufficiency-based selective generation, claim-level verification, calibrated detectors. We found no study combining a small trained answerability gate with claim-level verification in a local course-tutor setting and testing it against a tuned reranker-score threshold under withheld-evidence stress on an independently labelled course set. That is a replication-plus-adaptation. A negative result is a valid outcome, and our first test result is negative on the registered hypothesis.

## Slide 6: Objectives and a falsifiable hypothesis, registered before testing

Read the research question, then the hypothesis. H1 is deliberately demanding: it requires the whole confidence interval of the AURC difference to be below zero, and a limit on lost coverage. The tolerance m of 10 percentage points was set by the team and is flagged as pending instructor confirmation. Emphasise the pre-registration: the document was frozen with hashes before any test output was produced, and the analysis code and thresholds were fixed. Transition to the architecture.

## Slide 7: System architecture as implemented

This is the system as built, not a plan. The top row is offline preparation: the open textbook is parsed with provenance, chunked at section boundaries into 1,242 passages, and indexed with BM25 and BGE embeddings. The bottom row is online: hybrid retrieval with reciprocal-rank fusion and a cross-encoder rerank, then a trained sufficiency gate, grounded generation by Qwen3-4B with bracketed citations, claim-level verification with MiniCheck and an NLI model, and a fusion step that outputs a typed decision. Fail-closed: any component error leads to abstention. Colours encode function; the legend sits below.

## Slide 8: Technology selection: what we reused, trained and wrote

These are final choices as implemented, with pinned revisions recorded in the repository. Note what was evaluated but not adopted in the research reports: LettuceDetect is used only as an optional secondary evaluator and not as a decision component; MiniCheck is a decision component and is never used to evaluate itself. The generator fits on a free T4 in fp16 (8.1 GB peak measured in the smoke test); NF4 halves that. Selection rationale is cost, licence, and fit to a free T4.

## Slide 9: Beyond RAG: when should the tutor answer?

The policy has four typed outcomes. Sufficient evidence: answer with citations. Partial: answer only what is supported and say what is not covered. Insufficient: abstain and show nearby sections labelled related, not supporting. Contradictory: disclose the conflict. Be honest that in the frozen test run the contradiction state was disabled, because we built no development items for it; so the result slides cover three effective outcomes. The decision is a logistic fusion of gate, retrieval, and verifier features with a threshold chosen on SQuAD calibration data, and no probability is shown unless calibrated.

## Slide 10: Dataset strategy: article-level splits, locked course set

Three data roles. SQuAD 2.0 trains the gate and calibrates thresholds: it is split by article, so no article appears in two partitions. The course corpus is the open textbook Dive into Deep Learning, 1,242 passages from 10 chapters, provisional pending faculty approval. The course evaluation set has 57 questions; the out-of-syllabus ones come from chapters that were deliberately not indexed. The items were drafted by an AI assistant from the corpus text and then accepted, edited or rejected by both members; this is disclosed. Be upfront that the second blind labelling failed and was not repeated, so we report no inter-annotator agreement.

## Slide 11: Comparison: two baselines, one gate, four ablations

Handbook task 2 asks for two justified baselines. B1 is the small-LLM route: the same generator is allowed to say INSUFFICIENT_EVIDENCE by instruction only. B2 is the sentence-transformer route: the same retrieval and reranking, with a threshold on the cross-encoder score tuned on SQuAD calibration data. G adds the trained gate, the verifier features and the calibrated fusion. All systems share the same retrieved passages and generator, so the comparison isolates the abstention mechanism. Ablations remove one component at a time and are descriptive.

## Slide 12: Implementation status: complete, partial, outstanding

This is the honest status slide. Complete: the full pipeline runs end to end on a free T4; the gate trained to a gate-development AUROC of 0.954; hybrid retrieval with reranking reaches Recall@5 of 0.988 on SQuAD calibration; the test items were frozen and the pre-registration committed before any test output; 75 outputs were judged. Partial: the demo app is built but the recorded demo is pending; the instructor has not confirmed corpus approval or the coverage tolerance. Outstanding: the SQuAD test run, stress conditions S2 to S4, ablation A4, double judging, and a valid inter-annotator agreement.

## Slide 13: References (1 of 2)

Verification codes: V = identifier and venue checked against a primary page or model card; PV = paper and venue consistent across sources, specific numbers not re-read; G = standard reference cited from general knowledge, identifier not re-checked online in this session. No number from a PV or G source is quoted in the deck.

## Slide 14: References (2 of 2)

Verification codes: V = identifier and venue checked against a primary page or model card; PV = paper and venue consistent across sources, specific numbers not re-read; G = standard reference cited from general knowledge, identifier not re-checked online in this session. No number from a PV or G source is quoted in the deck.
