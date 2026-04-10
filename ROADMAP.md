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

## Phase 9: Intelligent Report Layer

**Цель:** система отвечает как аналитик, а не как data pipe. Интерпретация, приоритизация, рекомендации — без LLM.

### 9.1 Убрать debug-вывод из ответа

| # | Задача | DOD |
|---|--------|-----|
| 9.1.1 | Analytics summary без meta-info | `run_analytics_no_llm()` не включает в summary строки "Loaded N rows", "Columns:", "Date range:". Эта информация — internal context для агента, не для пользователя |
| 9.1.2 | Report agent фильтрует debug | `format_report()` не пропускает строки с debug-паттернами в финальный ответ |
| 9.1.3 | Тест | Ответ на любой запрос НЕ содержит "Loaded", "Columns:", "Date range:" |

**DOD:** ни один ответ системы не содержит debug-информацию. Каждый ответ начинается с сути.

### 9.2 Интерпретация данных

| # | Задача | DOD |
|---|--------|-----|
| 9.2.1 | Interpret layer в analytics | Новая функция `interpret_metrics()` — принимает сырую таблицу метрик, возвращает текст: лучшая/худшая кампания, доля бюджета в убыток, ключевые числа |
| 9.2.2 | Ответ на вопрос | На "Где мы сливаем бюджет?" ответ называет конкретные кампании с ROAS < 1, суммы потерь, процент бюджета |
| 9.2.3 | На "Какая кампания лучшая?" | Ответ называет кампанию, её ROAS/CPA, и почему она лучшая (сравнение с остальными) |
| 9.2.4 | Тест | Ответ содержит имена кампаний + числа в контексте ("ROAS 8.11", "474K RUB"), а не только raw таблицу |

**DOD:** ответ читается как абзац аналитика, а не как pandas `.to_string()`.

### 9.3 Приоритизация аномалий

| # | Задача | DOD |
|---|--------|-----|
| 9.3.1 | Группировка аномалий | `detect_anomalies()` группирует результаты по кампании, а не показывает 1365 отдельных строк |
| 9.3.2 | Классификация типа | Каждая группа аномалий получает тип: бот-трафик (высокий CTR + 0 конверсий), CPC spike (CPC > 3x от среднего), мусорная площадка (CTR < 0.05% + 0 конверсий), промо-эффект (конверсии > 2x) |
| 9.3.3 | Топ-N | Показывает 3-5 критичных проблем, отсортированных по impact (потраченный бюджет × отклонение) |
| 9.3.4 | Тест | Ответ на "Найди аномалии" содержит ≤5 пунктов с типом и impact, а не 20 строк z-score |

**DOD:** маркетолог читает "3 критические проблемы" с понятными названиями, а не z-score таблицу.

### 9.4 Рекомендации

| # | Задача | DOD |
|---|--------|-----|
| 9.4.1 | Recommendations engine | Новая функция `generate_recommendations()` — на основе метрик и аномалий генерирует список действий. Правила: ROAS < 0.5 → "отключить", ROAS 0.5-1.0 → "оптимизировать таргетинг", бот-трафик → "проверить площадки, добавить минус-список", CPC spike → "проверить ставки и конкурентов" |
| 9.4.2 | Секция в отчёте | Каждый analytics-ответ содержит секцию "Рекомендации" с 2-5 конкретными действиями |
| 9.4.3 | Тест | Ответ содержит секцию с рекомендациями, каждая рекомендация привязана к конкретной кампании |

**DOD:** маркетолог получает action items, а не просто данные.

### 9.5 Интеграционные тесты

| # | Задача | DOD |
|---|--------|-----|
| 9.5.1 | E2E: "Где мы сливаем бюджет?" | Ответ называет brand_awareness и geo_moscow, указывает суммы, даёт рекомендации |
| 9.5.2 | E2E: "Найди аномалии" | Ответ содержит ≤5 приоритизированных проблем с типами |
| 9.5.3 | E2E: "Какая кампания лучшая?" | Ответ называет retargeting_cart, объясняет почему |
| 9.5.4 | Регрессия | Все 81 существующих тест остаются зелёными |

**DOD:** все новые тесты зелёные + 0 регрессий.

**Результат:** система отвечает как маркетинговый аналитик — с выводами, приоритетами и рекомендациями.

---

## Phase 10: UX/UI Audit & Polish

**Цель:** UI выглядит и работает как продукт, а не как Streamlit-демо. Аудит глазами UX-специалиста → фиксы по ui-ux-pro-max design system → визуальная верификация через Playwright.

### 10.1 UX-аудит текущего состояния

| # | Задача | DOD |
|---|--------|-----|
| 10.1.1 | Playwright-замер: empty state | Скриншот начального экрана. Оценка: hierarchy, whitespace, CTA clarity, sidebar usability |
| 10.1.2 | Playwright-замер: HITL flow | Скриншот после клика на пример → HITL approval. Оценка: button prominence, info density, scan path |
| 10.1.3 | Playwright-замер: result state | Скриншот полного ответа с графиком и рекомендациями. Оценка: readability, chart integration, recommendations visibility |
| 10.1.4 | Scorecard | Письменная оценка по 8 критериям (hierarchy, typography, spacing, color, interaction, responsiveness, information density, accessibility). Каждый 1-10 |

**DOD:** документированный аудит с конкретными проблемами и скриншотами before-состояния.

### 10.2 Фиксы по ui-ux-pro-max design system

| # | Задача | DOD |
|---|--------|-----|
| 10.2.1 | Запрос к design system | `search.py` — получить рекомендации по palette, typography, spacing, components для data-dense dashboard |
| 10.2.2 | CSS overhaul | Переписать inline CSS в app.py по рекомендациям скилла. Фокус: visual hierarchy (h1 > h2 > body > caption), spacing rhythm, button states, card elevation |
| 10.2.3 | Welcome state redesign | Empty state должен направлять пользователя к действию: prominent input, example queries как chips/cards, не список кнопок |
| 10.2.4 | HITL redesign | Approval flow: primary action (Approve) визуально выделен, secondary actions (only analytics / only research) менее prominent |
| 10.2.5 | Result layout | Ответ с рекомендациями: секции визуально разделены, графики не ломают flow, рекомендации в callout-блоке |
| 10.2.6 | Sidebar cleanup | Sidebar: компактнее, section headers subtle, agents list как status indicators |

**DOD:** CSS обновлён, все элементы соответствуют design system tokens.

### 10.3 Playwright-верификация после фиксов

| # | Задача | DOD |
|---|--------|-----|
| 10.3.1 | Скриншот: empty state after | Визуально сравнить с before. Welcome state направляет к действию |
| 10.3.2 | Скриншот: HITL after | Approve кнопка — primary, план читаем |
| 10.3.3 | Скриншот: result after | Ответ читаем, рекомендации выделены, график вписан |
| 10.3.4 | Full-page screenshot | Полный скролл для README |

**DOD:** скриншоты after визуально лучше before по каждому критерию аудита.

### 10.4 README + push

| # | Задача | DOD |
|---|--------|-----|
| 10.4.1 | Обновить screenshots в README | Заменить старые скриншоты на новые after-версии |
| 10.4.2 | Git commit + push | Один коммит со всеми изменениями Phase 10 |
| 10.4.3 | Регрессия | Все 98 тестов зелёные |

**DOD:** README на GitHub показывает актуальный UI. 0 регрессий.

**Результат:** UI выглядит как SaaS-продукт, а не как tutorial Streamlit app.

---

## Phase 11: Strategy Agent

**Цель:** агент даёт рекомендации по бюджету, прогнозирует метрики и моделирует what-if сценарии на основе данных Analytics и Research агентов.

| # | Задача | DOD |
|---|--------|-----|
| 11.1 | Strategy Agent базовый | `agents/strategy.py` — принимает `agent_outputs` (analytics + research), возвращает `AgentOutput` с рекомендациями. Без LLM — rule-based |
| 11.2 | Budget reallocation | На вход: метрики по каналам. На выход: рекомендация перераспределения бюджета с обоснованием (ROAS-based). Формат: таблица "канал → текущий % → рекомендуемый % → причина" |
| 11.3 | What-if моделирование | Функция `what_if(scenario)` — принимает параметр ("увеличить бюджет email +20%"), возвращает прогноз метрик на основе линейной экстраполяции текущих данных |
| 11.4 | Интеграция в граф | Strategy Agent как нода в LangGraph. Supervisor может роутить на `strategy`. `classify_query()` распознаёт запросы типа "что если...", "куда перераспределить" |
| 11.5 | Тесты | 4+ теста: budget reallocation на demo_campaigns.csv возвращает таблицу, what-if возвращает прогноз, supervisor роутит "куда перераспределить бюджет" → strategy, все существующие тесты зелёные |

**Результат:** "Куда перераспределить бюджет?" → конкретная таблица перераспределения с обоснованием + прогноз.

---

## Phase 12: MCP Server

**Цель:** система доступна как MCP tool для Claude/Cursor — можно вызывать маркетинговый анализ прямо из IDE или Claude Desktop.

| # | Задача | DOD |
|---|--------|-----|
| 12.1 | MCP server scaffold | `src/mcp_server.py` — MCP server с `@tool` декоратором. Запуск: `python -m src.mcp_server`. Сервер стартует без ошибок |
| 12.2 | Tool: analyze_marketing | MCP tool `analyze_marketing(query: str) -> str` — вызывает `build_graph().invoke()`, возвращает `final_answer`. Работает с demo-данными |
| 12.3 | Tool: get_campaign_metrics | MCP tool `get_campaign_metrics(channel?: str) -> str` — возвращает метрики по каналу или все каналы. JSON output |
| 12.4 | Tool: detect_anomalies | MCP tool `detect_anomalies() -> str` — возвращает приоритизированные аномалии из analytics agent |
| 12.5 | Claude Desktop конфиг | `mcp-config.json` — пример конфигурации для Claude Desktop. Документация в README: как подключить |
| 12.6 | Тесты | 3+ теста: каждый tool возвращает валидный ответ, server стартует без ошибок, tool `analyze_marketing` возвращает строку с секцией "Аналитика" |

**Результат:** `claude mcp add marketing-agent` → маркетинговый анализ доступен как tool в Claude.

---

## Phase 13: RAG по документам компании

**Цель:** пользователь загружает PDF/DOCX — система индексирует и отвечает на вопросы с учётом внутренних документов компании.

| # | Задача | DOD |
|---|--------|-----|
| 13.1 | Document loader | `tools/doc_loader.py` — загрузка PDF/DOCX/TXT. Chunking: RecursiveCharacterTextSplitter, 1000 chars, 200 overlap. Возвращает list[Document] |
| 13.2 | Vector store | `tools/vector_store.py` — ChromaDB collection `company_docs`. Функции: `index_documents(docs)`, `search(query, k=5) -> list[Document]` |
| 13.3 | RAG Agent | `agents/rag.py` — retrieval + generation. На запрос "что в нашей стратегии про email" → ищет в vector store → формирует ответ с цитатами |
| 13.4 | Upload в UI | Streamlit sidebar: file uploader (PDF/DOCX). При загрузке: parse → chunk → index. Показать "Indexed N chunks from filename.pdf" |
| 13.5 | Интеграция в граф | RAG Agent как нода. Supervisor роутит запросы про "нашу стратегию", "наш план", "в документе" → rag |
| 13.6 | Тесты | 4+ теста: chunking разбивает текст на чанки нужного размера, vector search возвращает релевантные чанки, RAG agent формирует ответ с источниками, upload + query e2e |

**Результат:** загрузил PDF стратегии → "что мы планируем по email?" → ответ с цитатами из документа.

---

## Phase 14: React UI + FastAPI Backend

**Цель:** заменить Streamlit на production-стек: FastAPI (async API) + React (SPA). Все существующие фичи (чат, графики, HITL, streaming) работают в новом UI.

### 14.1 FastAPI Backend

| # | Задача | DOD |
|---|--------|-----|
| 14.1.1 | Структура проекта | `src/api/` — FastAPI app. `src/api/main.py` — точка входа. `uvicorn src.api.main:app` стартует на порту 8000 |
| 14.1.2 | POST /api/query | Принимает `{query: str, thread_id?: str}`. Возвращает `{thread_id, plan, final_answer, charts: str[], sources: []}`. Вызывает `build_graph().invoke()` |
| 14.1.3 | POST /api/query/stream | SSE endpoint. Стримит события: `{event: "node_start", node: "supervisor"}`, `{event: "node_end", node: "supervisor", data: {...}}`, `{event: "done", data: {final_answer, charts, sources}}` |
| 14.1.4 | POST /api/approve | Принимает `{thread_id: str, plan?: str[]}`. Резьюмит HITL граф. Возвращает `{final_answer, charts, sources}` |
| 14.1.5 | GET /api/health | Возвращает `{status: "ok", version: "0.2.0"}` |
| 14.1.6 | CORS + middleware | CORS разрешает `localhost:5173` (Vite dev). Request logging middleware |
| 14.1.7 | Pydantic schemas | `src/api/schemas.py` — `QueryRequest`, `QueryResponse`, `StreamEvent`, `ApproveRequest`, `HealthResponse`. Все типизированы |
| 14.1.8 | Тесты backend | 6+ тестов: health endpoint 200, query возвращает plan + final_answer, stream возвращает SSE события, approve резьюмит HITL, невалидный request → 422, thread isolation |

**DOD backend:** `pytest tests/test_api.py` — все зелёные. `curl localhost:8000/api/health` → `{"status": "ok"}`.

### 14.2 React Frontend

| # | Задача | DOD |
|---|--------|-----|
| 14.2.1 | Vite + React + TypeScript scaffold | `ui/` — `npm create vite`, React 19 + TypeScript. `npm run dev` стартует на порту 5173 |
| 14.2.2 | Design tokens из Streamlit | CSS variables: `--primary`, `--bg`, `--surface`, etc. Шрифты: Inter + Fira Code. Tailwind с custom tokens |
| 14.2.3 | Layout: Sidebar + Chat | Sidebar (260px, тёмная тема): лого, new conversation, example queries, agents list. Main: chat area + input |
| 14.2.4 | Chat компонент | Список сообщений (user/assistant). Markdown rendering (react-markdown). Inline графики (base64 → img). Sources как ссылки |
| 14.2.5 | Streaming UI | При отправке запроса: показать прогресс по нодам (supervisor → analytics → ...). EventSource для SSE. Каждая нода — строка статуса |
| 14.2.6 | HITL flow | После supervisor: показать план. Кнопки: Approve (primary), Analytics only, Research only. По клику → POST /api/approve |
| 14.2.7 | Welcome state | Пустой чат: иконка + "Ask about your marketing data" + example query cards (кликабельные) |
| 14.2.8 | Responsive | Mobile: sidebar скрывается, chat full-width. Breakpoint: 768px |
| 14.2.9 | API client | `src/lib/api.ts` — функции `sendQuery()`, `streamQuery()`, `approveplan()`, `healthCheck()`. Типизированные |
| 14.2.10 | Тесты frontend | 5+ тестов (Vitest): ChatMessage рендерит markdown, Sidebar показывает example queries, HITL buttons вызывают approve API, welcome state отображается при пустом чате, API client формирует правильные запросы |

**DOD frontend:** `npm test` — все зелёные. `npm run dev` → UI на localhost:5173, подключается к FastAPI на 8000.

### 14.3 Интеграция + Polish

| # | Задача | DOD |
|---|--------|-----|
| 14.3.1 | Docker compose | `docker-compose.yml` обновлён: `api` (FastAPI, порт 8000) + `ui` (nginx, порт 3000). `docker compose up` → рабочая система |
| 14.3.2 | E2E: query → result | Отправить запрос через React UI → FastAPI → LangGraph → ответ с графиками в UI |
| 14.3.3 | E2E: HITL flow | Запрос "ROI vs benchmarks" → план (analytics + research) → approve → результат |
| 14.3.4 | E2E: streaming | Прогресс нод виден в реальном времени в React UI |
| 14.3.5 | Playwright скриншоты | 4 скриншота: welcome state, HITL approval, streaming progress, full result. Визуально соответствуют design system |
| 14.3.6 | README обновлён | Секция "Quick Start" обновлена: `docker compose up` → UI на localhost:3000. Скриншоты React UI |
| 14.3.7 | Регрессия | Все существующие тесты (98+) зелёные. Streamlit UI не удаляется (legacy) |

**DOD интеграция:** полный flow работает через React + FastAPI. Playwright-скриншоты подтверждают.

**Результат:** production-grade SPA вместо Streamlit. SSE streaming, типизированный API, responsive design.

---

## Phase 15: Google Ads / Meta Ads API

**Цель:** подключение к реальным рекламным кабинетам вместо CSV. Данные подтягиваются по API, анализируются теми же агентами.

| # | Задача | DOD |
|---|--------|-----|
| 15.1 | Google Ads connector | `tools/google_ads.py` — подключение через Google Ads API (google-ads-python). Функция `fetch_campaigns(date_from, date_to) -> DataFrame`. Поля: campaign_name, impressions, clicks, conversions, cost, revenue |
| 15.2 | Meta Ads connector | `tools/meta_ads.py` — подключение через Marketing API (facebook-business). Функция `fetch_campaigns(date_from, date_to) -> DataFrame`. Те же поля |
| 15.3 | Yandex Direct connector | `tools/yandex_direct.py` — подключение через Yandex Direct API v5. Функция `fetch_campaigns(date_from, date_to) -> DataFrame` |
| 15.4 | Unified data layer | `tools/data_loader.py` обновлён: `load_data(source)` принимает `"csv"`, `"google_ads"`, `"meta"`, `"yandex"`. Возвращает единый DataFrame с нормализованными столбцами |
| 15.5 | OAuth flow | FastAPI endpoints: `GET /api/connect/google`, `GET /api/connect/meta`. OAuth2 redirect flow. Токены хранятся в `.env` / DB |
| 15.6 | UI: data sources | React sidebar: секция "Data Sources" — статус подключения (connected/disconnected) для каждого сервиса. Кнопка "Connect" |
| 15.7 | Тесты | 4+ теста: mock Google Ads API возвращает DataFrame с правильными столбцами, unified loader нормализует данные из разных источников, analytics agent работает с live-данными так же как с CSV, disconnect/reconnect flow |

**Результат:** подключил Google Ads → "покажи ROI" → реальные данные из кабинета, а не CSV.

---

## Phase 16: Research Agent — SPEC compliance

**Цель:** довести Research Agent до полного соответствия SPEC: FireCrawl для структурированного скрейпинга, RSS для мониторинга, sentiment analysis для brand mentions.

### 16.1 FireCrawl integration

| # | Задача | DOD |
|---|--------|-----|
| 16.1.1 | FireCrawl tool | `tools/firecrawl_scraper.py` — обёртка над FireCrawl API. Функция `firecrawl_scrape(url) -> str` возвращает structured markdown. Fallback на BeautifulSoup при отсутствии ключа |
| 16.1.2 | Интеграция в Research Agent | `research.py` — FireCrawl как primary scraper, BS4 как fallback. LLM tool calling использует оба |
| 16.1.3 | Тесты | 2+ теста: firecrawl tool возвращает structured content (mock), fallback на BS4 работает без API key |

### 16.2 RSS feeds

| # | Задача | DOD |
|---|--------|-----|
| 16.2.1 | RSS tool | `tools/rss.py` — `fetch_rss(url, max_items=10) -> str`. Парсит RSS/Atom feed (feedparser). Возвращает title + summary + link для каждой статьи |
| 16.2.2 | Preset feeds | Список маркетинговых RSS: MarketingLand, Search Engine Journal, HubSpot. Функция `fetch_marketing_news() -> str` |
| 16.2.3 | Интеграция в Research | RSS tool добавлен в `TOOLS` списка Research Agent. На запросы про "новости", "что нового" — вызывается RSS |
| 16.2.4 | Тесты | 2+ теста: RSS парсинг mock-фида возвращает items, preset feeds возвращает данные |

### 16.3 Sentiment analysis

| # | Задача | DOD |
|---|--------|-----|
| 16.3.1 | Sentiment tool | `tools/sentiment.py` — `analyze_sentiment(texts: list[str]) -> list[dict]`. Возвращает `{text, sentiment: positive/negative/neutral, score: float}`. Используем TextBlob или VADER (без тяжёлых моделей) |
| 16.3.2 | Brand mention monitoring | Функция `monitor_brand(brand_name) -> str` — Tavily search по бренду → sentiment analysis каждого результата → summary: "X positive, Y negative, Z neutral mentions" |
| 16.3.3 | Интеграция в Research | На запросы "что пишут про бренд X", "reputation" — Research agent вызывает monitor_brand |
| 16.3.4 | Тесты | 3+ теста: sentiment правильно классифицирует positive/negative/neutral, monitor_brand возвращает summary с counts, integration в граф через Research agent |

**DOD Phase 16:** Research Agent поддерживает FireCrawl, RSS, sentiment. Все новые тесты зелёные + 0 регрессий.

**Результат:** "Что пишут про наш бренд?" → sentiment summary + sources. "Новости в маркетинге?" → RSS digest.

---

## Phase 17: Analytics Agent — SPEC compliance

**Цель:** довести Analytics Agent до полного соответствия SPEC: SQL loader для баз данных, Google Sheets для онлайн-таблиц, LTV/когорты, сегментация аудитории.

### 17.1 SQL loader

| # | Задача | DOD |
|---|--------|-----|
| 17.1.1 | SQL tool | `tools/sql_loader.py` — `query_sql(connection_string, query) -> DataFrame`. Поддержка SQLite и PostgreSQL (sqlalchemy). Валидация: только SELECT, без мутаций |
| 17.1.2 | Demo SQLite | `data/demo.db` — SQLite база с таблицей `campaigns` (те же данные что в demo_campaigns.csv). Скрипт генерации: `data/generate_db.py` |
| 17.1.3 | Интеграция в Analytics | `data_loader.py`: `load_dataframe(path)` — если path заканчивается на `.db` или начинается с `postgresql://`, использует SQL loader. CSV остаётся дефолтом |
| 17.1.4 | Тесты | 3+ теста: SQL tool загружает из SQLite, возвращает DataFrame с правильными столбцами, SELECT-only валидация блокирует DELETE/UPDATE |

### 17.2 Advanced metrics (LTV, когорты)

| # | Задача | DOD |
|---|--------|-----|
| 17.2.1 | LTV расчёт | `tools/data_loader.py`: `compute_metrics(metric="ltv")` — LTV = revenue / conversions per channel. Группировка по каналам |
| 17.2.2 | Когортный анализ | `tools/data_loader.py`: `compute_metrics(metric="cohort")` — группировка по месяцу первого касания, retention по последующим месяцам. Возвращает таблицу retention |
| 17.2.3 | Тесты | 2+ теста: LTV возвращает числа для каждого канала, когортная таблица имеет правильную форму (месяцы × когорты) |

### 17.3 Сегментация аудитории

| # | Задача | DOD |
|---|--------|-----|
| 17.3.1 | Сегментация по поведению | `tools/segmentation.py` — `segment_campaigns(df) -> str`. K-means кластеризация кампаний по нормализованным метрикам (CTR, CPA, ROAS). Возвращает 3-5 сегментов с описанием: "Высокий ROI / низкий объём", "Массовый охват / низкая конверсия" |
| 17.3.2 | Визуализация | Scatter plot сегментов (spend vs ROAS, цвет = кластер). base64 PNG через matplotlib |
| 17.3.3 | Интеграция | На запросы "сегментируй кампании", "какие группы кампаний" — Analytics agent вызывает segmentation |
| 17.3.4 | Тесты | 3+ теста: сегментация возвращает 3+ кластеров, каждый кластер имеет label и описание, scatter plot генерируется в base64 |

**DOD Phase 17:** Analytics Agent поддерживает SQL, LTV, когорты, сегментацию. Все новые тесты зелёные + 0 регрессий.

**Результат:** "Сегментируй наши кампании" → кластеры + scatter plot. "Покажи LTV по каналам" → таблица + интерпретация.

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
| 7. Production LangGraph | 1 сессия |
| 8. README + Polish | 1 сессия |
| 9. Intelligent Report Layer | 1 сессия |
| 10. UX/UI Audit & Polish | 1 сессия |
| 11. Strategy Agent | 1 сессия |
| 12. MCP Server | 1 сессия |
| 13. RAG по документам | 1-2 сессии |
| 14. React UI + FastAPI | 2-3 сессии |
| 15. Google Ads / Meta Ads API | 1-2 сессии |
| 16. Research Agent SPEC compliance | 1 сессия |
| 17. Analytics Agent SPEC compliance | 1-2 сессии |
| **Итого MVP (1-10)** | **9-11 сессий** |
| **Итого полный (1-17)** | **16-23 сессии** |

> 1 сессия = один рабочий заход с Claude Code.
