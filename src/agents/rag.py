"""RAG Agent — retrieval-augmented generation over company documents.

Searches ChromaDB vector store for relevant chunks, then generates
an answer with citations. No LLM required — uses extractive approach
as fallback.
"""

from src.state import AgentOutput
from src.tools.vector_store import search


def run_rag(query: str, collection: str = "company_docs") -> AgentOutput:
    """Run RAG: retrieve relevant chunks → format answer with citations.

    Args:
        query: User question about company documents.
        collection: ChromaDB collection to search.

    Returns AgentOutput with summary and sources.
    """
    results = search(query, collection=collection, k=5)

    if not results:
        return AgentOutput(
            summary="Документы не найдены. Загрузите PDF/TXT через UI для анализа.",
            data={},
            charts=[],
            sources=[],
            error=None,
        )

    # Build answer from retrieved chunks
    parts = [f"### Найдено в документах ({len(results)} фрагментов)\n"]

    sources = []
    seen_sources = set()

    for i, doc in enumerate(results, 1):
        content = doc.page_content.strip()
        source = doc.metadata.get("source", "unknown")

        parts.append(f"**[{i}]** {content}\n")

        if source not in seen_sources:
            seen_sources.add(source)
            sources.append({
                "title": source.split("/")[-1] if "/" in source else source,
                "url": source,
                "snippet": content[:100],
            })

    summary = "\n".join(parts)

    return AgentOutput(
        summary=summary,
        data={},
        charts=[],
        sources=sources,
        error=None,
    )
