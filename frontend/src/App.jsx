import { useState, useEffect } from "react";
import { checkHealth, uploadDocument, searchDocuments, listDocuments, clearDocuments } from "./api";
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

  useEffect(() => {
    loadDocs();
  }, []);

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
    loadDocs();
    runSearch(query, method);
  }

  function handleSearch(e) {
    e.preventDefault();
    runSearch(query, method);
  }

  async function handleClear() {
    await clearDocuments();
    setResults([]);
    setUploadMsg("");
    loadDocs();
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
        <div className="doc-list-header">
          <h2>Documents ({docs.length})</h2>
          {docs.length > 0 && (
            <button type="button" className="clear-btn" onClick={handleClear}>
              Clear all
            </button>
          )}
        </div>
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