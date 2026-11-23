"""LearnMate: evidence-grounded course AI tutor (G06).

Pipeline: provenance-preserving ingestion -> hybrid retrieval -> cross-encoder rerank ->
trained sufficiency gate -> grounded generation with [C#] citations -> citation validation ->
claim-level verification (MiniCheck + NLI) -> calibrated fusion -> typed decision policy.
"""
__version__ = "0.1.0"
