import re

# Inside tests/testranker.py
from pathlib import Path
import sys

# Add the project root (documentretrieval) to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Now Python can locate the app module cleanly
from app.retrieval.snippets import make_snippet
class TestMakeSnippet:

    def test_basic_match_and_highlight(self):
        #basic match is correctly wrapped in <mark> tags
        text = "The quick brown fox jumps over the lazy dog"
        query = ["fox"]
        result = make_snippet(text, query)

        assert "<mark>fox</mark>" in result
        assert "The quick brown" in result

    def test_case_and_punctuation_insensitive_match(self):
        #query matches words with uppercase letters or attached punctuation
        text = "Hello! The Quick, Brown Fox jumps over."
        query = ["fox", "quick"]

        result = make_snippet(text, query)

        # Should match despite capital 'Q' and attached comma
        assert "<mark>Quick,</mark>" in result or "<mark>Quick</mark>" in result
        assert "<mark>Fox</mark>" in result

    def test_no_match_fallback(self):
        #no matches
        text = "This project is about database management and optimization techniques."
        query = ["zebra", "quantum"]

        result = make_snippet(text, query)

        assert "<mark>" not in result
        assert len(result) > 0

    def test_empty_inputs(self):
        #edge cases w no input or no query tokens
        assert make_snippet("", ["test"]) == ""
        assert make_snippet("Hello world", []) == "Hello world"

    def test_truncation(self):
        #test truncating window
        prefix_words = ["word"] * 50
        suffix_words = ["word"] * 49
        text = " ".join(prefix_words + ["target"] + suffix_words)

        result = make_snippet(text, ["target"])

        assert result.startswith("...")
        assert result.endswith("...")
        assert "<mark>target</mark>" in result

    def test_multiple_query_matches_in_window(self):
        #multiple query matches
        text = "Several test cases were made to evaluate program accuracy."
        query = ["several", "test", "accuracy"]

        result = make_snippet(text, query)

        assert "<mark>Several</mark>" in result
        assert "<mark>test</mark>" in result
        assert "<mark>accuracy.</mark>" in result