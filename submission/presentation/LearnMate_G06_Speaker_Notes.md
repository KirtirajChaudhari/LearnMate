# LearnMate G06: Speaker notes
Two presenters: agree the split between you yourselves; nothing here assigns sections.

## Slide 1: Course
documents

Open by stating the status: the system is built and evaluated once on a locked test set; the headline result is a preliminary null on our registered hypothesis, and the deck is honest about that. Placeholders in brackets (institution, names, guide, date) must be filled before presenting. Two presenters: agree the split between you in advance; nothing in this deck assigns sections to either member.

## Slide 2: A plausible answer is not the same as a supported answer

Explain the three cases. Case 1 is the goal: the course passage entails the answer and it is cited. Case 2 is the subtle failure: the statement may be true in the world, but the course text shown to the student does not say it, so for a course tutor it is unsupported. Case 3 is the dangerous one: an out-of-syllabus question that should be refused with pointers to related sections. Examples are drawn from our own evaluation set and smoke test, shown for illustration only. Transition: the handbook makes exactly this the assigned challenge.

## Slide 3: The assigned research challenge: G06 LearnMate

This slide is traceable to page 5 of the handbook. Read the problem statement, then point out the split: the left column is what the prototype must do; the right column is what the research must show. The handbook also says to check whether the approach is already published, which is why our framing is a controlled evaluation and not a novelty claim. Transition: what has the literature established?

## Slide 4: Research landscape: three linked streams

Walk left to right. Retrieval brings candidate evidence; generation turns it into cited prose; verification and abstention decide whether to show it. The tutoring context box reminds the audience that small local models with RAG are already used in computing education [10], but without verification or calibrated abstention. Cross-links matter: retrieval relevance does not guarantee sufficiency, and a citation being present does not guarantee support. Transition to the literature table.

## Slide 5: Literature review: key studies and what they leave open

Pick two rows to talk through. Joren et al. propose using context sufficiency to guide selective generation, with large autoraters; we ask whether a small trained local gate transfers to course text. Setiawan shows prompt-only abstention is fragile under misleading context, which is exactly our B1 baseline. Wallat separates citation correctness from faithfulness, motivating our withheld-gold stress test. The full 10-paper matrix is in Deliverable B. Be explicit that we did not re-read numbers from the primary texts for every source; no quantitative claim from those papers is used in this deck.

## Slide 6: What the literature reveals: four unguaranteed links

The chain on top is the core argument. Each arrow is a place where a conventional RAG demo silently assumes success. Relevant retrieval does not guarantee sufficient evidence [1]; having evidence does not guarantee a faithful answer; a present citation does not guarantee support [9]; and a model asked to abstain may not [6][7]. The three cards underneath state what the literature implies for method design: verify at claim level, calibrate on held-out data, and report the coverage cost. Avoid saying any paper proves these hold for course tutoring.

## Slide 7: Research gap: a controlled evaluation, not a new algorithm

State the gap precisely and modestly. Each ingredient exists: sufficiency-based selective generation, claim-level verification, calibrated detectors. We found no study combining a small trained answerability gate with claim-level verification in a local course-tutor setting and testing it against a tuned reranker-score threshold under withheld-evidence stress on an independently labelled course set. That is a replication-plus-adaptation. A negative result is a valid outcome, and as we show later, ours is negative on the registered hypothesis.

## Slide 8: Objectives and a falsifiable hypothesis, registered before testing

Read the research question, then the hypothesis. H1 is deliberately demanding: it requires the whole confidence interval of the AURC difference to be below zero, and a limit on lost coverage. The tolerance m of 10 percentage points was set by the team and is flagged as pending instructor confirmation. Emphasise the pre-registration: the document was frozen with hashes before any test output was produced, and the analysis code and thresholds were fixed. Transition to the architecture.

## Slide 9: System architecture as implemented

This is the system as built, not a plan. The top row is offline preparation: the open textbook is parsed with provenance, chunked at section boundaries into 1,242 passages, and indexed with BM25 and BGE embeddings. The bottom row is online: hybrid retrieval with reciprocal-rank fusion and a cross-encoder rerank, then a trained sufficiency gate, grounded generation by Qwen3-4B with bracketed citations, claim-level verification with MiniCheck and an NLI model, and a fusion step that outputs a typed decision. Fail-closed: any component error leads to abstention. Colours encode function; the legend sits below.

## Slide 10: Technology selection: pinned models per responsibility

These are final choices as implemented, with pinned revisions recorded in the repository. Note what was evaluated but not adopted in the research reports: LettuceDetect is used only as an optional secondary evaluator and not as a decision component; MiniCheck is a decision component and is never used to evaluate itself. The generator fits on a free T4 in fp16 (8.1 GB peak measured in the smoke test); NF4 halves that. Selection rationale is cost, licence, and fit to a free T4.

## Slide 11: Beyond RAG: when should the tutor answer?

The policy has four typed outcomes. Sufficient evidence: answer with citations. Partial: answer only what is supported and say what is not covered. Insufficient: abstain and show nearby sections labelled related, not supporting. Contradictory: disclose the conflict. Be honest that in the frozen test run the contradiction state was disabled, because we built no development items for it; so the result slides cover three effective outcomes. The decision is a logistic fusion of gate, retrieval, and verifier features with a threshold chosen on SQuAD calibration data, and no probability is shown unless calibrated.

## Slide 12: Dataset strategy: article-level splits, locked course set

Three data roles. SQuAD 2.0 trains the gate and calibrates thresholds: it is split by article, so no article appears in two partitions. The course corpus is the open textbook Dive into Deep Learning, 1,242 passages from 10 chapters, provisional pending faculty approval. The course evaluation set has 57 questions; the out-of-syllabus ones come from chapters that were deliberately not indexed. The items were drafted by an AI assistant from the corpus text and then accepted, edited or rejected by both members; this is disclosed. Be upfront that the second blind labelling failed and was not repeated, so we report no inter-annotator agreement.

## Slide 13: Experimental comparison: two baselines, one gate, four ablations

Handbook task 2 asks for two justified baselines. B1 is the small-LLM route: the same generator is allowed to say INSUFFICIENT_EVIDENCE by instruction only. B2 is the sentence-transformer route: the same retrieval and reranking, with a threshold on the cross-encoder score tuned on SQuAD calibration data. G adds the trained gate, the verifier features and the calibrated fusion. All systems share the same retrieved passages and generator, so the comparison isolates the abstention mechanism. Ablations remove one component at a time and are descriptive.

## Slide 14: Evaluation framework and stress conditions

Left: the four measurement dimensions. Right: the stress matrix with its true status. Only S1, withheld evidence, was run: the gold passage is removed from the index so that every answerable question becomes unsupported, and any answer is then an unsupported answer. S2 to S4 were not run in the time available. Error is defined strictly: a partially correct answer counts as an error in the primary analysis, with a lenient sensitivity analysis alongside. Judges labelled outputs blind to the system.

## Slide 15: Implementation status: complete, partial, outstanding

This is the honest status slide. Complete: the full pipeline runs end to end on a free T4; the gate trained to a gate-development AUROC of 0.954; hybrid retrieval with reranking reaches Recall@5 of 0.988 on SQuAD calibration; the test items were frozen and the pre-registration committed before any test output; 75 outputs were judged. Partial: the demo app is built but the recorded demo is pending; the instructor has not confirmed corpus approval or the coverage tolerance. Outstanding: the SQuAD test run, stress conditions S2 to S4, ablation A4, double judging, and a valid inter-annotator agreement.

## Slide 16: Preliminary result: H1 is not supported on 57 questions

Lead with the verdict. The registered test of H1 gives a difference in AURC of plus 0.079 with a confidence interval from minus 0.002 to plus 0.181: not entirely below zero, so H1 is not supported; the coverage condition is met. Explain why B2's AURC is low: it answers two questions in total, so its risk is almost vacuous. The more useful reading is the table: G and B1 both abstain on 20 of 21 out-of-syllabus questions; G answers fewer questions than B1 and makes fewer judged errors, but loses utility because it refuses 42 percent of answerable questions that were answered correctly. Caveat strongly: with 0 to 5 errors per system, small differences are one or two items. Lenient sensitivity analysis gives the same verdict.

## Slide 17: Stress test S1 and ablations

S1 withholds the gold passages, so every answer to an answerable question is unsupported by construction. Under S1 the prompt-only baseline still answers 56 percent of questions, 32 of 57, all unsupported; G answers about 10 percent, 6 questions; the threshold baseline answers none. That is the one condition where G clearly beats B1, but it is one stress condition on 57 items. The ablation table is descriptive: removing the verifier features (A1) gives a lower AURC and no errors at the price of more refusals; removing calibration (A3) raises coverage and doubles unsupported answers. Each difference is one or two items, so we do not rank components.

## Slide 18: Failure cases: seven judged errors, four questions

Seven outputs were judged partially correct, all by one judge, covering four questions. Case 1: the warmup answer is correct at the core but adds claims about initialisation that the passages do not contain. Case 2: for a partially covered question about multi-head attention, the answer states a head count the course does not give; the course's own demo model differs from the original paper. Case 3: for max pooling versus average pooling, both systems flagged that a number was missing but added an unsupported claim. Case 4: a padding computation for a 5 by 3 kernel gave the wrong width padding in the prompt-only output only. We have not yet classified retrieval misses or false abstentions per item; that is future work.

## Slide 19: Limitations and transparency

Be direct with the examiner. The judging has a structural weakness: each output was judged by the member who did not write the item, and the two judges differ in strictness, so judge and item author are confounded. The judges saw an AI-suggested verdict which they could accept or override; 66 of 72 suggestions were accepted, 6 overridden; that is disclosed and the judge's choice is final. The first blind second labelling was invalid and not repeated, so there is no agreement statistic. The pre-registration was regenerated once after an interrupted run; only a helper script changed between the two commits. Gate training time was not measured. The AI assistant helped write the code, the specification and drafted the course items; no experimental number was produced by it.

## Slide 20: Conclusion and next steps

Close with the synthesis: what we built, what the registered test showed, and what it cannot show. Do not present S1 as a general victory; it is one stress condition. Invite questions on judging, the null result, and the next steps. Presenters should be ready for: why is B2 so conservative (its threshold was fitted on SQuAD and transfers badly to course text), why is the verifier not shown to help (almost no errors to catch), and how reproducible the run is (pinned revisions, seeds, frozen hashes).

## Slide 21: References (1 of 2)

Verification codes: V = identifier and venue checked against a primary page or model card; PV = paper and venue consistent across sources, specific numbers not re-read; G = standard reference cited from general knowledge, identifier not re-checked online in this session. No number from a PV or G source is quoted in the deck.

## Slide 22: References (2 of 2)

Verification codes: V = identifier and venue checked against a primary page or model card; PV = paper and venue consistent across sources, specific numbers not re-read; G = standard reference cited from general knowledge, identifier not re-checked online in this session. No number from a PV or G source is quoted in the deck.
