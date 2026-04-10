"""Document loader — chunking for RAG pipeline.

Supports TXT and PDF files. Uses RecursiveCharacterTextSplitter for chunking.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_chunk(
    path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[Document]:
    """Load a document file and split into chunks.

    Args:
        path: Path to TXT or PDF file.
        chunk_size: Max characters per chunk.
        chunk_overlap: Overlap between consecutive chunks.

    Returns list of Document objects with page_content and metadata.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    if p.suffix == ".pdf":
        text = _load_pdf(p)
    else:
        text = p.read_text(encoding="utf-8", errors="replace")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    chunks = splitter.create_documents(
        texts=[text],
        metadatas=[{"source": str(path)}],
    )

    return chunks


def _load_pdf(path: Path) -> str:
    """Extract text from PDF. Falls back to empty string if extraction fails."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        # PyPDF2 not installed — read as binary and try basic extraction
        return path.read_text(encoding="utf-8", errors="replace")
