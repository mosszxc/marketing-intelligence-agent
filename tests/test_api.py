"""Tests for Phase 14: FastAPI backend API."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_body(self, client):
        data = client.get("/api/health").json()
        assert data["status"] == "ok"
        assert "version" in data


# ── Query ─────────────────────────────────────────────────────────────────

class TestQuery:
    def test_query_returns_plan_and_answer(self, client):
        resp = client.post("/api/query", json={"query": "ROI по каналам"})
        assert resp.status_code == 200
        data = resp.json()
        assert "thread_id" in data
        assert isinstance(data["plan"], list)
        assert len(data["plan"]) > 0
        assert len(data["final_answer"]) > 0

    def test_query_analytics_only(self, client):
        resp = client.post("/api/query", json={"query": "Покажи расходы по каналам"})
        data = resp.json()
        assert "analytics" in data["plan"]

    def test_query_research_only(self, client):
        resp = client.post("/api/query", json={"query": "Тренды AI маркетинга 2026"})
        data = resp.json()
        assert "research" in data["plan"]

    def test_query_with_thread_id(self, client):
        resp = client.post("/api/query", json={
            "query": "ROI по каналам",
            "thread_id": "test-thread-123",
        })
        data = resp.json()
        assert data["thread_id"] == "test-thread-123"

    def test_query_invalid_body_422(self, client):
        resp = client.post("/api/query", json={})
        assert resp.status_code == 422

    def test_query_empty_string_422(self, client):
        resp = client.post("/api/query", json={"query": ""})
        assert resp.status_code == 422

    def test_thread_isolation(self, client):
        r1 = client.post("/api/query", json={"query": "ROI по каналам"})
        r2 = client.post("/api/query", json={"query": "Тренды рынка"})
        assert r1.json()["thread_id"] != r2.json()["thread_id"]


# ── Stream ────────────────────────────────────────────────────────────────

class TestStream:
    def test_stream_returns_sse(self, client):
        resp = client.post(
            "/api/query/stream",
            json={"query": "ROI по каналам"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_stream_contains_events(self, client):
        resp = client.post(
            "/api/query/stream",
            json={"query": "ROI по каналам"},
        )
        body = resp.text
        assert "event:" in body
        assert "data:" in body

    def test_stream_ends_with_done(self, client):
        resp = client.post(
            "/api/query/stream",
            json={"query": "ROI по каналам"},
        )
        lines = [ln for ln in resp.text.strip().split("\n") if ln.startswith("event:")]
        assert any("done" in ln for ln in lines)


# ── HITL Approve ──────────────────────────────────────────────────────────

class TestApprove:
    def _start_hitl_query(self, client):
        """Start a HITL query and return the thread_id + plan."""
        resp = client.post("/api/query", json={
            "query": "ROI по каналам",
        }, params={"hitl": "true"})
        data = resp.json()
        return data["thread_id"], data.get("plan", [])

    def test_approve_resumes_graph(self, client):
        thread_id, plan = self._start_hitl_query(client)
        if not plan:
            pytest.skip("HITL not triggered")
        resp = client.post("/api/approve", json={"thread_id": thread_id})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["final_answer"]) > 0

    def test_approve_with_modified_plan(self, client):
        thread_id, plan = self._start_hitl_query(client)
        if not plan:
            pytest.skip("HITL not triggered")
        resp = client.post("/api/approve", json={
            "thread_id": thread_id,
            "plan": ["analytics"],
        })
        assert resp.status_code == 200

    def test_approve_invalid_thread(self, client):
        resp = client.post("/api/approve", json={"thread_id": "nonexistent"})
        assert resp.status_code in (404, 400)


# ── CORS ──────────────────────────────────────────────────────────────────

# ── Upload CSV ────────────────────────────────────────────────────────────

class TestUpload:
    def test_upload_valid_csv(self, client):
        csv_content = (
            "date,channel,impressions,clicks,conversions,spend,revenue\n"
            "2025-01-01,google,1000,50,5,100,500\n"
        )
        resp = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["rows"] == 1
        assert data["filename"] == "test.csv"

    def test_upload_invalid_extension(self, client):
        resp = client.post(
            "/api/upload",
            files={"file": ("test.txt", "hello", "text/plain")},
        )
        assert resp.status_code == 400

    def test_upload_invalid_csv_columns(self, client):
        csv_content = "name,age\nalice,30\n"
        resp = client.post(
            "/api/upload",
            files={"file": ("bad.csv", csv_content, "text/csv")},
        )
        assert resp.status_code == 422


# ── CORS ──────────────────────────────────────────────────────────────────

class TestCORS:
    def test_cors_allows_localhost(self, client):
        resp = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") in (
            "http://localhost:5173",
            "*",
        )
