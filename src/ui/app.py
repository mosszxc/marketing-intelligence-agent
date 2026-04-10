"""Streamlit UI for the Marketing Intelligence Agent.

Design system: Data-Dense Dashboard (ui-ux-pro-max)
Colors: Primary #1E40AF, Secondary #3B82F6, CTA #F59E0B, BG #F8FAFC, Text #1E3A8A
Typography: Fira Code (data/headings) / Inter (body)
"""

import base64
import uuid

import streamlit as st

from src.graph import build_graph

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Marketing Intelligence Agent",
    page_icon="https://api.iconify.design/lucide/bar-chart-3.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design system CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

/* ===== ROOT TOKENS ===== */
:root {
    --primary: #1E40AF;
    --primary-light: #3B82F6;
    --primary-lighter: #DBEAFE;
    --cta: #F59E0B;
    --cta-light: #FEF3C7;
    --bg: #F8FAFC;
    --bg-dark: #0F172A;
    --bg-dark-2: #1E293B;
    --surface: #FFFFFF;
    --text: #0F172A;
    --text-secondary: #475569;
    --text-muted: #94A3B8;
    --border: #E2E8F0;
    --border-light: #F1F5F9;
    --success: #10B981;
    --error: #EF4444;
    --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
}

/* ===== GLOBAL ===== */
html, body, [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text) !important;
}
h1, h2, h3, h4, h5, h6, [data-testid="stHeading"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    letter-spacing: -0.025em;
}

/* ===== HIDE STREAMLIT CHROME ===== */
header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, header .stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* Hide sidebar collapse button text */
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
button[kind="header"] { display: none !important; }

/* Hide heading anchor links (the chain icon) */
[data-testid="stHeading"] a { display: none !important; }
.stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a { display: none !important; }

/* ===== AVATAR ICONS ===== */
/* Styled by JS below — hide Material Icon font rendering */
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"] {
    width: 30px !important;
    height: 30px !important;
    min-width: 30px !important;
    min-height: 30px !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    -webkit-font-feature-settings: normal !important;
    font-feature-settings: normal !important;
}
[data-testid="chatAvatarIcon-user"] {
    background: var(--primary-lighter) !important;
    color: var(--primary) !important;
    font-size: 12px !important;
}
[data-testid="chatAvatarIcon-assistant"] {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%) !important;
    color: white !important;
    font-size: 10px !important;
}

/* Hide sidebar collapse arrow */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

/* ===== MAIN CONTAINER ===== */
[data-testid="stMain"] > div { padding-top: 0.5rem !important; }
.block-container { max-width: 860px !important; padding: 0.75rem 2rem 4rem !important; }

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--bg-dark) 0%, var(--bg-dark-2) 100%) !important;
    border-right: 1px solid #1E293B !important;
    width: 260px !important;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] h1 {
    color: #F8FAFC !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.15rem !important;
}
[data-testid="stSidebar"] h3 {
    color: #64748B !important;
    font-size: 0.6rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 600 !important;
    margin-top: 0.4rem !important;
    margin-bottom: 0.35rem !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.06) !important;
    margin: 0.5rem 0 !important;
}
[data-testid="stSidebar"] p {
    font-size: 0.78rem !important;
    line-height: 1.4 !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #E2E8F0 !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 0.4rem 0.6rem !important;
    transition: all 150ms ease !important;
    cursor: pointer !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(59, 130, 246, 0.12) !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
    color: #F8FAFC !important;
}

/* Sidebar captions */
[data-testid="stSidebar"] [data-testid="stCaption"] {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.6rem !important;
    color: #475569 !important;
}

/* ===== MAIN TITLE ===== */
.block-container h1:first-of-type {
    font-size: 1.25rem !important;
    color: var(--text) !important;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--border) !important;
    margin-bottom: 1rem !important;
}

/* ===== CHAT MESSAGES ===== */
[data-testid="stChatMessage"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-xs) !important;
    padding: 0.75rem 1rem !important;
    margin-bottom: 0.5rem !important;
    background: var(--surface) !important;
}
[data-testid="stChatMessage"]:hover {
    border-color: var(--primary-lighter) !important;
}

/* User messages — subtle blue tint */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%) !important;
    border-color: var(--primary-lighter) !important;
}

/* ===== CHAT INPUT ===== */
[data-testid="stChatInput"] {
    border-top: 1px solid var(--border) !important;
    padding-top: 0.5rem !important;
    background: var(--bg) !important;
}
[data-testid="stChatInput"] textarea {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    border-radius: var(--radius-lg) !important;
    border: 1.5px solid var(--border) !important;
    padding: 0.75rem 1rem !important;
    background: var(--surface) !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--primary-light) !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

/* ===== HITL ALERT ===== */
[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--primary-lighter) !important;
    border-left: 4px solid var(--primary) !important;
    background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%) !important;
    padding: 0.85rem 1.15rem !important;
    font-size: 0.88rem !important;
}

/* ===== BUTTONS ===== */
/* Default (secondary) */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    padding: 0.5rem 1rem !important;
    transition: all 150ms ease !important;
    cursor: pointer !important;
    border: 1.5px solid var(--border) !important;
    background: var(--surface) !important;
    color: var(--text-secondary) !important;
}
.stButton > button:hover {
    border-color: var(--primary-light) !important;
    color: var(--primary) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Primary button — Approve action */
[data-testid="stBaseButton-primary"] {
    background: var(--primary) !important;
    color: white !important;
    border-color: var(--primary) !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stBaseButton-primary"]:hover {
    background: #1D4ED8 !important;
    border-color: #1D4ED8 !important;
    color: white !important;
    box-shadow: var(--shadow-md) !important;
}

/* ===== STATUS/STREAMING ===== */
[data-testid="stStatusWidget"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
    font-size: 0.82rem !important;
}
[data-testid="stStatusWidget"] p {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.78rem !important;
    color: var(--text-secondary) !important;
}

/* ===== CAPTIONS ===== */
[data-testid="stCaption"] {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.65rem !important;
    color: var(--text-muted) !important;
}

/* ===== IMAGES/CHARTS ===== */
[data-testid="stImage"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    overflow: hidden;
    margin: 0.5rem 0 !important;
}
/* Hide fullscreen button on images */
[data-testid="stImage"] button { display: none !important; }

/* ===== MARKDOWN (reports) ===== */
/* Report title — smaller, inline */
[data-testid="stChatMessage"] .stMarkdown h1 {
    font-size: 1rem !important;
    margin-bottom: 0.5rem !important;
    padding-bottom: 0 !important;
    border-bottom: none !important;
}

/* Section headings */
.stMarkdown h2 {
    font-size: 0.9rem !important;
    color: var(--primary) !important;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
    padding-bottom: 0.25rem;
    border-bottom: 1px solid var(--border-light);
}

/* Body text */
.stMarkdown p {
    font-size: 0.85rem !important;
    line-height: 1.6 !important;
    color: var(--text-secondary) !important;
}
.stMarkdown strong { color: var(--text) !important; }

/* Lists in reports */
.stMarkdown ul, .stMarkdown ol {
    font-size: 0.85rem !important;
    color: var(--text-secondary) !important;
    margin-top: 0.25rem !important;
    margin-bottom: 0.5rem !important;
}
.stMarkdown li {
    margin-bottom: 0.3rem !important;
    line-height: 1.5 !important;
}
.stMarkdown li strong { color: var(--text) !important; }

/* Code blocks */
.stMarkdown code {
    font-family: 'Fira Code', monospace !important;
    background: var(--border-light) !important;
    color: var(--primary) !important;
    padding: 2px 5px !important;
    border-radius: 3px !important;
    font-size: 0.8rem !important;
}

/* Tables */
.stMarkdown table { font-size: 0.8rem !important; width: 100% !important; }
.stMarkdown th {
    background: var(--bg) !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    padding: 6px 10px !important;
    border-bottom: 2px solid var(--border) !important;
    text-align: left !important;
}
.stMarkdown td {
    padding: 5px 10px !important;
    border-bottom: 1px solid var(--border-light) !important;
    color: var(--text-secondary) !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* ===== REDUCED MOTION ===== */
@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "graph" not in st.session_state:
    st.session_state.graph = build_graph(human_in_the_loop=True)
if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False
if "pending_plan" not in st.session_state:
    st.session_state.pending_plan = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AGENT_LABELS = {
    "supervisor": "Supervisor  classifying",
    "analytics": "Analytics  processing",
    "research": "Research  searching",
    "synthesize": "Report  building",
}


def _get_config():
    return {"configurable": {"thread_id": st.session_state.thread_id}}


def _new_thread():
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.awaiting_approval = False
    st.session_state.pending_plan = None
    st.session_state.graph = build_graph(human_in_the_loop=True)


def _run_graph_streaming(query: str | None):
    config = _get_config()
    inp = {"query": query} if query else None
    node_names = []
    result = {}

    with st.status("Processing...", expanded=True) as status:
        for chunk in st.session_state.graph.stream(inp, config, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                node_names.append(node_name)
                result.update(node_output)
                label = AGENT_LABELS.get(node_name, node_name)
                st.write(f"`{label}` done")

        status.update(label=f"Done — {', '.join(node_names)}", state="complete")

    return result, node_names


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("Marketing Intelligence")
    st.caption("Multi-agent analytics  ·  LangGraph")
    st.divider()

    if st.button("New conversation", use_container_width=True, type="primary"):
        _new_thread()
        st.rerun()

    st.markdown("### Queries")
    examples = [
        "ROI by channel",
        "Anomalies in spend?",
        "AI marketing trends 2026",
        "Compare ROI with benchmarks",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state.pending_query = ex

    st.divider()
    st.markdown("### Agents")
    st.markdown(
        "**Supervisor** — classify & route\n\n"
        "**Analytics** — data, metrics, charts\n\n"
        "**Research** — web, trends\n\n"
        "**Report** — synthesis"
    )
    st.divider()
    st.caption(f"thread {st.session_state.thread_id[:8]}")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("Marketing Intelligence Agent")

# Welcome state when no messages
if not st.session_state.messages and not st.session_state.awaiting_approval:
    st.markdown("""
<div style="
    text-align: center;
    padding: 2.5rem 1.5rem 1.5rem;
    color: #94A3B8;
">
    <div style="margin-bottom: 0.75rem;">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="opacity: 0.4;">
            <line x1="18" y1="20" x2="18" y2="10"></line>
            <line x1="12" y1="20" x2="12" y2="4"></line>
            <line x1="6" y1="20" x2="6" y2="14"></line>
        </svg>
    </div>
    <p style="font-size: 0.95rem; font-weight: 500; color: #64748B; margin: 0 0 0.35rem;">
        Ask about your marketing data
    </p>
    <p style="font-size: 0.8rem; color: #94A3B8; max-width: 380px; margin: 0 auto; line-height: 1.5;">
        Queries are routed to analytics, research, or both.
        You approve the plan before execution.
    </p>
</div>
""", unsafe_allow_html=True)

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for chart_b64 in msg.get("charts", []):
            try:
                st.image(base64.b64decode(chart_b64), use_container_width=True)
            except Exception:
                pass
        if msg.get("plan"):
            st.caption(f"agents: {', '.join(msg['plan'])}")

# ---------------------------------------------------------------------------
# HITL: approval
# ---------------------------------------------------------------------------
if st.session_state.awaiting_approval and st.session_state.pending_plan:
    plan = st.session_state.pending_plan

    st.info(f"Supervisor proposed plan: **{', '.join(plan)}**")

    col1, col2, col3 = st.columns(3)
    approve = col1.button("Approve", use_container_width=True, type="primary")
    only_analytics = col2.button("Analytics only", use_container_width=True) if "analytics" in plan else False
    only_research = col3.button("Research only", use_container_width=True) if "research" in plan else False

    if approve or only_analytics or only_research:
        if only_analytics:
            st.session_state.graph.update_state(_get_config(), {"plan": ["analytics"]})
            chosen = ["analytics"]
        elif only_research:
            st.session_state.graph.update_state(_get_config(), {"plan": ["research"]})
            chosen = ["research"]
        else:
            chosen = plan

        st.session_state.awaiting_approval = False
        st.session_state.pending_plan = None

        with st.chat_message("assistant"):
            result, node_names = _run_graph_streaming(None)
            state = st.session_state.graph.get_state(_get_config())
            final_answer = state.values.get("final_answer", "No answer.")
            agent_outputs = state.values.get("agent_outputs", {})

            st.markdown(final_answer)
            charts = []
            for name in chosen:
                output = agent_outputs.get(name, {})
                for chart_b64 in output.get("charts", []):
                    charts.append(chart_b64)
                    try:
                        st.image(base64.b64decode(chart_b64), use_container_width=True)
                    except Exception:
                        pass
            st.caption(f"agents: {', '.join(chosen)}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": final_answer,
            "charts": charts,
            "plan": chosen,
        })

# ---------------------------------------------------------------------------
# Query input
# ---------------------------------------------------------------------------
query = st.chat_input("Ask about your marketing data...")

if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

if query and not st.session_state.awaiting_approval:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        result, node_names = _run_graph_streaming(query)
        state = st.session_state.graph.get_state(_get_config())
        next_nodes = state.next

        if next_nodes:
            plan = state.values.get("plan", [])
            st.session_state.awaiting_approval = True
            st.session_state.pending_plan = plan
            st.info(f"Plan: **{', '.join(plan)}** — approve above.")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Plan: {', '.join(plan)} — awaiting approval.",
                "plan": plan,
                "charts": [],
            })
            st.rerun()
        else:
            final_answer = state.values.get("final_answer", result.get("final_answer", "No answer."))
            agent_outputs = state.values.get("agent_outputs", {})
            plan = state.values.get("plan", [])

            st.markdown(final_answer)
            charts = []
            for name in plan:
                output = agent_outputs.get(name, {})
                for chart_b64 in output.get("charts", []):
                    charts.append(chart_b64)
                    try:
                        st.image(base64.b64decode(chart_b64), use_container_width=True)
                    except Exception:
                        pass
            st.caption(f"agents: {', '.join(plan)}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": final_answer,
                "charts": charts,
                "plan": plan,
            })
