# oncology-clinic-ai-agent-chatbot

Справочный чат-бот онкодиспансера (прототип MVP).

Бот отвечает утверждёнными текстами из базы знаний, всегда показывает источник, не даёт медицинских назначений и передаёт вопрос специалисту. Границы и критерии приёмки — в [`docs/spec.md`](docs/spec.md). Правила работы — в [`AGENTS.md`](AGENTS.md).

> Все тексты в `data/kb.json` — **тестовые**, не утверждены заказчиком.

## Что внутри

- `app/lemmatize.py` — лемматизация русского языка (pymorphy3)
- `app/safety.py` — правила безопасности (экстренные симптомы, назначения)
- `app/kb.py` — база знаний и обращения (SQLite, FTS5)
- `app/pipeline.py` — конвейер ответа: безопасность → поиск → источник или передача специалисту
- `app/main.py` — FastAPI: API и страницы
- `app/static/` — виджет чата и страница оператора
- `data/kb.json` — тестовая база знаний
- `tests/questions.csv` — тестовый набор вопросов с ожидаемым поведением
- `tests/test_pipeline.py` — тесты на тестовый набор

## Запуск

```bash
py -m pip install -r requirements.txt
py -m pytest tests/ -q
py -m uvicorn app.main:app --reload
```

- Чат: http://localhost:8000/
- Оператор: http://localhost:8000/operator

## API

- `POST /api/ask` — `{"text": "..."}` → тип ответа (`answer` / `refuse` / `emergency` / `not_found`), текст, источник, флаг передачи
- `POST /api/handoff` — `{"dialog_text": "..."}` → создаёт обращение
- `GET /api/tickets` — список обращений
- `POST /api/tickets/{id}/answer` — `{"answer": "..."}` → ответ оператора
