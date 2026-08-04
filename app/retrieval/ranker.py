import math
from collections import defaultdict
from typing import Callable

from app.retrieval.indexer import InvertedIndex

Scorer = Callable[[InvertedIndex, str, str], float]

def tfidf_score(index: InvertedIndex, token: str, doc_id: str) -> float:
    tf = index.term_frequency(token, doc_id)
    idf = log((index.doc_count + 1) / (index.document_frequency(token) + 1)) + 1
    return tf * idf
    


def bm25_score(index: InvertedIndex,
    token: str,
    doc_id: str,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    df = index.document_frequency(token)
    tf = index.term_frequency(token, doc_id)
    idf = log((index.doc_count - df + 0.5) / df + 0.5 + 1)
    score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b*(index.doc_lengths[doc_id] / index.avg_doc_length)))
    

SCORERS: dict[str, Scorer] = {
    "tfidf": tfidf_score,
    "bm25": bm25_score,
}

def rank(
    index: InvertedIndex,
    query_tokens: list[str],
    method: str = "bm25",
) -> list[tuple[str, float]]:
    scorer = SCORERS[method]
    scores : dict[str, float] = defaultdict(float)
    for token in query_tokens:
        for doc in index.documents_containing(token):
            scores[doc]+= scorer(index, token, doc)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


    