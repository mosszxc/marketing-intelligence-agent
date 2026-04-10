"""Tests for Phase 14.3: React + FastAPI integration (Playwright).

Run with: pytest tests/test_react_integration.py
Requires both FastAPI (port 8000) and React dev server (port 5173) running.
"""

import subprocess

import pytest
import requests

API_URL = "http://localhost:8000"
UI_URL = "http://localhost:5173"


def _api_running():
    try:
        return requests.get(f"{API_URL}/api/health", timeout=2).status_code == 200
    except Exception:
        return False


def _ui_running():
    try:
        return requests.get(UI_URL, timeout=2).status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="module")
def check_servers():
    if not _api_running():
        pytest.skip("FastAPI not running on :8000")
    if not _ui_running():
        pytest.skip("React dev server not running on :5173")


class TestE2EIntegration:
    """E2E tests that verify React UI talks to FastAPI correctly."""

    def test_api_health_from_ui_perspective(self, check_servers):
        resp = requests.get(f"{API_URL}/api/health")
        assert resp.json()["status"] == "ok"

    def test_query_roundtrip(self, check_servers):
        resp = requests.post(f"{API_URL}/api/query", json={"query": "ROI по каналам"})
        data = resp.json()
        assert data["final_answer"]
        assert data["plan"]

    def test_stream_roundtrip(self, check_servers):
        resp = requests.post(
            f"{API_URL}/api/query/stream",
            json={"query": "ROI по каналам"},
            stream=True,
        )
        events = []
        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("event:"):
                events.append(line)
        assert len(events) > 0

    def test_ui_serves_html(self, check_servers):
        resp = requests.get(UI_URL)
        assert "<!doctype html>" in resp.text.lower() or "<html" in resp.text.lower()

    def test_ui_has_react_root(self, check_servers):
        resp = requests.get(UI_URL)
        assert 'id="root"' in resp.text


class TestBuildArtifacts:
    """Verify that the React project builds without errors."""

    def test_npm_build_succeeds(self):
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd="/home/dev-moss/paperclip/projects/marketing-intelligence-agent/ui",
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

    def test_build_output_exists(self):
        import os
        dist = "/home/dev-moss/paperclip/projects/marketing-intelligence-agent/ui/dist"
        assert os.path.isdir(dist), "dist/ directory not found after build"
        assert os.path.isfile(os.path.join(dist, "index.html")), "index.html not in dist/"
