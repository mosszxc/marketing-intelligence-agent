# Roadmap — Marketing Intelligence Agent

> Каждый этап = рабочий инкремент. Можно остановиться после любого и уже иметь демо.

---

## Phase 1: Скелет проекта

**Цель:** запускаемый пустой граф, все зависимости стоят, структура готова.

| # | Задача | DOD |
|---|--------|-----|
| 1.1 | pyproject.toml с зависимостями | `pip install -e .` проходит без ошибок |
| 1.2 | Структура папок (src/, tests/, data/) | Все файлы из SPEC.md существуют с `__init__.py` |
| 1.3 | .env.example | Перечислены все нужные ключи (OPENAI_API_KEY, TAVILY_API_KEY, ANTHROPIC_API_KEY) |
| 1.4 | State schema | `state.py` — TypedDict с полями query, messages, agent_outputs, final_answer |
| 1.5 | Пустой LangGraph граф | `graph.py` — граф компилируется, `graph.invoke({"query": "test"})` возвращает state без ошибок |
| 1.6 | Smoke test | `pytest tests/test_graph.py` — 1 тест проходит (граф запускается и возвращает state) |

**Результат:** `python -m src.graph` запускает граф, тест зелёный.

---

## Phase 2: Analytics Agent

**Цель:** агент принимает CSV, считает метрики, рисует графики.

| # | Задача | DOD |
|---|--------|-----|
| 2.1 | Синтетический датасет | `data/demo_campaigns.csv` — 6 каналов, 12 мес, столбцы: date, channel, impressions, clicks, conversions, spend, revenue. Минимум 2 встроенных аномалии |
| 2.2 | CSV loader tool | `tools/data_loader.py` — загружает CSV в pandas DataFrame, валидирует обязательные столбцы, возвращает ошибку при невалидном файле |
| 2.3 | Charts tool | `tools/charts.py` — принимает DataFrame + тип графика (line/bar/pie), возвращает base64 PNG. Минимум 3 типа графика |
| 2.4 | Analytics Agent | `agents/analytics.py` — LangChain agent с tools (data_loader, charts, python_repl). На запрос "покажи ROI по каналам" возвращает числа + график |
| 2.5 | Интеграция в граф | Analytics Agent подключён как нода в LangGraph. `graph.invoke({"query": "ROI по каналам"})` → state содержит agent_outputs.analytics с данными и графиком |
| 2.6 | Тесты | 3+ теста: загрузка CSV, расчёт метрик (ROI = (revenue - spend) / spend), генерация графика. Все зелёные |

**Результат:** запрос про данные кампаний → числа + график. Проверяемо вручную.

---

## Phase 3: Research Agent

**Цель:** агент ищет в вебе, возвращает структурированные данные с источниками.

| # | Задача | DOD |
|---|--------|-----|
| 3.1 | Tavily search tool | `tools/search.py` — обёртка над Tavily API. Принимает query, возвращает list[{title, url, content, score}]. Fallback при отсутствии ключа — mock-данные |
| 3.2 | Web scraper tool | `tools/scraper.py` — принимает URL, возвращает текст страницы (BeautifulSoup). Timeout 10s, обработка ошибок |
| 3.3 | Research Agent | `agents/research.py` — LangChain agent с tools (search, scraper). На запрос "что пишут про бренд X" возвращает summary + sources + sentiment |
| 3.4 | Интеграция в граф | Research Agent как нода. `graph.invoke({"query": "тренды в AI маркетинге"})` → state содержит agent_outputs.research |
| 3.5 | Тесты | 2+ теста: mock-поиск возвращает результаты, agent форматирует ответ с источниками. Зелёные |

**Результат:** запрос про рынок/конкурентов → структурированный ответ с ссылками.

---

## Phase 4: Supervisor + Routing

**Цель:** supervisor определяет, какие агенты нужны, оркестрирует выполнение, собирает ответ.

| # | Задача | DOD |
|---|--------|-----|
| 4.1 | Supervisor Agent | `agents/supervisor.py` — классифицирует запрос → выбирает агентов (analytics, research, или оба). Возвращает plan: list[str] |
| 4.2 | Router в графе | `graph.py` — conditional edges: supervisor → route по плану → агенты → synthesize. Параллельное выполнение если оба агента нужны |
| 4.3 | Report Agent | `agents/report.py` — собирает agent_outputs, форматирует единый Markdown-ответ с секциями, графиками, источниками |
| 4.4 | End-to-end тест | Запрос "как изменился ROI и что делают конкуренты" → supervisor вызывает оба агента → report собирает ответ. Ответ содержит числа + ссылки |
| 4.5 | Тесты | 3+ теста: routing на analytics-only, research-only, both. Все зелёные |

**Результат:** любой маркетинговый запрос → система сама решает куда идти → собранный ответ.

---

## Phase 5: Evaluation Pipeline

**Цель:** каждый ответ системы автоматически оценивается по качеству.

| # | Задача | DOD |
|---|--------|-----|
| 5.1 | LLM-as-judge | `evaluation/evaluator.py` — принимает (query, response), возвращает scores: {relevance: float, completeness: float, accuracy: float}. Каждый 0.0-1.0 |
| 5.2 | Ground truth dataset | `data/eval_questions.json` — 10+ пар (query, expected_answer) для analytics-запросов. Expected = конкретные числа из demo_campaigns.csv |
| 5.3 | Eval runner | `evaluation/evaluator.py` — batch_evaluate() прогоняет все вопросы, считает средние метрики, сохраняет в `data/eval_results.json` |
| 5.4 | Интеграция в граф | Evaluation как финальная нода (опционально, включается флагом). Score записывается в state.evaluation |
| 5.5 | Baseline метрики | Прогнать eval, зафиксировать baseline: relevance >= 0.7, accuracy >= 0.8 на ground truth. Числа записаны в README |

**Результат:** `python -m src.evaluation.evaluator` → отчёт с метриками. Есть baseline для улучшений.

---

## Phase 6: Streamlit UI

**Цель:** человек может пользоваться системой через браузер.

| # | Задача | DOD |
|---|--------|-----|
| 6.1 | Чат-интерфейс | `ui/app.py` — Streamlit chat. Ввод запроса → ответ в чате. История сохраняется в session_state |
| 6.2 | Отображение графиков | Графики из analytics agent рендерятся inline в чате (st.image из base64) |
| 6.3 | Отображение источников | Ссылки из research agent — кликабельные, с title |
| 6.4 | Загрузка CSV | Sidebar: upload CSV → заменяет демо-датасет → analytics agent работает с новыми данными |
| 6.5 | Индикация работы | Spinner во время работы агентов. Показать, какой агент сейчас работает (supervisor → analytics → ...) |
| 6.6 | Smoke test | Запустить `streamlit run src/ui/app.py`, задать 3 разных запроса, все отрабатывают без ошибок. Скриншот в README |

**Результат:** `streamlit run src/ui/app.py` → рабочий чат с графиками и источниками.

---

## Phase 7: Production LangGraph Features

**Цель:** апгрейд от tutorial-level до production-grade LangGraph. Именно эти фичи отличают junior от senior в вакансиях.

### 7.1 Checkpointing + Memory

| # | Задача | DOD |
|---|--------|-----|
| 7.1.1 | MemorySaver в графе | `build_graph()` принимает `checkpointer` параметр. По умолчанию `MemorySaver()` |
| 7.1.2 | Thread ID support | `graph.invoke({"query": "..."}, {"configurable": {"thread_id": "abc"}})` — state привязан к thread |
| 7.1.3 | Продолжение диалога | Второй invoke с тем же thread_id видит результаты первого. Тест: query1 → query2, state содержит оба agent_outputs |
| 7.1.4 | Streamlit интеграция | UI использует session-based thread_id. Новая сессия = новый thread. Кнопка "Новый диалог" сбрасывает thread |
| 7.1.5 | Тесты | 3+ теста: thread isolation (разные thread_id не пересекаются), state persistence (два invoke, state сохраняется), new thread reset |

**Результат:** пользователь задаёт "ROI по каналам", потом "а покажи по месяцам" — система помнит контекст.

### 7.2 Human-in-the-loop

| # | Задача | DOD |
|---|--------|-----|
| 7.2.1 | interrupt_before на dispatcher | После supervisor классифицировал запрос — граф останавливается. State содержит plan, но агенты ещё не запущены |
| 7.2.2 | Resume с подтверждением | `graph.invoke(None, config)` продолжает выполнение. Или `graph.invoke(Command(resume=modified_plan), config)` с изменённым планом |
| 7.2.3 | Streamlit HITL UI | После supervisor: показать план ("Буду использовать: analytics, research"). Кнопки: "Подтвердить" / "Только analytics" / "Только research". По клику — resume |
| 7.2.4 | Тесты | 3+ теста: interrupt возвращает state с plan но без agent_outputs, resume выполняет агентов, modified resume меняет plan |

**Результат:** пользователь видит план до выполнения и может его скорректировать.

### 7.3 Streaming

| # | Задача | DOD |
|---|--------|-----|
| 7.3.1 | stream_mode в графе | `graph.stream(input, config, stream_mode="updates")` — yields события по нодам |
| 7.3.2 | Streamlit streaming UI | Прогресс-бар / status updates: "Supervisor: классификация..." → "Analytics: анализ данных..." → "Synthesize: сборка отчёта..." |
| 7.3.3 | Тесты | 2+ теста: stream yields правильные node names в правильном порядке, все ноды из plan присутствуют в stream |

**Результат:** пользователь видит живой прогресс, а не спиннер.

### 7.4 Error Recovery

| # | Задача | DOD |
|---|--------|-----|
| 7.4.1 | Error handling в agent нодах | Каждая agent-нода ловит exceptions, записывает в `AgentOutput.error`. Граф НЕ падает |
| 7.4.2 | Partial results в synthesize | Если analytics упал но research отработал — отчёт содержит research + сообщение об ошибке analytics |
| 7.4.3 | Тесты | 3+ теста: agent с ошибкой не крашит граф, partial results содержат доступные данные, error message в отчёте |

**Результат:** граф resilient — одна сломанная нода не убивает весь pipeline.

---

## Phase 8: README + Polish

**Цель:** проект готов для портфолио и GitHub.

| # | Задача | DOD |
|---|--------|-----|
| 8.1 | README.md | Секции: What (1 абзац), Architecture (диаграмма), Quick Start (3 команды до работающего демо), Screenshots (2-3), Evaluation Results, Tech Stack |
| 8.2 | Архитектурная диаграмма | Mermaid или PNG. Показывает граф, агентов, tools, data flow |
| 8.3 | Docker | `Dockerfile` + `docker-compose.yml`. `docker compose up` → UI на localhost:8501 |
| 8.4 | CI | GitHub Actions: lint (ruff) + tests на каждый push |
| 8.5 | Скриншоты | 3 скриншота UI: analytics-запрос, research-запрос, mixed-запрос. В README |
| 8.6 | Impact-формулировки | README содержит метрики: "Reduces manual analysis from 2h to 30s", "85%+ relevance on eval suite" |

**Результат:** клонируешь repo → 3 команды → работающее демо. README продаёт проект за 30 секунд.

---

## Опционально (post-MVP)

| Phase | Что | Когда |
|-------|-----|-------|
| 9 | Strategy Agent — рекомендации по бюджету | После найма / фриланс-заказа |
| 10 | MCP сервер — подключение как tool к Claude/Cursor | Когда нужен MCP в портфолио |
| 11 | RAG по документам компании — загрузка PDF/стратегий | Для фриланс-кейса |
| 12 | React UI + FastAPI backend | Для production-версии |
| 13 | Google Ads / Meta Ads API интеграция | Для реального клиента |

---

## Timeline (оценка)

| Phase | Объём |
|-------|-------|
| 1. Скелет | 1 сессия |
| 2. Analytics Agent | 1-2 сессии |
| 3. Research Agent | 1 сессия |
| 4. Supervisor + Routing | 1 сессия |
| 5. Evaluation | 1 сессия |
| 6. Streamlit UI | 1 сессия |
| 7. README + Polish | 1 сессия |
| **Итого MVP** | **7-8 сессий** |

> 1 сессия = один рабочий заход с Claude Code.
