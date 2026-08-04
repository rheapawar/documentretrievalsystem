"""
k1 sweep -- determine optimal k1 value to minimize keyword-stuffing gap between a spam doc and a
real doc, on a single-term query
where idf can't help distinguish them.

Run with: python k1_sweep.py
"""

from app.retrieval.tokenizer import tokenize
from app.retrieval.indexer import InvertedIndex
from app.retrieval.ranker import bm25_score

DOCS = {
    "python_real": (
        "Python is a versatile programming language widely used for web "
        "development, data science, and automation scripting."
    ),
    "python_spam": (
        "python python python python python python python python python "
        "python python best python tutorial download now click here"
    ),
    "python_snake": (
        "The ball python is a popular pet snake known for its docile "
        "temperament, manageable size, and beautiful patterned scales."
    ),
}

index = InvertedIndex()
for doc_id, text in DOCS.items():
    index.add_document(doc_id, tokenize(text))

query_token = "python"  # single ambiguous term, idf is identical across all 3 docs

print("=" * 70)
print(f"Query: '{query_token}' -- idf is IDENTICAL across all 3 docs here,")
print("so any score difference below comes purely from tf saturation + length.")
print("=" * 70)
print(f"{'k1':>6} | {'python_real':>12} | {'python_spam':>12} | {'python_snake':>13} | winner")
print("-" * 70)

for k1 in [0.1, 0.3, 0.5, 0.8, 1.2, 1.5, 2.0, 3.0, 5.0]:
    scores = {
        doc_id: bm25_score(index, query_token, doc_id, k1=k1, b=0.75)
        for doc_id in DOCS
    }
    winner = max(scores, key=scores.get)
    print(
        f"{k1:>6.1f} | {scores['python_real']:>12.4f} | "
        f"{scores['python_spam']:>12.4f} | {scores['python_snake']:>13.4f} | {winner}"
    )

print()
print("The gap between python_real and python_spam as k1 drops.")
print("It should narrow, but python_spam likely still wins at every k1 > 0 --")
print("this ceiling is described in the README: pure term-frequency")
print("ranking can reduce, but not eliminate a keyword-stuffing advantage")
print("on a single ambiguous term with no other signal to lean on.")
