# Marketing Intelligence Agent

> Multi-agent система для маркетинговой аналитики на LangGraph
> Статус: spec draft | Апрель 2026

---

## Зачем

Маркетологи тратят 60%+ времени на ручной сбор данных, анализ конкурентов и генерацию отчётов. Эта система делает это автоматически: задаёшь вопрос на человеческом языке — получаешь ответ с данными, графиками и рекомендациями.

**Целевой пользователь:** маркетолог / growth-менеджер / CMO малого-среднего бизнеса.

**Пример использования:**
- "Как изменился ROI по каналам за последний месяц?"
- "Найди, что пишут про наш бренд в соцсетях"
- "Сравни наши метрики с конкурентами"
- "Предложи, куда перераспределить бюджет"

---

## Архитектура

```
User Query
    |
    v
[Supervisor Agent] — LangGraph orchestrator
    |
    ├── [Research Agent]    — веб-скрейпинг, мониторинг конкурентов, тренды
    ├── [Analytics Agent]   — анализ данных кампаний (CSV/SQL), метрики, аномалии
    ├── [Strategy Agent]    — рекомендации по бюджету и действиям
    └── [Report Agent]      — форматирование ответа, графики, markdown
    |
    v
[Evaluation Layer] — RAGAS / LLM-as-judge, качество ответов
    |
    v
Response (text + charts + sources)
```

### Граф (LangGraph)

```
START → supervisor → route_to_agents → [research | analytics | strategy] → synthesize → evaluate → END
                                                                              ↑
                                                                    human-in-the-loop
                                                                    (approve/reject/refine)
```

---

## Агенты

### 1. Supervisor Agent
- Разбирает запрос пользователя
- Определяет, какие агенты нужны (один или несколько)
- Оркестрирует выполнение через LangGraph state machine
- Решает, нужна ли итерация (если данных недостаточно)

### 2. Research Agent
- **Инструменты:** Tavily Search, FireCrawl (веб-скрейпинг), RSS-фиды
- **Задачи:**
  - Мониторинг упоминаний бренда (sentiment analysis)
  - Анализ контента конкурентов
  - Поиск трендов в нише
  - Сбор данных из открытых источников
- **Выход:** структурированный JSON с источниками и цитатами

### 3. Analytics Agent
- **Инструменты:** Python REPL (pandas), SQL (SQLite/PostgreSQL), matplotlib
- **Задачи:**
  - Загрузка и анализ данных кампаний (CSV, Google Sheets, SQL)
  - Расчёт метрик: ROI, CPA, LTV, конверсии, когорты
  - Обнаружение аномалий (резкие изменения метрик)
  - Сегментация аудитории
- **Выход:** числа, таблицы, графики (base64 PNG)

### 4. Strategy Agent
- **Инструменты:** доступ к результатам Research и Analytics агентов
- **Задачи:**
  - Рекомендации по перераспределению бюджета
  - Приоритизация каналов по ROI
  - Action items: что делать на этой неделе
  - Прогноз на основе трендов
- **Выход:** структурированные рекомендации с обоснованием

### 5. Report Agent (Intelligent Report Layer)
- Собирает выходы всех агентов
- **Интерпретирует данные** — не дампит таблицу, а отвечает на вопрос ("лучшая кампания — retargeting_cart с ROAS 8.11")
- **Приоритизирует аномалии** — группирует по кампании, классифицирует тип (бот-трафик, CPC spike, мусорная площадка), показывает топ-3 критичных
- **Даёт рекомендации** — ROAS < 1 → "рассмотреть отключение", CTR аномально высокий + 0 конверсий → "вероятный бот-трафик, проверить площадки"
- **Не показывает debug** — "Loaded 8688 rows, 14 columns..." — internal context, не output
- Форматирует в читаемый Markdown
- Указывает источники данных

---

## Стек

| Компонент | Технология | Почему |
|-----------|------------|--------|
| Orchestration | **LangGraph** | Де-факто стандарт, граф-воркфлоу, human-in-the-loop |
| LLM | **Claude 4 / GPT-4o** | Через LangChain — можно переключать |
| Vector DB | **ChromaDB** (dev) → **pgvector** (prod) | Простой старт, масштабируется |
| Web Search | **Tavily** | Оптимизирован для AI-агентов |
| Web Scraping | **FireCrawl** / **BeautifulSoup** | Структурированный скрейпинг |
| Data Analysis | **pandas** + **matplotlib** | Стандарт |
| Evaluation | **RAGAS** + **LLM-as-judge** | Метрики качества RAG |
| API | **FastAPI** | Async, быстрый, типизированный |
| UI | **Streamlit** (MVP) → **React** (prod) | Быстрый прототип |
| MCP | **MCP сервер** для внешних интеграций | Показывает MCP-скилл |

---

## Данные

### Входные данные
1. **CSV/Excel** — выгрузки из рекламных кабинетов (Google Ads, Meta Ads, Yandex Direct)
2. **SQL** — подключение к аналитической БД
3. **Веб** — скрейпинг конкурентов, соцсетей, новостей
4. **RAG база** — загруженные документы компании (стратегии, отчёты, брифы)

### Демо-данные
Синтетический датасет маркетинговых кампаний:
- 6 каналов (Google Ads, Meta, TikTok, Yandex, Email, SEO)
- 12 месяцев данных
- Метрики: impressions, clicks, conversions, spend, revenue
- Встроенные аномалии для тестирования детекции

---

## MVP (v0.1) — scope

Минимум для рабочего демо:

- [ ] LangGraph граф с Supervisor + 2 агента (Analytics + Research)
- [ ] Analytics Agent: загрузка CSV, базовые метрики (ROI, CPA), один график
- [ ] Research Agent: Tavily search по запросу, структурированный ответ
- [ ] Синтетический демо-датасет (6 каналов, 12 месяцев)
- [ ] Streamlit UI: чат-интерфейс, отображение графиков
- [ ] Evaluation: базовый LLM-as-judge (relevance + correctness)
- [ ] README с архитектурной диаграммой и инструкцией запуска

### Принципы ответа (Report Layer)

1. **Отвечай на вопрос, не дампи данные.** Пользователь спросил "где мы сливаем бюджет?" — ответ должен назвать конкретные кампании и суммы, а не показать таблицу.
2. **Debug-информация — internal.** Строки типа "Loaded N rows, Columns: ..." не должны попадать в ответ.
3. **Аномалии = приоритизированный список.** Не "Found 1365 anomalies", а "3 критические проблемы: (1)..., (2)..., (3)..."
4. **Рекомендации обязательны.** Каждый аналитический ответ завершается секцией "Рекомендации" с конкретными действиями.

### Не в MVP
- Strategy Agent (v0.2)
- MCP сервер (v0.2)
- RAG по документам компании (v0.3)
- Human-in-the-loop approval flow (v0.3)
- PostgreSQL / pgvector (v0.3)
- React UI (v1.0)
- Интеграции с Google Ads API / Meta API (v1.0)

---

## Evaluation Pipeline

Каждый ответ системы оценивается по:

| Метрика | Метод | Порог |
|---------|-------|-------|
| Relevance | LLM-as-judge | >= 0.8 |
| Correctness | Сравнение с ground truth (для аналитики) | >= 0.9 |
| Faithfulness | RAGAS (для research) | >= 0.85 |
| Latency | Таймер | < 30s для простых, < 120s для complex |

---

## Структура проекта

```
marketing-intelligence-agent/
├── SPEC.md
├── README.md
├── pyproject.toml
├── .env.example
├── src/
│   ├── __init__.py
│   ├── graph.py              # LangGraph определение графа
│   ├── state.py              # State schema
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor.py     # Supervisor / router
│   │   ├── research.py       # Research agent
│   │   ├── analytics.py      # Analytics agent
│   │   ├── strategy.py       # Strategy agent (v0.2)
│   │   └── report.py         # Report formatter
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py         # Tavily wrapper
│   │   ├── scraper.py        # Web scraping
│   │   ├── data_loader.py    # CSV/SQL loader
│   │   └── charts.py         # matplotlib chart generation
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── evaluator.py      # RAGAS + LLM-as-judge
│   └── ui/
│       └── app.py            # Streamlit app
├── data/
│   └── demo_campaigns.csv    # Синтетический датасет
└── tests/
    ├── test_graph.py
    ├── test_analytics.py
    └── test_research.py
```

---

## Что это демонстрирует для портфолио

| Скилл из вакансий | Где в проекте |
|-------------------|---------------|
| LangGraph | Граф оркестрации, state machine, routing |
| RAG | Research agent + vector store для документов |
| Evaluation | RAGAS + LLM-as-judge pipeline |
| MCP | MCP сервер для внешних инструментов (v0.2) |
| Tool Use | Tavily, Python REPL, SQL, scraping |
| Human-in-the-loop | Approval flow в графе (v0.3) |
| Production patterns | FastAPI, Docker, CI/CD, метрики |
| Domain expertise | Маркетинговые метрики, ROI, когорты — unfair advantage |

---

## Production LangGraph Features

Фичи, которые отличают production-grade LangGraph проект от tutorial copy-paste.
Именно их ищут в вакансиях при упоминании LangGraph (senior+ level).

### Checkpointing + Memory

Граф сохраняет состояние между вызовами. Каждый диалог — `thread_id`.
Пользователь может продолжить разговор с контекстом предыдущих вопросов.

- `MemorySaver` для dev/test, `AsyncPostgresSaver` для prod
- Thread-scoped state, переживает рестарт процесса
- Time-travel: возможность вернуться к любому шагу выполнения

### Human-in-the-loop (HITL)

Supervisor предлагает план — пользователь подтверждает или корректирует перед выполнением.
Ключевой дифференциатор LangGraph vs CrewAI/AutoGen.

- `interrupt_before` на ноде dispatcher (после supervisor, перед агентами)
- Граф останавливается, сохраняет state в checkpoint
- Пользователь видит план, может изменить набор агентов
- `graph.invoke(None, config)` для resume с тем же thread_id

### Streaming

Поэтапный вывод результатов в UI: supervisor решил → analytics работает → результат.
Не "подождите 10 секунд... готово", а живой процесс.

- `stream_mode="updates"` — события по нодам
- Streamlit UI показывает прогресс каждой ноды в реальном времени

### Error Recovery

Если агент упал (timeout, bad data, API error) — граф не крашится.
Re-plan нода перенаправляет на fallback или retry.

- Try/except в каждой agent-ноде, ошибка записывается в `AgentOutput.error`
- Synthesize нода обрабатывает частичные результаты
- Fallback: если analytics упал, research всё равно отрабатывает

---

## Порядок реализации

1. **Скелет** — pyproject.toml, зависимости, структура папок
2. **State + Graph** — LangGraph state schema, базовый граф
3. **Analytics Agent** — CSV loader, pandas, метрики, графики
4. **Research Agent** — Tavily search, структурированный output
5. **Supervisor** — routing логика, объединение результатов
6. **Evaluation** — LLM-as-judge, метрики
7. **Демо-данные** — синтетический датасет
8. **Streamlit UI** — чат + графики
9. **README** — архитектура, скриншоты, инструкции
