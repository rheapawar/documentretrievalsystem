"""
Self-check for tokenizer.py. Run with: pytest tests/test_tokenizer.py -v
"""

from app.retrieval.tokenizer import tokenize


def test_lowercases():
    assert tokenize("HELLO World") == ["hello", "world"]


def test_splits_on_punctuation():
    tokens = tokenize("fox, jumps! over-the fence.")
    # punctuation should be treated as a separator, not glued to words
    assert "fox" in tokens
    assert "jumps" in tokens
    assert "fox," not in tokens


def test_drops_stop_words():
    tokens = tokenize("the quick fox and the lazy dog")
    assert "the" not in tokens
    assert "and" not in tokens
    # these should survive -- they're not in any reasonable stop-word list
    assert "quick" in tokens
    assert "fox" in tokens
    assert "lazy" in tokens
    assert "dog" in tokens


def test_numbers_are_kept_as_tokens():
    tokens = tokenize("Python 3.11 released")
    assert "3" in tokens
    assert "11" in tokens


def test_empty_and_none_input():
    assert tokenize("") == []
    assert tokenize(None) == []


def test_repeated_words_appear_multiple_times():
    # tokenize should NOT deduplicate -- the indexer needs repeat counts
    tokens = tokenize("python python python")
    assert tokens.count("python") == 3
