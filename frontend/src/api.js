const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function checkHealth(){
    const res = await fetch(`${API_BASE}/health`);
    if(!res.ok){
        throw new Error("Backend connection health error");
    }
    return res.json();
}

export async function uploadDocument(file){
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
    });

    if(!res.ok){
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || "Upload failed");
    }
}

export async function searchDocuments(query, method){
    const params = new URLSearchParams({query, method});
    const res = await fetch(`${API_BASE}/search?${params.toString()}`);

    if(!res.ok){
        throw new Error("Search failed");
    }

    return res.json();
}

export async function listDocuments() {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) {
    throw new Error("Failed to load documents");
  }
  return res.json();
}