# Development Readiness Assessment

**Verdict: CONDITIONALLY READY.** Phase II can start right after approval. No input is strictly blocking for M0–M3. Three conditions must be met by the dates below or the plan falls back (see `implementation_roadmap.md` § Fallbacks).

## 1. Conditions

| # | Condition | Why needed | Needed by | Owner | If not met |
|---|---|---|---|---|---|
| C1 | **GPU access**: Colab free T4 or Kaggle GPU | This container has no GPU. Gate training and full-scale generation need one | M0 (Day 1–2) | Students | CPU fallback mode: GGUF generator, small gate, no squad-test |
| C2 | **Faculty decision on the course corpus**: approve d2l chapter subset, or supply licensed materials with permission | Handbook §5 "approved course materials"; §10 sign-off | End of Week 1 (before item authoring passes ~50%) | Instructor | Continue with d2l labelled *provisional*, and record the gap in Deliverable C |
| C3 | **Instructor confirmation of m = 10 pp and λ = 2**, plus submission dates | Pre-registration values (ADR-014) | End of Week 2 (pre-registration) | Instructor | Team freezes the defaults and documents them as team-set |

## 2. Ready now

- **Licenses verified.** All selected models are MIT or Apache-2.0 and ungated. Exceptions: B0 is CC BY 4.0 and needs attribution; SQuAD and d2l are CC BY-SA 4.0.
- **Data reachable.** SQuAD 2.0 and d2l are reachable from this environment, and SQuAD counts were reproduced programmatically.
- **Specification complete.** It covers architecture, ADRs, dataset/annotation plan, protocol, roadmap and traceability.
- **No paid APIs or gated weights.**

## 3. Known risks carried into Phase II

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| transformers 5.x incompatibility (MiniCheck / LettuceDetect) | Medium | Medium | ADR-010 pin `<5`; M0 smoke test |
| Gate does not transfer SQuAD→course (high ECE/AURC on course-cal) | Medium | High for H1 | Platt recalibration; A5 control; report as finding |
| Annotation time overrun | Medium | High | Start Day 2; 150-item floor |
| Generation throughput on T4 | Low–Medium | Medium | 4B fp16; staged caching; reduce squad sample |
| Verifier weak on math/notation | High | Medium | `has_math` slice; error tagging |
| Null result for H1 | Plausible | None for validity | Pre-registered; report honestly with ablation diagnosis |

## 4. Explicitly out of scope for LCA-3

LLM fine-tuning, LoRA/DPO, multi-pass regeneration, web search fallback, multi-user deployment, multimodal slide parsing, and formal risk guarantees.
