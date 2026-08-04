"""
Real IR evaluation against the Cranfield test collection (1,400 documents,
225 queries, with genuine human relevance judgments) -- replaces the
synthetic corpus check with actual measured
precision, recall, and MRR.

Install first: pip install ir_datasets
Run with: python cranfield_eval.py

First run will download the collection (small, a few MB) and cache it
locally, so subsequent runs are fast.
"""

import ir_datasets

from app.retrieval.tokenizer import tokenize
from app.retrieval.indexer import InvertedIndex
from app.retrieval.ranker import rank

TOP_K = 10

print("Loading Cranfield dataset...")
dataset = ir_datasets.load("cranfield")

print("Indexing documents...")
index = InvertedIndex()
for doc in dataset.docs_iter():
    full_text = f"{doc.title} {doc.text}"
    index.add_document(doc.doc_id, tokenize(full_text))

print(f"Indexed {index.doc_count} documents\n")

# Build query_id -> set of doc_ids judged relevant (relevance > 0;
# Cranfield uses -1 for "not relevant", 1-4 for increasing relevance)
relevant_docs = {}
for qrel in dataset.qrels_iter():
    if qrel.relevance > 0:
        relevant_docs.setdefault(qrel.query_id, set()).add(qrel.doc_id)

queries = [q for q in dataset.queries_iter() if q.query_id in relevant_docs]
print(f"Evaluating on {len(queries)} queries with relevance judgments\n")

for scorer in ("bm25", "tfidf"):
    precisions, recalls, reciprocal_ranks = [], [], []

    for query in queries:
        judged_relevant = relevant_docs[query.query_id]
        query_tokens = tokenize(query.text)
        results = rank(index, query_tokens, method=scorer)
        top_k_ids = [doc_id for doc_id, _ in results[:TOP_K]]

        hits = len(set(top_k_ids) & judged_relevant)
        precisions.append(hits / TOP_K)
        recalls.append(hits / len(judged_relevant))

        rr = 0.0
        for i, doc_id in enumerate(top_k_ids, start=1):
            if doc_id in judged_relevant:
                rr = 1.0 / i
                break
        reciprocal_ranks.append(rr)

    n = len(queries)
    print(f"[{scorer.upper()}] over {n} queries")
    print(f"  Precision@{TOP_K}: {sum(precisions)/n:.4f}")
    print(f"  Recall@{TOP_K}:    {sum(recalls)/n:.4f}")
    print(f"  MRR:              {sum(reciprocal_ranks)/n:.4f}\n")
