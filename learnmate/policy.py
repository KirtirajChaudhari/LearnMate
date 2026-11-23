"""Typed decision policy (spec C10, ADR-012). Pure function of features + frozen thresholds -> testable.

States
  system_error  : any component failed                     -> abstain (fail-closed)
  contradictory : top passages contradict (pp_contra>=kc)  -> show both passages, no adjudication
  insufficient  : P(safe) < tau or LLM said INSUFFICIENT    -> abstain, show nearest sections as "related"
  partial       : some sentences unsupported (< s_min)      -> show only supported sentences + coverage note
  sufficient    : all sentences supported                   -> show answer with verified citations
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

STATES = ("sufficient", "partial", "insufficient", "contradictory", "system_error")
ANSWER_STATES = ("sufficient", "partial")

NOT_COVERED_NOTE = "Part of this question is not covered by the approved course material."
ABSTAIN_MSG = ("I can't answer this from the approved course material. "
               "The sections below are related, but they do not contain the answer.")
CONTRA_MSG = ("The course passages I found disagree with each other, so I won't pick one. "
              "Both passages are shown below; this question has been flagged for the instructor.")
ERROR_MSG = "Something went wrong while checking the evidence, so I'm not answering rather than risk an unverified answer."


@dataclass
class Decision:
    state: str
    answered: bool
    p_safe: float | None
    tau: float | None
    reason: str
    message: str
    displayed_sentences: list[dict] = field(default_factory=list)
    related_ids: list[str] = field(default_factory=list)
    contradiction_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def decide(
    *,
    llm_insufficient: bool,
    sentences: list[dict],
    p_safe: float | None,
    tau: float | None,
    pp_contra: float = 0.0,
    kappa_c: float | None = None,
    s_min: float = 0.5,
    ranked_ids: list[str] | None = None,
    error: str | None = None,
    score_only: bool = False,
) -> Decision:
    """``sentences``: dicts with text, citations, support. ``score_only`` = baseline mode (no sentence pruning).

    For B1 (prompt-only) pass p_safe=None, tau=None; for B2 pass p_safe=ce_top1, tau=tau_CE, score_only=True.
    """
    ranked_ids = ranked_ids or []
    if error is not None:
        return Decision("system_error", False, p_safe, tau, f"error: {error}", ERROR_MSG, [], ranked_ids[:3])
    if kappa_c is not None and pp_contra >= kappa_c:
        return Decision("contradictory", False, p_safe, tau, f"pp_contra={pp_contra:.2f}>={kappa_c:.2f}",
                        CONTRA_MSG, [], [], ranked_ids[:2])
    if llm_insufficient or not sentences:
        return Decision("insufficient", False, p_safe, tau, "generator returned INSUFFICIENT_EVIDENCE",
                        ABSTAIN_MSG, [], ranked_ids[:3])
    if p_safe is not None and tau is not None and p_safe < tau:
        return Decision("insufficient", False, p_safe, tau, f"p_safe={p_safe:.3f}<tau={tau:.3f}",
                        ABSTAIN_MSG, [], ranked_ids[:3])
    if score_only:
        return Decision("sufficient", True, p_safe, tau, "answered (baseline policy)", "", list(sentences), [])
    supported = [s for s in sentences if s.get("citations") and (s.get("support") or 0.0) >= s_min]
    if not supported:
        return Decision("insufficient", False, p_safe, tau, "no sentence is supported by its cited passage",
                        ABSTAIN_MSG, [], ranked_ids[:3])
    if len(supported) < len(sentences):
        return Decision("partial", True, p_safe, tau,
                        f"{len(sentences) - len(supported)} of {len(sentences)} sentences unsupported",
                        NOT_COVERED_NOTE, supported, [])
    return Decision("sufficient", True, p_safe, tau, "all sentences supported by cited passages", "", supported, [])
