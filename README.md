# Document Retrieval System
 
A document retrieval system that ingests uploaded PDF and text files,
indexes their content, and returns ranked search results with highlighted,
context-aware snippets.
 
**Live:** [documentretrievalsystem.onrender.com](https://documentretrievalsystem.onrender.com)
 
## Status
 
**Core retrieval engine, backend, frontend, and deployment complete.**
 
- [x] Tokenizer (`app/retrieval/tokenizer.py`)
- [x] Inverted index with incremental add/replace/remove (`app/retrieval/indexer.py`)
- [x] TF-IDF ranking (`app/retrieval/ranker.py`)
- [x] BM25 ranking (`app/retrieval/ranker.py`)
- [x] Snippet extraction with query-term highlighting (`app/retrieval/snippets.py`)
- [x] PDF/text extraction (`app/ingestion/extractor.py`)
- [x] SQLite storage (`app/storage/db.py`)
- [x] `/upload`, `/search`, `/documents`, `/health` endpoints (`app/main.py`)
- [x] React frontend — upload panel, live document list, debounced search, ranked result cards
- [x] Unit tests for tokenizer, indexer, ranker (20 tests, all passing)
- [x] Integration tests for the full API (`tests/test_main.py`, 6 tests, all passing)
- [x] Deployed to Render as a single service
## Difference from a search engine
 
Most small information-retrieval projects load a fixed corpus once at
startup and never touch the index again. This is a genuine *retrieval
system*: documents are uploaded by a user at any time, and the index is
updated incrementally as each one arrives — `InvertedIndex.add_document`
never triggers a full rebuild, even when a document is re-uploaded or
edited. That's a meaningfully different (and slightly harder) engineering
problem than indexing a static corpus.
 
## Stack
 
FastAPI + SQLite (via SQLAlchemy) on the backend, a React (Vite) frontend
on top. Both are built and deployed as a **single Render service** — the
backend serves the compiled React app directly (`StaticFiles` mount), so
there's one URL, one process, and no CORS to manage in production. No
external search engine, no managed database, no queue.
 
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
                                  ranked results ──▶ React frontend
```
 
The indexer stores only raw facts — term counts per document, and
document lengths. All scoring logic lives in `ranker.py`, which is why
TF-IDF and BM25 can share the same `rank()` function: it doesn't know or
care which formula it's using, it just sums per-token scores across the
query and sorts. Adding a third ranking method later means writing one
new scoring function, not touching the indexer, the API, or the frontend.
 
## Project structure
 
```
document-retrieval/
├── app/
│   ├── main.py               FastAPI app: /upload, /search, /documents, /health
│   │                          + serves the built React app at /
│   ├── ingestion/
│   │   └── extractor.py      PDF (pdfplumber) / txt / md text extraction
│   ├── retrieval/
│   │   ├── tokenizer.py      lowercase, split, stop-word removal
│   │   ├── indexer.py        inverted index: raw counts + doc lengths only
│   │   ├── ranker.py         TF-IDF and BM25 scoring, swappable via `method`
│   │   └── snippets.py       highlighted, context-window snippet extraction
│   └── storage/
│       └── db.py             SQLite persistence (Document table)
├── frontend/                  React (Vite)
│   ├── src/
│   │   ├── App.jsx           upload panel, live document list, search, ranked results
│   │   ├── api.js            fetch wrappers for the backend API
│   │   └── App.css           black-and-white, monospace/typewriter styling
│   └── dist/                  production build, committed and served by FastAPI
├── tests/                     20 unit tests + 6 integration tests
├── benchmark.py                40-document benchmark: accuracy + latency
├── resilience_benchmark.py     adversarial test cases (see below)
├── cranfield_eval.py           real IR benchmark evaluation (see below)
├── k1_sweep.py                 BM25 k1 parameter sweep
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
 
## Running it locally
 
Two processes, both need to stay running at once:
 
```bash
# terminal 1 — backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
 
# terminal 2 — frontend
cd frontend
npm install
npm run dev
```
 
Open `http://localhost:5173`. Upload a few files from `sample_docs/`,
then search and compare BM25 vs. TF-IDF results.
 
## Deployment
 
Deployed as a single Render Web Service — no separate frontend host:
 
1. `npm run build` in `frontend/` produces `frontend/dist/`, which is
   committed to the repo.
2. `app/main.py` mounts that build directory with `StaticFiles`, after
   all API routes, so `/upload`, `/search`, `/documents`, and `/health`
   still resolve correctly and everything else falls through to serving
   the React app.
3. `frontend/api.js` calls the API with relative paths (`fetch("/health")`,
   not an absolute URL) in production, since the frontend and backend
   are served from the same origin — no CORS configuration needed
   outside of local development.
4. Render build command: `pip install -r requirements.txt`. Start
   command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
Note: Render's free tier spins down after inactivity, so the first
request after idling can take 30–50 seconds while it restarts.
 
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
 
**Integration tests** — 6 end-to-end tests against the full FastAPI app
(upload → index → search → results), using an isolated test database:
 
```bash
pytest tests/test_main.py -v
```
 
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
   alone, it can't — a known limitation of bag-of-words ranking, not a
   bug.
**Results:** on the keyword-stuffing test, BM25 correctly favored the
real document over the spam document (4.29 vs. 1.23), while TF-IDF was
fooled by the spam document's raw repetition (16.87 vs. 5.60 — spam
won) — a direct, measured demonstration of BM25's term-frequency
saturation actually working, not just a claim about it. On the single
ambiguous-word query with no disambiguating context, both rankers were
fooled by the spam document, which is the expected, known limit of
term-frequency-only ranking (see Known limitations below) rather than a
bug to fix.
 
## Evaluation against a real IR benchmark
 
Beyond the synthetic tests above, this was evaluated against the
[Cranfield test collection](https://ir-datasets.com/cranfield.html) —
1,400 real documents, 225 real queries, and genuine human relevance
judgments, a standard evaluation set used in IR research since the
1960s. Unlike the synthetic benchmarks, this measures real
precision/recall/MRR rather than a proxy like topic accuracy:
 
```bash
pip install ir_datasets
python cranfield_eval.py
```
 
| Metric        | BM25   | TF-IDF |
|---------------|--------|--------|
| Precision@10  | 0.2378 | 0.1813 |
| Recall@10     | 0.4021 | 0.3064 |
| MRR           | 0.5246 | 0.4461 |
 
BM25 outperforms TF-IDF across every metric — consistent with published
IR literature, and a reasonable sign this implementation is behaving
like a correct BM25 rather than something subtly broken. MRR of 0.52
means the first relevant result appears at rank ~2 on average; Recall@10
of 0.40 means roughly 40% of all documents judged relevant to a query
are found within the top 10 results.
 
## Known limitations
 
Being upfront about these rather than hiding them:
 
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
 
- Add a term-density penalty to further mitigate keyword stuffing
  (thresholding on term-frequency-to-length ratio, beyond what BM25's
  saturation already handles)
- Persistent disk or external storage so the document store survives
  redeploys on Render's free tier
- Phrase search and pagination
 
