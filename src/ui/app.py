"""Streamlit UI for the Marketing Intelligence Agent."""

import base64
import uuid

import streamlit as st

from src.graph import build_graph

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Marketing Intelligence Agent",
    page_icon="📊",
    layout="wide",
)

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
    "supervisor": "Supervisor: классификация запроса",
    "analytics": "Analytics: анализ данных",
    "research": "Research: поиск информации",
    "synthesize": "Report: сборка отчёта",
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
    """Run graph with streaming, showing node progress in real-time."""
    config = _get_config()
    inp = {"query": query} if query else None

    node_names = []
    result = {}

    with st.status("Обработка запроса...", expanded=True) as status:
        for chunk in st.session_state.graph.stream(inp, config, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                node_names.append(node_name)
                result.update(node_output)
                label = AGENT_LABELS.get(node_name, node_name)
                st.write(f"**{label}** ... done")

        status.update(
            label=f"Готово — агенты: {', '.join(node_names)}",
            state="complete",
        )

    return result, node_names


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("Marketing Intelligence")
    st.markdown("Multi-agent система анализа маркетинговых данных")
    st.divider()

    if st.button("Новый диалог", use_container_width=True):
        _new_thread()
        st.rerun()

    st.markdown("### Примеры запросов")
    examples = [
        "Покажи ROI по каналам",
        "Какие аномалии в расходах?",
        "Тренды AI маркетинга 2026",
        "Сравни ROI с рыночными бенчмарками",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state.pending_query = ex

    st.divider()
    st.markdown("### Агенты")
    st.markdown(
        "- **Supervisor** — классификация и роутинг\n"
        "- **Analytics** — CSV-метрики, графики\n"
        "- **Research** — веб-поиск, тренды\n"
        "- **Report** — финальный отчёт"
    )
    st.divider()
    st.caption(f"Thread: `{st.session_state.thread_id[:8]}...`")

# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------
st.title("Marketing Intelligence Agent")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for chart_b64 in msg.get("charts", []):
            try:
                st.image(base64.b64decode(chart_b64), use_container_width=True)
            except Exception:
                pass
        if msg.get("plan"):
            st.caption(f"Агенты: {', '.join(msg['plan'])}")

# ---------------------------------------------------------------------------
# HITL: approval buttons
# ---------------------------------------------------------------------------
if st.session_state.awaiting_approval and st.session_state.pending_plan:
    plan = st.session_state.pending_plan

    st.info(f"Supervisor предлагает план: **{', '.join(plan)}**")

    col1, col2, col3 = st.columns(3)
    approve = col1.button("Подтвердить", use_container_width=True)
    only_analytics = col2.button("Только Analytics", use_container_width=True) if "analytics" in plan else False
    only_research = col3.button("Только Research", use_container_width=True) if "research" in plan else False

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
            final_answer = state.values.get("final_answer", "Нет ответа.")
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

            st.caption(f"Агенты: {', '.join(chosen)}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": final_answer,
            "charts": charts,
            "plan": chosen,
        })

# ---------------------------------------------------------------------------
# Query input
# ---------------------------------------------------------------------------
query = st.chat_input("Задайте вопрос о маркетинговых данных...")

if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

if query and not st.session_state.awaiting_approval:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        # Stream through supervisor — will interrupt for HITL
        result, node_names = _run_graph_streaming(query)

        # Check if we're at an interrupt (HITL)
        state = st.session_state.graph.get_state(_get_config())
        next_nodes = state.next

        if next_nodes:
            # Interrupted — supervisor set the plan, waiting for approval
            plan = state.values.get("plan", [])
            st.session_state.awaiting_approval = True
            st.session_state.pending_plan = plan
            st.info(f"План: **{', '.join(plan)}** — подтвердите выше.")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"План: {', '.join(plan)} — ожидаю подтверждения.",
                "plan": plan,
                "charts": [],
            })
            st.rerun()
        else:
            # No interrupt — ran to completion (shouldn't happen with HITL but fallback)
            final_answer = state.values.get("final_answer", result.get("final_answer", "Нет ответа."))
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

            st.caption(f"Агенты: {', '.join(plan)}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": final_answer,
                "charts": charts,
                "plan": plan,
            })
