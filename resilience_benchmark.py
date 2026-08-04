"""
Adversarial / resilience test cases -- these are deliberately designed to
be HARD, not just topically separable. Each section tests a specific
failure mode a naive "count the matching words" ranker would fall into.

Run with: python resilience_benchmark.py
"""

from app.retrieval.tokenizer import tokenize
from app.retrieval.indexer import InvertedIndex
from app.retrieval.ranker import rank, bm25_score, tfidf_score

index = InvertedIndex()

DOCS = {
    # --- Test 1: keyword-stuffing resistance ---
    # A real document mentions "python" once but has substantive, relevant
    # supporting content. A spam document mentions "python" 11 times with
    # no real content at all. A ranker that just counts term frequency
    # would let the spam doc win; BM25's saturation should limit that.
    "python_real": (
        "Python is a versatile programming language widely used for web "
        "development, data science, and automation scripting."
    ),
    "python_spam": (
        "python python python python python python python python python "
        "python python best python tutorial download now click here"
    ),

    # --- Test 2: length adversarial / "mentioned vs. about" ---
    # A short document is genuinely ABOUT machine learning. A long,
    # rambling document mentions "machine learning" exactly once, buried
    # in ~150 words of unrelated content. The short, focused doc should
    # win despite having far fewer total words.
    "ml_focused": (
        "Machine learning models learn patterns from data using neural "
        "networks and gradient descent optimization techniques."
    ),
    "ml_buried_long": (
        "Today I woke up early and made coffee before reading the morning "
        "news about the stock market. Later I took a long walk in the park "
        "and watched several dogs playing fetch near the pond with their "
        "owners. In the afternoon I sat through a lengthy meeting about "
        "quarterly budgets and a presentation that briefly touched on "
        "machine learning before I headed out to grab lunch with a "
        "coworker at a sandwich shop nearby. After lunch we talked about "
        "weekend plans involving a hiking trip to the mountains and maybe "
        "camping overnight if the weather held up. The evening was spent "
        "watching a movie and reading before an early night, since I had "
        "a flight the next morning to visit family out of state."
    ),

    # --- Test 3: lexical ambiguity ---
    # "python" the programming language vs. "python" the snake. A pure
    # bag-of-words ranker CANNOT disambiguate a single ambiguous word --
    # that's a real, known limitation worth understanding, not hiding.
    "python_snake": (
        "The ball python is a popular pet snake known for its docile "
        "temperament, manageable size, and beautiful patterned scales."
    ),
}

for doc_id, text in DOCS.items():
    index.add_document(doc_id, tokenize(text))


def show_scores(query, method="bm25"):
    query_tokens = tokenize(query)
    results = rank(index, query_tokens, method=method)
    print(f"  Query: '{query}' ({method})")
    for doc_id, score in results:
        print(f"    {doc_id}: {score:.4f}")
    return results


print("=" * 70)
print("TEST 1: Keyword-stuffing resistance")
print("  (does raw repetition of 'python' beat a real, relevant document?)")
print("=" * 70)
for method in ("bm25", "tfidf"):
    results = show_scores("python programming language", method)
    winner = results[0][0] if results else None
    verdict = "PASS -- real doc won" if winner == "python_real" else "CONCERN -- spam doc won"
    print(f"  -> {verdict}\n")

print("  Single ambiguous term 'python' alone (no disambiguating context):")
for method in ("bm25", "tfidf"):
    results = show_scores("python", method)
    winner = results[0][0] if results else None
    print(f"  -> top result: {winner} ({method}) -- worth knowing which way this goes\n")

print("=" * 70)
print("TEST 2: Length adversarial (focused vs. buried-in-noise)")
print("=" * 70)
for method in ("bm25", "tfidf"):
    results = show_scores("machine learning", method)
    winner = results[0][0] if results else None
    verdict = "PASS -- focused doc won" if winner == "ml_focused" else "CONCERN -- long doc won despite one passing mention"
    print(f"  -> {verdict}\n")

print("=" * 70)
print("TEST 3: Lexical ambiguity (python language vs. python snake)")
print("=" * 70)
print("  Disambiguating query (extra context should resolve the ambiguity):")
for method in ("bm25", "tfidf"):
    results = show_scores("python programming code", method)
    winner = results[0][0] if results else None
    is_lang_doc = winner in ("python_real", "python_spam")
    verdict = "PASS -- correctly favored a programming doc" if is_lang_doc else "CONCERN -- snake doc won a programming query"
    print(f"  -> {verdict}\n")

print("  Ambiguous single-word query (genuinely unresolvable without more context):")
for method in ("bm25", "tfidf"):
    results = show_scores("python", method)
    print(f"  -> This is a KNOWN LIMITATION, not a bug: bag-of-words ranking")
    print(f"     can't disambiguate word sense from one word alone. A real")
    print(f"     search engine would need query context, embeddings, or")
    print(f"     click data to resolve this -- worth saying so directly if asked.\n")
