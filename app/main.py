
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import UploadFile, File, Depends, HTTPException

from pathlib import Path
import shutil
import uuid
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.storage.db import init_db, get_db, all_documents, Document
from app.retrieval.tokenizer import tokenize
from app.retrieval.indexer import InvertedIndex
from app.retrieval.ranker import rank
from app.retrieval.snippets import make_snippet
from app.ingestion.extractor import extract_text




index = InvertedIndex()
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = next(get_db())
    for doc in all_documents(db):
        tokens = tokenize(doc.extracted_text)
        index.add_document(doc.id, tokens)
        doc_store[doc.id] = {"filename": doc.file_name, "extracted_text": doc.extracted_text}
    db.close()
    yield


app = FastAPI(title="Document Retrieval System", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}

UPLOAD_DIR = Path("./uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    doc_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix 
    dest_path = UPLOAD_DIR / f"{doc_id}{suffix}"

    with dest_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        text = extract_text(str(dest_path), suffix)
    except ValueError as e:
        raise HTTPException(400, str(e))
    new_doc = Document(
        id = doc_id,
        file_name = file.filename,
        content_type = file.content_type,
        file_size_bytes=dest_path.stat().st_size,
        extracted_text=text,
        uploaded_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(new_doc)
    db.commit()
    tokens = tokenize(text)
    index.add_document(doc_id, tokens)

    doc_store[doc_id] = {"filename": new_doc.file_name, "extracted_text": new_doc.extracted_text}

    return {
    "id": doc_id,
    "tokens_indexed": len(tokens),
    }


doc_store: dict[str, dict] = {}

@app.get("/search")
def search(q: str, method: str = "bm25"):
    query_tokens = tokenize(q)
    results = rank(index, query_tokens, method)

    output = []
    for doc_id, score in results:
        info = doc_store.get(doc_id)
        if not info:
            continue
        snippet = make_snippet(info["extracted_text"], query_tokens)
        output.append({
            "id" : doc_id,
            "filename": info["filename"],
            "score": round(score, 4),
            "snippet" : snippet,
        })
    return {"query": q, "method": method, "results": output}
