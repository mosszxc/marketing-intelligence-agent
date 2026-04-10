"""Vector store — ChromaDB wrapper for document retrieval.

Uses ChromaDB with default embedding function (all-MiniLM-L6-v2 via sentence-transformers
if available, otherwise Chroma's built-in embedding).
"""

import chromadb
from langchain_core.documents import Document

# Persistent client — stores in memory for dev/test, can switch to persistent path
_client = chromadb.Client()


def index_documents(
    docs: list[Document],
    collection: str = "company_docs",
) -> int:
    """Index documents into ChromaDB collection.

    Args:
        docs: List of LangChain Document objects.
        collection: ChromaDB collection name.

    Returns number of documents indexed.
    """
    col = _client.get_or_create_collection(name=collection)

    ids = []
    documents = []
    metadatas = []
    for i, doc in enumerate(docs):
        doc_id = f"{collection}_{i}_{hash(doc.page_content) % 10000}"
        ids.append(doc_id)
        documents.append(doc.page_content)
        metadatas.append(doc.metadata or {})

    col.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(docs)


def search(
    query: str,
    collection: str = "company_docs",
    k: int = 5,
) -> list[Document]:
    """Search ChromaDB collection for relevant documents.

    Args:
        query: Search query string.
        collection: ChromaDB collection name.
        k: Number of results to return.

    Returns list of LangChain Document objects sorted by relevance.
    """
    try:
        col = _client.get_collection(name=collection)
    except Exception:
        return []

    results = col.query(query_texts=[query], n_results=min(k, col.count()))

    docs = []
    for content, metadata in zip(
        results["documents"][0],
        results["metadatas"][0],
    ):
        docs.append(Document(page_content=content, metadata=metadata))

    return docs
