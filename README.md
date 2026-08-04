# Document Retrieval System

A document retrieval system that ingests uploaded PDF and text files,
indexes their content, and returns ranked search results with highlighted,
context-aware snippets. The inverted index, TF-IDF ranking, BM25 ranking,
and snippet extraction are all implemented from scratch — no external
search engine and no database full-text search feature is doing the
ranking work for you.

## Status

**Core retrieval engine complete, wiring in progress.**

- [x] Tokenizer (`app/retrieval/tokenizer.py`)
- [x] Inverted index with incremental add/replace/remove (`app/retrieval/indexer.py`)
- [x] TF-IDF ranking (`app/retrieval/ranker.py`)
- [x] BM25 ranking (`app/retrieval/ranker.py`)
- [x] Snippet extraction with query-term highlighting (`app/retrieval/snippets.py`)
- [x] PDF/text extraction (`app/ingestion/extractor.py`)
- [ ] SQLite storage (`app/storage/db.py`)
- [ ] `/upload` and `/search` endpoints wired up (`app/main.py`)
- [ ] Frontend (upload + search UI)
- [x] Unit tests for tokenizer, indexer, ranker (20 tests, all passing)
- [ ] Deployed

## Why this isn't a search-engine demo

Most small information-retrieval projects load a fixed corpus once at
startup and indexes are never retouched. This is a *retrieval
system*: documents are uploaded by a user at any time, and the index is
updated incrementally as each one is include — `InvertedIndex.add_document`
never triggers a full rebuild, even when a document is re-uploaded or
edited. This produces a meaningfully different engineering problem than indexing a static corpus.

## Stack

Single Python application: FastAPI + SQLite (via SQLAlchemy) + a vanilla
JS frontend, no separate frontend build or framework. Everything runs as
one process — no external search engine, no managed database, no queue.

## Architecture

```
 upload (PDF/txt) ──▶ extractor.py ──▶ raw text
                                          │
                                          ▼
                                    storage/db.py   (SQLite: persisted docs,
                                                      survives restarts)
                                          │
                                          ▼
                                   tokenizer.py ──▶ tokens
                                          │
                                          ▼
                                    indexer.py    (inverted index: raw term
                                                    counts + doc lengths only,
                                                    updated incrementally per
                                                    upload — never rebuilt)
                                          │
 query ──▶ tokenizer.py ──▶ tokens ──▶ ranker.py  (TF-IDF / BM25 scoring,
                                                     sum across query terms,
                                                     sort by relevance)
                                          │
                                          ▼
                                   snippets.py    (highlighted excerpt
                                                    around the first match,
                                                    per result)
                                          │
                                          ▼
                                  ranked results ──▶ frontend
```

The indexer stores only raw facts — term counts per document, and
document lengths. All scoring logic lives in `ranker.py`, which is why
TF-IDF and BM25 can share the same `rank()` function: it is indifferent to the formula it's using, it just sums per-token scores across the
query and sorts. This makes it simpler to add additional ranking methods through writing a new scoring function and all other files remain untouched.

## Project structure

```
document-retrieval/
├── app/
│   ├── main.py               FastAPI app: /upload, /search, /documents, /health
│   ├── ingestion/
│   │   └── extractor.py      PDF (pdfplumber) / txt / md text extraction
│   ├── retrieval/
│   │   ├── tokenizer.py      lowercase, split, stop-word removal
│   │   ├── indexer.py        inverted index: raw counts + doc lengths only
│   │   ├── ranker.py         TF-IDF and BM25 scoring, swappable via `method`
│   │   └── snippets.py       highlighted, context-window snippet extraction
│   ├── storage/
│   │   └── db.py             SQLite persistence (Document table)
│   └── static/                index.html / style.css / script.js, no build step
├── tests/                     20 unit tests covering tokenizer/indexer/ranker
├── benchmark.py                40-document benchmark: accuracy + latency
├── resilience_benchmark.py     adversarial test cases (see below)
├── sample_docs/                a few files to demo with immediately
├── requirements.txt
└── Procfile                    for Render/Heroku-style deployment
```

## How the ranking works

The indexer tracks two things per document: how many times each token
appears in it, and how many tokens it has in total. `ranker.py` turns
those raw facts into relevance scores.

**TF-IDF** — `score = tf × idf`, where `idf = log((N+1)/(df+1)) + 1`. `tf`
is how often the query term appears in this document; `idf` down-weights
terms that appear in many documents (common words carry little signal
about what makes one document more relevant than another) and up-weights
rare, distinguishing terms.

**BM25** — improves on TF-IDF in two ways. Term frequency *saturates*:
mentioning a word 50 times in a document doesn't count anywhere near 50x
as much as mentioning it once, because there are diminishing returns past
a point. And scores are *normalized by document length*, so a long
document doesn't win purely by containing more words overall. Two tunable
parameters control this: `k1` (how fast term frequency saturates) and `b`
(how strongly document length is penalized) — this implementation uses
the standard defaults (`k1=1.5`, `b=0.75`) from the original Okapi BM25
research.

Both scorers share the exact same signature
(`(index, token, doc_id) -> float`), which is what lets `rank()` stay
completely agnostic to which formula is in use.

## Running it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000`. Upload a few files from `sample_docs/`,
then search and compare BM25 vs. TF-IDF results.

## Testing

**Unit tests** — 20 tests across tokenizer, indexer, and ranker:

```bash
pytest tests/ -v
```

These aren't just "did this return a number without crashing" checks.
Several specifically verify *ranking order* against hand-constructed
cases where the correct answer is known ahead of time, including BM25's
distinguishing behaviors: `test_bm25_length_normalization` confirms a
short, focused document can outrank a much longer one mentioning the
same term the same number of times, and
`test_bm25_term_frequency_saturation` confirms that 10 mentions of a term
scores higher than 1 mention, but nowhere near proportionally higher.

**Benchmark** — a 40-document corpus across 8 distinct topics, run with:

```bash
python benchmark.py
```

Reports indexing time, and top-1 topic accuracy + average query latency
for both ranking methods across 16 labeled test queries.

**Resilience / adversarial tests** — harder, deliberately adversarial
cases, run with:

```bash
python resilience_benchmark.py
```
Three specific failure modes a naive ranker would fall into:

1. *Keyword-stuffing resistance* — a real, relevant document vs. a spam
   document that just repeats a term 11 times with no real content.
2. *Length adversarial* — a short, focused document vs. a long document
   that mentions the topic once, buried in unrelated content.
3. *Lexical ambiguity* — the same word used in two unrelated senses (e.g.
   "python" the language vs. "python" the snake). With disambiguating
   query context this resolves correctly; with a single ambiguous word
   alone, it can't — which is a known limitation of bag-of-words ranking,


"On this implementation, BM25 correctly favored the real document over
the keyword-stuffed spam document (score 4.2934 vs. 1.2331), while TF-IDF was
incorrectly favored the spam document's raw repetition (score 5.6027 vs. 16.8656) -- a direct,
measured demonstration of BM25's term-frequency saturation."

## Known limitations

- **No semantic understanding.** Ranking is purely bag-of-words term
  matching — it can't disambiguate word sense (see the lexical ambiguity
  test above) or match synonyms/paraphrases that don't share exact
  tokens.
- **No phrase search.** Queries are treated as independent terms, not
  exact phrases — there's no way to search for an exact multi-word
  sequence.
- **No pagination** on search results (returns top-k only).
- **Single-process only.** The in-memory index lives in one process's
  memory; this wouldn't work unmodified across multiple backend
  instances without a shared index store.
- **SQLite on free-tier hosts** typically has an ephemeral disk, so the
  document store resets on redeploy unless paired with persistent
  storage.

## What's next

- Add term-density penalty to mitigate keyword stuffing through applying threshold value 
- Wire `/upload` and `/search` against the SQLite-backed document
  store (in progress)
- Vanilla JS frontend for upload + search
- Deploy to Render
