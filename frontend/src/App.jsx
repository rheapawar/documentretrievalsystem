/*
 * TODO: build this component yourself. It needs to do exactly what your
 * vanilla-JS script.js already does -- upload a file, search, render
 * results -- just using React state instead of manually querying and
 * mutating DOM elements. That translation (imperative DOM updates ->
 * declarative state + re-render) is the actual React skill being shown
 * here, not the fetch calls themselves (those are already done for you
 * in api.js).
 *
 * ---- State you'll need (useState) ----
 *   1. backendStatus  -- "checking..." | "connected" | "unreachable"
 *      Set this once on mount via useEffect, by calling checkHealth().
 *   2. file           -- the currently selected File object (or null),
 *      from a controlled <input type="file">.
 *   3. uploadMsg      -- text to show under the upload form (status/errors).
 *   4. query          -- the search input's current text (controlled input).
 *   5. method         -- "bm25" | "tfidf", from a <select>.
 *   6. results        -- array of result objects from the last search.
 *   7. searching       -- boolean, true while a search request is in flight
 *      (used to disable the search button and show "Searching...").
 *
 * ---- Effects ----
 *   On mount (empty dependency array), call checkHealth() from api.js and
 *   set backendStatus based on whether it succeeds or throws.
 *
 * ---- Handlers ----
 *   handleUpload(e):
 *     - e.preventDefault()
 *     - if no file selected, return early
 *     - set uploadMsg to "Uploading..."
 *     - call uploadDocument(file), await the result
 *     - on success: show tokens_indexed in uploadMsg
 *     - on failure: show err.message in uploadMsg
 *     - wrap the await in try/catch
 *
 *   handleSearch(e):
 *     - e.preventDefault()
 *     - if query is empty/whitespace, return early
 *     - set searching to true
 *     - call searchDocuments(query, method), await the result
 *     - set results to data.results (default to [] if missing)
 *     - set searching back to false in a finally block
 *
 * ---- JSX structure ----
 *   - A header showing the title and backendStatus
 *   - An upload <form onSubmit={handleUpload}> with a file input and
 *     submit button, plus the uploadMsg text below it
 *   - A search <form onSubmit={handleSearch}> with a text input (bound to
 *     query), a method <select> (bound to method), and a submit button
 *   - A results list: results.map(r => ...) rendering each result's
 *     filename, score, and snippet
 *
 * ---- One important gotcha ----
 *   Each result's `snippet` field contains literal <mark> tags from your
 *   backend (e.g. "the <mark>fox</mark> jumps"), meant to render as HTML
 *   for the highlighting to actually show up. If you render it as plain
 *   text (e.g. {r.snippet} directly in JSX), React will escape it and
 *   you'll see literal "<mark>" text on the page instead of highlighting.
 *   You need React's dangerouslySetInnerHTML for just that one field:
 *
 *     <p dangerouslySetInnerHTML={{ __html: r.snippet }} />
 *
 *   The name is a deliberate warning label from the React team -- it's
 *   normally how XSS vulnerabilities get introduced, since it renders raw
 *   HTML with no escaping. It's fine here specifically because YOUR OWN
 *   backend builds this string (not an untrusted user directly), but
 *   it's worth understanding why the API is named this scarily on
 *   purpose, and why you should never reach for it as a default habit.
 *
 * ---- Don't forget ----
 *   Every item in a .map()'d list needs a unique `key` prop -- use
 *   `r.id` here, not the array index.
 */

import { useState, useEffect } from "react";
import { checkHealth, uploadDocument, searchDocuments, listDocuments } from "./api";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [uploadMsg, setUploadMsg] = useState("");
  const [query, setQuery] = useState("");
  const [method, setMethod] = useState("bm25");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [backendStatus, setBackendStatus] = useState("checking...");
  const [docs, setDocs] = useState([]);

  useEffect(() => {
    checkHealth()
      .then(() => setBackendStatus("connected"))
      .catch(() => setBackendStatus("disconnected"));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() =>{
      runSearch(query, method);
    }, 300);
    return () => clearTimeout(timer);
  }, [query, method]);


  async function loadDocs() {
  try {
    const data = await listDocuments();
    setDocs(data.documents || []);
  } catch {
    setDocs([]);
  }
}

  async function runSearch(q, m) {
    if(!q.trim()){
      setResults([]);
      return;
    }
    setSearching(true);
    try{
      const data = await searchDocuments(q,m);
      setResults(data.results || []);
    } catch{
      setResults([]);
    } finally{
      setSearching(false);
    }
  }

  async function handleUpload(e) {
    e.preventDefault();
    if(!file){
      return;
    }

    setUploadMsg("Uploading...");

    try{
      const data = await uploadDocument(file);
      setUploadMsg(`Indexed ${data.tokens_indexed} tokens.`);
      setFile(null);
    }catch(err){
      setUploadMsg(`Error: ${err.message}`);
    }
    runSearch(query, method);
  }

  function handleSearch(e) {
    e.preventDefault();
    runSearch(query, method);  
  }

  return (
  <div className="app">
    <aside className="sidebar">
      <h1>Document Retrieval</h1>
      <p className="status">Backend: {backendStatus}</p>

      <form onSubmit={handleUpload} className="upload-form">
        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
        <button type="submit">Upload</button>
        <p className="upload-msg">{uploadMsg}</p>
      </form>

      <div className="doc-list">
        <h2>Documents ({docs.length})</h2>
        <ul>
          {docs.map((d) => (
            <li key={d.id}>{d.filename}</li>
          ))}
        </ul>
      </div>
    </aside>

    <main className="main">
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search documents..."
        />
        <select value={method} onChange={(e) => setMethod(e.target.value)}>
          <option value="bm25">BM25</option>
          <option value="tfidf">TF-IDF</option>
        </select>
        <button type="submit" disabled={searching}>
          {searching ? "Searching..." : "Search"}
        </button>
      </form>

      <div className="results">
        {results.map((r, i) => (
          <div key={r.id} className="result-card">
            <div className="rank">{i + 1}</div>
            <div className="result-content">
              <div className="result-header">
                <span className="filename">{r.filename}</span>
                <span className="score">{r.score}</span>
              </div>
              <p className="snippet" dangerouslySetInnerHTML={{ __html: r.snippet }} />
            </div>
          </div>
        ))}
      </div>
    </main>
  </div>
);
}

export default App;