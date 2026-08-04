"""
Benchmark script -- produces real, defensible numbers for a resume bullet:
top-1 ranking accuracy and average query latency, measured against a
40-document corpus spanning 8 distinct topics.

Run with: python benchmark.py
"""

import time
import statistics

from app.retrieval.tokenizer import tokenize
from app.retrieval.indexer import InvertedIndex
from app.retrieval.ranker import rank

# ---------------------------------------------------------------------------
# Corpus: 8 topics x 5 documents each = 40 documents, deliberately using
# distinct vocabulary per topic so "which topic is this query about" has an
# unambiguous right answer.
# ---------------------------------------------------------------------------
CORPUS = {
    "python": [
        "Python is a high-level programming language known for readable syntax and dynamic typing.",
        "Python supports object-oriented, procedural, and functional programming paradigms in one language.",
        "The Python standard library includes modules for file handling, networking, and text processing.",
        "Python's package manager pip lets developers install third-party libraries from PyPI easily.",
        "Virtual environments in Python isolate project dependencies to avoid version conflicts between projects.",
    ],
    "databases": [
        "Relational databases organize data into tables with rows and columns connected by keys.",
        "SQL is the standard query language used to insert, update, and retrieve rows from a database.",
        "Database indexes speed up lookups by avoiding a full table scan for every query.",
        "Normalization reduces data redundancy by splitting information across related database tables.",
        "Transactions in a database guarantee that a group of operations either all succeed or all fail.",
    ],
    "machine_learning": [
        "Machine learning models learn patterns from labeled training data to make predictions.",
        "Neural networks consist of layers of interconnected nodes that adjust weights during training.",
        "Overfitting occurs when a model memorizes training data instead of generalizing to new examples.",
        "Gradient descent is an optimization algorithm used to minimize a model's loss function.",
        "Feature engineering transforms raw data into inputs that improve a model's predictive accuracy.",
    ],
    "cooking": [
        "Searing meat at high heat creates a flavorful crust through the Maillard browning reaction.",
        "Fresh herbs like basil and cilantro should be added near the end of cooking to preserve flavor.",
        "A roux made from butter and flour is used to thicken sauces and soups in French cooking.",
        "Marinating chicken in acidic ingredients like lemon juice helps tenderize the meat before grilling.",
        "Proper knife skills, like the rocking chop, make vegetable prep faster and more consistent.",
    ],
    "soccer": [
        "A soccer match consists of two 45 minute halves with a short break in between.",
        "Midfielders control possession and link defense to attack across the soccer pitch.",
        "The offside rule prevents attacking players from gaining an unfair positional advantage near goal.",
        "Set pieces like corner kicks and free kicks often decide close soccer matches.",
        "A team's formation, like 4-3-3, determines how players are positioned across the field.",
    ],
    "space": [
        "The James Webb telescope observes infrared light to study distant galaxies and star formation.",
        "Rockets use staged propulsion, discarding empty fuel stages to reduce weight during ascent.",
        "Mars rovers analyze soil samples to search for evidence of past microbial life.",
        "Satellites in geostationary orbit stay fixed above the same point on Earth's surface.",
        "Astronauts on the space station experience microgravity, which affects muscle and bone density.",
    ],
    "personal_finance": [
        "A diversified portfolio spreads investment risk across different asset classes and sectors.",
        "Compound interest allows savings to grow faster over time as interest earns additional interest.",
        "An emergency fund covering several months of expenses protects against unexpected income loss.",
        "Index funds track a market benchmark and typically charge lower fees than actively managed funds.",
        "Budgeting apps categorize spending automatically to help track monthly income and expenses.",
    ],
    "ancient_history": [
        "The Roman Senate advised elected magistrates but held no direct executive power itself.",
        "Roman aqueducts used gravity to transport fresh water across long distances into cities.",
        "Legionaries in the Roman army trained extensively in formation fighting and fortification building.",
        "The Colosseum hosted gladiator contests and public spectacles for tens of thousands of spectators.",
        "Roman roads connected the empire, enabling fast troop movement and trade across provinces.",
    ],
}

QUERIES = [
    ("python virtual environment dependencies", "python"),
    ("object oriented programming language", "python"),
    ("SQL query database table", "databases"),
    ("database index lookup speed", "databases"),
    ("neural network training loss", "machine_learning"),
    ("overfitting generalize training data", "machine_learning"),
    ("searing meat flavorful crust", "cooking"),
    ("marinate chicken tenderize", "cooking"),
    ("soccer midfielder possession", "soccer"),
    ("offside rule attacking players", "soccer"),
    ("rocket propulsion fuel stages", "space"),
    ("mars rover microbial life", "space"),
    ("diversified investment portfolio risk", "personal_finance"),
    ("compound interest savings grow", "personal_finance"),
    ("roman senate magistrates power", "ancient_history"),
    ("roman aqueducts fresh water", "ancient_history"),
]

# ---------------------------------------------------------------------------
# Build the index, timing it
# ---------------------------------------------------------------------------
index = InvertedIndex()
doc_topic = {}  # doc_id -> topic, so we can check "did the right TOPIC win"

start = time.perf_counter()
total_tokens = 0
for topic, docs in CORPUS.items():
    for i, text in enumerate(docs):
        doc_id = f"{topic}_{i}"
        tokens = tokenize(text)
        index.add_document(doc_id, tokens)
        doc_topic[doc_id] = topic
        total_tokens += len(tokens)
index_time_ms = (time.perf_counter() - start) * 1000

print("=" * 70)
print(f"Indexed {index.doc_count} documents ({total_tokens} tokens total) in {index_time_ms:.2f}ms")
print("=" * 70)

# ---------------------------------------------------------------------------
# Run every query against both ranking methods, measuring latency and
# whether the top-ranked result's TOPIC matches the expected topic.
# ---------------------------------------------------------------------------
for method in ("bm25", "tfidf"):
    latencies = []
    hits = 0

    for query_text, expected_topic in QUERIES:
        query_tokens = tokenize(query_text)

        start = time.perf_counter()
        results = rank(index, query_tokens, method=method)
        latencies.append((time.perf_counter() - start) * 1000)

        top_doc_id = results[0][0] if results else None
        top_topic = doc_topic.get(top_doc_id)
        if top_topic == expected_topic:
            hits += 1

    accuracy = (hits / len(QUERIES)) * 100
    avg_latency = statistics.mean(latencies)
    max_latency = max(latencies)

    print(f"\n[{method.upper()}]")
    print(f"  Top-1 topic accuracy: {hits}/{len(QUERIES)} ({accuracy:.1f}%)")
    print(f"  Avg query latency:    {avg_latency:.3f}ms")
    print(f"  Max query latency:    {max_latency:.3f}ms")

print()
print("=" * 70)

print("=" * 70)
