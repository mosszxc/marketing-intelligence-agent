"""Analytics Agent — analyzes campaign data using LLM + tools."""

import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.state import AgentOutput
from src.tools.charts import create_chart
from src.tools.data_loader import compute_metrics, detect_anomalies, load_campaign_data

TOOLS = [load_campaign_data, compute_metrics, detect_anomalies, create_chart]

SYSTEM_PROMPT = """You are a marketing analytics agent. You analyze campaign performance data.

When asked a question:
1. First load the campaign data to understand what's available.
2. Compute the relevant metrics (roi, roas, cpa, ctr, conversion_rate, summary).
3. If the question involves trends or comparisons, create a chart.
4. If asked about problems or anomalies, run anomaly detection.

Always provide specific numbers. Format monetary values with commas.
Respond in Russian."""


def run_analytics(query: str) -> AgentOutput:
    """Run the analytics agent on a query. Requires OPENAI_API_KEY."""
    llm = ChatOpenAI(
        model=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
        temperature=0,
    )
    llm_with_tools = llm.bind_tools(TOOLS)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=query),
    ]

    charts: list[str] = []
    max_iterations = 8

    for _ in range(max_iterations):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            tool_fn = {t.name: t for t in TOOLS}[tc["name"]]
            result = tool_fn.invoke(tc["args"])

            if tc["name"] == "create_chart" and not result.startswith(("Unknown", "No positive", "Column")):
                charts.append(result)

            from langchain_core.messages import ToolMessage
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    summary = response.content if response.content else "Analysis complete."

    return AgentOutput(
        summary=summary,
        data={},
        charts=charts,
        sources=[],
        error=None,
    )


def run_analytics_no_llm(query: str) -> AgentOutput:
    """Fallback analytics without LLM — keyword-based routing for demos/tests."""
    query_lower = query.lower()

    data_summary = load_campaign_data.invoke({"path": ""})

    charts: list[str] = []

    if any(w in query_lower for w in ["roi", "рои", "окупаемость", "эффективность", "roas"]):
        metrics = compute_metrics.invoke({"metric": "roas", "group_by": ""})
        chart = create_chart.invoke({"chart_type": "bar", "metric": "roas"})
        charts.append(chart)
    elif any(w in query_lower for w in ["cpa", "стоимость", "цена", "расход", "spend"]):
        metrics = compute_metrics.invoke({"metric": "cpa", "group_by": ""})
        chart = create_chart.invoke({"chart_type": "bar", "metric": "spend"})
        charts.append(chart)
    elif any(w in query_lower for w in ["аномал", "проблем", "anomal", "бот", "мусор"]):
        metrics = detect_anomalies.invoke({"threshold": 2.0})
        chart = create_chart.invoke({"chart_type": "line", "metric": "spend"})
        charts.append(chart)
    elif any(w in query_lower for w in ["ctr", "клик", "click"]):
        metrics = compute_metrics.invoke({"metric": "ctr", "group_by": ""})
        chart = create_chart.invoke({"chart_type": "bar", "metric": "ctr"})
        charts.append(chart)
    elif any(w in query_lower for w in ["формат", "format", "video", "banner"]):
        metrics = compute_metrics.invoke({"metric": "summary", "group_by": "ad_format"})
        chart = create_chart.invoke({"chart_type": "bar", "metric": "spend", "group_by": "ad_format"})
        charts.append(chart)
    elif any(w in query_lower for w in ["устройств", "device", "mobile", "desktop"]):
        metrics = compute_metrics.invoke({"metric": "summary", "group_by": "device"})
        chart = create_chart.invoke({"chart_type": "pie", "metric": "conversions", "group_by": "device"})
        charts.append(chart)
    else:
        metrics = compute_metrics.invoke({"metric": "summary", "group_by": ""})
        chart = create_chart.invoke({"chart_type": "bar", "metric": "revenue"})
        charts.append(chart)

    summary = f"{data_summary}\n\n{metrics}"

    return AgentOutput(
        summary=summary,
        data={},
        charts=charts,
        sources=[],
        error=None,
    )
