"""
Self-check for ranker.py. Run with: pytest tests/test_ranker.py -v

The important thing these tests check isn't just "does it return a
number" -- it's "does the RANKING ORDER make sense." A bug that returns
a plausible-looking wrong score is much easier to miss than one that
crashes, so every test here is built around a case where you can reason
out the correct answer by hand first.
"""

from app.retrieval.indexer import InvertedIndex
from app.retrieval.ranker import rank, tfidf_score, bm25_score


def build_basic_index():
    idx = InvertedIndex()
    idx.add_document("doc_python", ["python", "programming", "language", "python"])
    idx.add_document("doc_database", ["database", "indexing", "postgres"])
    idx.add_document("doc_mixed", ["python", "database", "ranking"])
    return idx


def test_tfidf_ranks_more_relevant_doc_first():
    idx = build_basic_index()
    results = rank(idx, ["python"], method="tfidf")
    # doc_python mentions "python" twice, doc_mixed once -- doc_python should win
    assert results[0][0] == "doc_python"


def test_bm25_ranks_more_relevant_doc_first():
    idx = build_basic_index()
    results = rank(idx, ["python"], method="bm25")
    assert results[0][0] == "doc_python"


def test_query_with_no_matches_returns_empty():
    idx = build_basic_index()
    assert rank(idx, ["zzzznonexistent"], method="bm25") == []


def test_multi_token_query_favors_doc_matching_more_terms():
    idx = build_basic_index()
    # doc_mixed contains BOTH "python" and "database"; doc_python and
    # doc_database each contain only one of them. doc_mixed should win
    # a combined query even though neither individual term is its
    # strongest match.
    results = rank(idx, ["python", "database"], method="bm25")
    top_doc_id = results[0][0]
    assert top_doc_id == "doc_mixed"


def test_document_with_zero_term_frequency_scores_zero():
    idx = build_basic_index()
    # "postgres" only appears in doc_database -- scoring it against a doc
    # that doesn't contain it at all should be exactly 0, not some tiny
    # nonzero float from a division slipping through.
    score = tfidf_score(idx, "postgres", "doc_python")
    assert score == 0.0
    score = bm25_score(idx, "postgres", "doc_python")
    assert score == 0.0


def test_bm25_length_normalization():
    """
    This is the specific thing that makes BM25 different from TF-IDF:
    a short document mentioning a term once should be able to outrank
    a much longer document that mentions it the same raw number of
    times, because BM25 penalizes documents for being long "just because."
    """
    idx = InvertedIndex()
    filler = [f"word{i}" for i in range(200)]  # 200 unique filler words
    idx.add_document("doc_short", ["target"] + filler[:5])       # length 6
    idx.add_document("doc_long", ["target"] + filler)             # length 201

    results = rank(idx, ["target"], method="bm25")
    top_doc_id = results[0][0]
    # both docs mention "target" exactly once -- the much shorter doc
    # should score higher under BM25's length normalization
    assert top_doc_id == "doc_short"


def test_bm25_term_frequency_saturation():
    """
    Raw term frequency alone would say "10 mentions is 10x better than 1
    mention." BM25 saturates that -- so the SCORE RATIO between a doc
    with 10 mentions and 1 mention should be well under 10x, even though
    the term count ratio literally is 10x.
    """
    idx = InvertedIndex()
    idx.add_document("doc_one_mention", ["target", "filler", "filler"])
    idx.add_document("doc_ten_mentions", ["target"] * 10 + ["filler", "filler"])

    score_one = bm25_score(idx, "target", "doc_one_mention")
    score_ten = bm25_score(idx, "target", "doc_ten_mentions")

    assert score_ten > score_one          # more mentions should still score higher...
    assert score_ten < score_one * 10     # ...but nowhere near proportionally higher
