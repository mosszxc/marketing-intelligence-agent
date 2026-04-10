"""FastAPI backend for the Marketing Intelligence Agent.

Endpoints:
    POST /api/query         — run full graph, return result
    POST /api/query/stream  — SSE streaming of graph execution
    POST /api/approve       — resume HITL graph after approval
    GET  /api/health        — health check
"""

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from src.api.schemas import (
    ApproveRequest,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SourceItem,
)
from src.graph import build_graph

app = FastAPI(title="Marketing Intelligence API", version="0.2.0")

# Serve React static build if available (Docker production)
_static_dir = Path(__file__).resolve().parent.parent.parent / "static"
if _static_dir.is_dir():
    # Mounted after API routes are registered (see bottom of file)
    _serve_static = True
else:
    _serve_static = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory graph store keyed by thread_id.
# Production would use a persistent store.
_graphs: dict[str, Any] = {}


def _get_or_create_graph(thread_id: str, *, hitl: bool = False):
    if thread_id not in _graphs:
        _graphs[thread_id] = build_graph(human_in_the_loop=hitl)
    return _graphs[thread_id]


def _extract_response(graph, config: dict) -> dict:
    """Pull final_answer, plan, charts, sources from graph state."""
    state = graph.get_state(config)
    values = state.values
    plan = values.get("plan", [])
    final_answer = values.get("final_answer", "")
    agent_outputs = values.get("agent_outputs", {})

    charts: list[str] = []
    sources: list[dict] = []
    for name in plan:
        out = agent_outputs.get(name, {})
        charts.extend(out.get("charts", []))
        for s in out.get("sources", []):
            if s.get("url") and s not in sources:
                sources.append(s)

    return {
        "plan": plan,
        "final_answer": final_answer,
        "charts": charts,
        "sources": sources,
    }


# ── Health ────────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse()


# ── Query ─────────────────────────────────────────────────────────────────

@app.post("/api/query", response_model=QueryResponse)
def query(body: QueryRequest, hitl: bool = Query(False)):
    if not body.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")

    thread_id = body.thread_id or str(uuid.uuid4())
    graph = _get_or_create_graph(thread_id, hitl=hitl)
    config = {"configurable": {"thread_id": thread_id}}

    graph.invoke({"query": body.query}, config)

    state = graph.get_state(config)
    awaiting = bool(state.next)

    result = _extract_response(graph, config)

    return QueryResponse(
        thread_id=thread_id,
        plan=result["plan"],
        final_answer=result["final_answer"],
        charts=result["charts"],
        sources=[SourceItem(**s) for s in result["sources"]],
        awaiting_approval=awaiting,
    )


# ── Stream ────────────────────────────────────────────────────────────────

@app.post("/api/query/stream")
def query_stream(body: QueryRequest):
    if not body.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")

    thread_id = body.thread_id or str(uuid.uuid4())
    graph = _get_or_create_graph(thread_id)
    config = {"configurable": {"thread_id": thread_id}}

    def _generate():
        for chunk in graph.stream({"query": body.query}, config, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                event_data = {"node": node_name}
                yield f"event: node_end\ndata: {json.dumps(event_data)}\n\n"

        result = _extract_response(graph, config)
        yield f"event: done\ndata: {json.dumps(result)}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Approve (HITL) ───────────────────────────────────────────────────────

@app.post("/api/approve", response_model=QueryResponse)
def approve(body: ApproveRequest):
    thread_id = body.thread_id
    if thread_id not in _graphs:
        raise HTTPException(status_code=404, detail="thread not found")

    graph = _graphs[thread_id]
    config = {"configurable": {"thread_id": thread_id}}

    if body.plan:
        graph.update_state(config, {"plan": body.plan})

    graph.invoke(None, config)

    result = _extract_response(graph, config)

    return QueryResponse(
        thread_id=thread_id,
        plan=result["plan"],
        final_answer=result["final_answer"],
        charts=result["charts"],
        sources=[SourceItem(**s) for s in result["sources"]],
        awaiting_approval=False,
    )


# ── Upload CSV ────────────────────────────────────────────────────────────

_data_dir = Path(__file__).resolve().parent.parent.parent / "data"


@app.post("/api/upload")
async def upload_csv(file: UploadFile):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files allowed")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    dest = _data_dir / "user_upload.csv"
    dest.write_bytes(content)

    # Validate the CSV has required columns
    try:
        from src.tools.data_loader import load_dataframe
        df = load_dataframe(str(dest))
        rows = len(df)
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Invalid CSV: {e}")

    return {"filename": file.filename, "rows": rows, "path": str(dest)}


# ── Static files (React build — must be last) ────────────────────────────

if _serve_static:
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = _static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_static_dir / "index.html")
