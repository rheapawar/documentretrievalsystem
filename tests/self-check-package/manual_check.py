from app.retrieval.tokenizer import tokenize
from app.retrieval.indexer import InvertedIndex
from app.retrieval.ranker import rank

DOCS = {
    "doc_python": "Python is a high-level programming language known for readability.",
    "doc_database": "Database indexing improves the speed of data retrieval operations.",
    "doc_ranking": "Ranking algorithms determine the order of search results. BM25 improves on TF-IDF.",
}

print("=" * 60)
print("STEP 1: Tokenization")
print("=" * 60)
for doc_id, text in DOCS.items():
    tokens = tokenize(text)
    print(f"{doc_id}: {tokens}")

print()
print("=" * 60)
print("STEP 2: Building inverted index")
print("=" * 60)
index = InvertedIndex()
for doc_id, text in DOCS.items():
    index.add_document(doc_id, tokenize(text))

print(f"Documents indexed: {index.doc_count}")
print(f"Average doc length: {index.avg_doc_length:.1f} tokens")
print(f"'ranking' appears in: {index.documents_containing('ranking')}")
print(f"'python' appears in: {index.documents_containing('python')}")

print()
print("=" * 60)
print("STEP 3: Search sanity checks")
print("=" * 60)

test_queries = [
    ("ranking algorithm", "bm25"),
    ("ranking algorithm", "tfidf"),
    ("database index", "bm25"),
    ("python programming", "bm25"),
    ("zzz nonexistent word", "bm25"),
]

for query, method in test_queries:
    query_tokens = tokenize(query)
    results = rank(index, query_tokens, method=method)
    print(f"\nQuery: '{query}' (method={method}, tokens={query_tokens})")
    if not results:
        print("  -> no results")
    for doc_id, score in results:
        print(f"  -> {doc_id}: {score:.4f}")

print()
print("=" * 60)
print("Does 'ranking algorithm' put doc_ranking on top?")
print("Does 'database index' put doc_database on top?")
print("Does an unrelated query correctly return nothing?")
print("=" * 60)
