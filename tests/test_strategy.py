"""Tests for Phase 11: Strategy Agent."""


from src.tools.data_loader import load_dataframe


class TestBudgetReallocation:
    def test_returns_reallocation_table(self):
        from src.agents.strategy import budget_reallocation
        df = load_dataframe()
        result = budget_reallocation(df)
        assert "текущий" in result.lower() or "рекомендуемый" in result.lower()
        assert "%" in result

    def test_recommends_scaling_high_roas(self):
        from src.agents.strategy import budget_reallocation
        df = load_dataframe()
        result = budget_reallocation(df)
        # retargeting_cart has ROAS 8.11 — should recommend increasing
        assert "retargeting_cart" in result or "увелич" in result.lower()

    def test_recommends_cutting_low_roas(self):
        from src.agents.strategy import budget_reallocation
        df = load_dataframe()
        result = budget_reallocation(df)
        # brand_awareness has ROAS 0 — should recommend cutting
        assert "brand_awareness" in result or "отключ" in result.lower() or "сократ" in result.lower()


class TestWhatIf:
    def test_what_if_returns_projection(self):
        from src.agents.strategy import what_if
        df = load_dataframe()
        result = what_if(df, "увеличить бюджет retargeting_cart +20%")
        assert "retargeting_cart" in result
        assert any(c.isdigit() for c in result)  # contains numbers

    def test_what_if_unknown_campaign(self):
        from src.agents.strategy import what_if
        df = load_dataframe()
        result = what_if(df, "увеличить бюджет nonexistent +50%")
        assert "не найден" in result.lower() or "not found" in result.lower()


class TestStrategyAgent:
    def test_run_strategy_returns_agent_output(self):
        from src.agents.strategy import run_strategy
        result = run_strategy("Куда перераспределить бюджет?")
        assert "summary" in result
        assert len(result["summary"]) > 0

    def test_strategy_output_has_recommendations(self):
        from src.agents.strategy import run_strategy
        result = run_strategy("Как оптимизировать бюджет?")
        summary = result["summary"]
        assert "рекомендуемый" in summary.lower() or "%" in summary


class TestSupervisorRouting:
    def test_routes_to_strategy(self):
        from src.agents.supervisor import classify_query
        plan = classify_query("Куда перераспределить бюджет?")
        assert "strategy" in plan

    def test_routes_what_if_to_strategy(self):
        from src.agents.supervisor import classify_query
        plan = classify_query("Что если увеличить бюджет на email на 20%?")
        assert "strategy" in plan

    def test_routes_optimization_to_strategy(self):
        from src.agents.supervisor import classify_query
        plan = classify_query("Как оптимизировать расходы на рекламу?")
        assert "strategy" in plan


class TestGraphIntegration:
    def test_strategy_node_in_graph(self):
        from src.graph import build_graph
        graph = build_graph()
        # Strategy should be a valid node
        config = {"configurable": {"thread_id": "test-strategy-1"}}
        result = graph.invoke({"query": "Куда перераспределить бюджет?"}, config)
        assert "strategy" in result.get("plan", [])
        assert len(result.get("final_answer", "")) > 0

    def test_strategy_report_has_reallocation(self):
        from src.graph import build_graph
        graph = build_graph()
        config = {"configurable": {"thread_id": "test-strategy-2"}}
        result = graph.invoke({"query": "Как оптимизировать бюджет?"}, config)
        answer = result.get("final_answer", "")
        assert "%" in answer or "бюджет" in answer.lower()

    def test_no_regression_analytics(self):
        from src.graph import build_graph
        graph = build_graph()
        config = {"configurable": {"thread_id": "test-regression-1"}}
        result = graph.invoke({"query": "ROI по каналам"}, config)
        assert "analytics" in result.get("plan", [])
        assert len(result.get("final_answer", "")) > 0
