
from pathlib import Path

import pdfplumber

def extract_text(file_path: str, content_type: str = "") -> str:

  suffix = Path(file_path).suffix.lower()

  if suffix == ".txt" or suffix == ".md":
    return Path(file_path).read_text(encoding="utf-8", errors="ignore")
  
  elif content_type == ".pdf":
    content_parts  =[]
    with pdfplumber.open(file_path) as pdf:
      for page in pdf.pages:
        content = page.extract_text() or ""
        content_parts.append(content)
      return "\n".join(content_parts)

  raise ValueError(f"Unsupported file type: {suffix}")