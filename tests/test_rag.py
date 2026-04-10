"""Tests for Phase 13: RAG — document loading, vector store, RAG agent."""

import os
import tempfile

import pytest


# ── Document Loader ───────────────────────────────────────────────────────

class TestDocumentLoader:
    def test_load_txt_file(self):
        from src.tools.doc_loader import load_and_chunk

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Marketing strategy for Q1 2026. Focus on retargeting and email campaigns. " * 20)
            path = f.name

        try:
            chunks = load_and_chunk(path)
            assert len(chunks) >= 1
            assert all(hasattr(c, "page_content") for c in chunks)
            assert "Marketing strategy" in chunks[0].page_content
        finally:
            os.unlink(path)

    def test_chunk_size_respected(self):
        from src.tools.doc_loader import load_and_chunk

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Word " * 500)  # ~2500 chars
            path = f.name

        try:
            chunks = load_and_chunk(path, chunk_size=500, chunk_overlap=100)
            assert len(chunks) >= 3  # 2500 / 500 ~= 5 chunks
            for c in chunks:
                assert len(c.page_content) <= 600  # some tolerance for overlap
        finally:
            os.unlink(path)

    def test_metadata_has_source(self):
        from src.tools.doc_loader import load_and_chunk

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content for metadata check.")
            path = f.name

        try:
            chunks = load_and_chunk(path)
            assert chunks[0].metadata.get("source") == path
        finally:
            os.unlink(path)


# ── Vector Store ──────────────────────────────────────────────────────────

class TestVectorStore:
    def test_index_and_search(self):
        from langchain_core.documents import Document
        from src.tools.vector_store import index_documents, search

        docs = [
            Document(page_content="Email campaign had 15% open rate in January", metadata={"source": "test"}),
            Document(page_content="Retargeting ROAS was 8.11 in Q4", metadata={"source": "test"}),
            Document(page_content="Social media strategy focuses on TikTok and Instagram", metadata={"source": "test"}),
        ]

        index_documents(docs, collection="test_collection")
        results = search("email open rate", collection="test_collection", k=2)

        assert len(results) >= 1
        assert any("email" in r.page_content.lower() for r in results)

    def test_search_returns_relevant(self):
        from langchain_core.documents import Document
        from src.tools.vector_store import index_documents, search

        docs = [
            Document(page_content="Budget allocation: 40% to Google Ads, 30% to Meta, 30% to Email", metadata={"source": "test"}),
            Document(page_content="Weather forecast for next week shows rain", metadata={"source": "test"}),
        ]

        index_documents(docs, collection="test_relevance")
        results = search("budget allocation", collection="test_relevance", k=1)

        assert len(results) == 1
        assert "budget" in results[0].page_content.lower()


# ── RAG Agent ─────────────────────────────────────────────────────────────

class TestRAGAgent:
    @pytest.fixture(autouse=True)
    def _index_test_docs(self):
        """Pre-index some test documents for RAG queries."""
        from langchain_core.documents import Document
        from src.tools.vector_store import index_documents

        docs = [
            Document(page_content="Our Q1 2026 strategy: increase email budget by 20%, reduce brand awareness spend. Focus on retargeting.", metadata={"source": "strategy.pdf"}),
            Document(page_content="KPI targets: Email open rate > 20%, ROAS > 5 for retargeting, CPA < 500 RUB.", metadata={"source": "kpi.pdf"}),
            Document(page_content="Competitor analysis: CompetitorX launched a TikTok campaign with 3x our spend.", metadata={"source": "competitors.pdf"}),
        ]
        index_documents(docs, collection="company_docs")

    def test_rag_agent_returns_answer(self):
        from src.agents.rag import run_rag
        result = run_rag("Какая у нас стратегия по email?")
        assert len(result["summary"]) > 0
        assert "email" in result["summary"].lower()

    def test_rag_agent_cites_sources(self):
        from src.agents.rag import run_rag
        result = run_rag("Какие KPI цели?")
        sources = result.get("sources", [])
        assert len(sources) >= 1

    def test_rag_agent_output_structure(self):
        from src.agents.rag import run_rag
        result = run_rag("Что делают конкуренты?")
        assert "summary" in result
        assert "sources" in result
        assert "error" in result


# ── Supervisor Routing ────────────────────────────────────────────────────

class TestRAGRouting:
    def test_routes_document_query_to_rag(self):
        from src.agents.supervisor import classify_query
        plan = classify_query("Что написано в нашей стратегии?")
        assert "rag" in plan

    def test_routes_plan_query_to_rag(self):
        from src.agents.supervisor import classify_query
        plan = classify_query("Какие KPI в документе?")
        assert "rag" in plan


# ── Graph Integration ─────────────────────────────────────────────────────

class TestRAGGraphIntegration:
    @pytest.fixture(autouse=True)
    def _index_docs(self):
        from langchain_core.documents import Document
        from src.tools.vector_store import index_documents
        index_documents([
            Document(page_content="Company plan: scale retargeting to 50% of total budget by Q3.", metadata={"source": "plan.pdf"}),
        ], collection="company_docs")

    def test_rag_node_in_graph(self):
        from src.graph import build_graph
        graph = build_graph()
        config = {"configurable": {"thread_id": "test-rag-1"}}
        result = graph.invoke({"query": "Что в нашем плане по ретаргетингу?"}, config)
        assert "rag" in result.get("plan", [])
        assert len(result.get("final_answer", "")) > 0
