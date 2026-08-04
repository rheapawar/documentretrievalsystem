"""
Self-check for indexer.py. Run with: pytest tests/test_indexer.py -v

These specifically test the INCREMENTAL behavior -- add, replace, remove --
since that's the part that's easy to get subtly wrong (see the trace
examples in your notes about postings not clearing on re-add).
"""

from app.retrieval.indexer import InvertedIndex


def test_add_single_document():
    idx = InvertedIndex()
    idx.add_document("doc1", ["python", "python", "code"])

    assert idx.doc_count == 1
    assert idx.doc_lengths["doc1"] == 3
    assert idx.term_frequency("python", "doc1") == 2
    assert idx.term_frequency("code", "doc1") == 1
    assert idx.term_frequency("nonexistent", "doc1") == 0


def test_document_frequency_across_multiple_docs():
    idx = InvertedIndex()
    idx.add_document("doc1", ["python", "search"])
    idx.add_document("doc2", ["python", "database"])
    idx.add_document("doc3", ["rust", "database"])

    assert idx.doc_count == 3
    assert idx.document_frequency("python") == 2      # in doc1, doc2
    assert idx.document_frequency("database") == 2     # in doc2, doc3
    assert idx.document_frequency("rust") == 1          # in doc3 only
    assert set(idx.documents_containing("database")) == {"doc2", "doc3"}


def test_avg_doc_length():
    idx = InvertedIndex()
    idx.add_document("doc1", ["a", "b", "c", "d"])   # length 4
    idx.add_document("doc2", ["a", "b"])              # length 2
    assert idx.avg_doc_length == 3.0                   # (4 + 2) / 2


def test_avg_doc_length_empty_index_does_not_crash():
    idx = InvertedIndex()
    assert idx.avg_doc_length == 0.0   # should NOT raise ZeroDivisionError


def test_re_adding_same_doc_id_replaces_not_accumulates():
    """
    This is the bug from your earlier debugging session: re-adding a
    doc_id should wipe its OLD contribution before adding the new one.
    """
    idx = InvertedIndex()
    idx.add_document("doc1", ["python", "python"])
    idx.add_document("doc1", ["rust"])  # simulate re-upload / edit

    assert idx.doc_count == 1  # still just 1 doc, not 2
    assert idx.term_frequency("python", "doc1") == 0   # old tokens gone
    assert idx.term_frequency("rust", "doc1") == 1      # new tokens present
    assert idx.doc_lengths["doc1"] == 1                  # length updated too


def test_remove_document_clears_postings_and_length():
    idx = InvertedIndex()
    idx.add_document("doc1", ["python", "search"])
    idx.add_document("doc2", ["python"])

    idx.remove_document("doc1")

    assert idx.doc_count == 1
    assert "doc1" not in idx.doc_lengths
    assert idx.term_frequency("python", "doc1") == 0
    # doc2's data should be completely untouched
    assert idx.term_frequency("python", "doc2") == 1
    assert idx.document_frequency("python") == 1


def test_remove_nonexistent_document_does_not_crash():
    idx = InvertedIndex()
    idx.add_document("doc1", ["python"])
    idx.remove_document("doc_that_was_never_added")  # should be a no-op
    assert idx.doc_count == 1
