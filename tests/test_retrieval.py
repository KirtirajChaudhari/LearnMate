from eval.retrieval_metrics import mrr, ndcg_at_k, recall_at_k
from learnmate.index import bm25_tokenize
from learnmate.retrieve import rrf_fuse


def test_rrf_arithmetic():
    fused = dict(rrf_fuse([["a", "b", "c"], ["b", "a", "d"]], k=60))
    assert abs(fused["a"] - (1 / 61 + 1 / 62)) < 1e-12
    assert abs(fused["d"] - 1 / 63) < 1e-12
    order = [c for c, _ in rrf_fuse([["a", "b"], ["b", "a"]], k=60)]
    assert order == ["a", "b"]  # tie broken by first appearance


def test_bm25_tokenizer_keeps_latex_and_numbers():
    toks = bm25_tokenize("The \\mathbf{w} vector has 3.5 entries and the ReLU")
    assert "\\mathbf" in toks and "3.5" in toks and "relu" in toks and "the" not in toks


def test_retrieval_metrics():
    assert recall_at_k(["x", "g"], {"g"}, 1) == 0.0 and recall_at_k(["x", "g"], {"g"}, 2) == 1.0
    assert mrr(["x", "g"], {"g"}) == 0.5
    assert abs(ndcg_at_k(["g"], {"g"}) - 1.0) < 1e-12
