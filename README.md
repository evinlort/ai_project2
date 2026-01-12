# IntentBid MVP

IntentBid is a minimal Request for Offer (RFO) bidding service. Buyers post RFOs with constraints and weighted preferences; vendors register, submit offers, and the system scores and ranks them with a transparent rule-based formula. A small vendor dashboard is included for browsing open RFOs and tracking offers.

## How it works

- Vendor registers and receives a one-time API key (stored hashed).
- Buyer creates an RFO with constraints and preference weights.
- Vendor submits offers for an OPEN RFO using `X-API-Key`.
- `/v1/rfo/{id}/best` returns the top offers with a score breakdown.
- Dashboard exposes login and RFO/offer views for vendors.

## Tech stack

- FastAPI + SQLModel for the API and data layer.
- Postgres via docker-compose; SQLite by default for local dev.
- Alembic migrations in `intentbid/app/db/migrations`.
- Jinja2 templates for the dashboard.
- Pytest for tests.

## Project layout

- `intentbid/app/main.py`: FastAPI app + `/health`.
- `intentbid/app/api/*`: REST routes for vendors, RFOs, offers, dashboard.
- `intentbid/app/core/scoring.py`: rule-based scoring with explain output.
- `intentbid/app/db/models.py`: Vendor, RFO, Offer models.
- `intentbid/scripts/seed_demo.py`: seed data + write demo vendor keys.
- `intentbid/scripts/vendor_simulator.py`: simulate vendors posting offers.
- `intentbid/tests/*`: API + scoring tests.

## Quick start (Docker + Postgres)

Start services:

```bash
docker-compose up --build
```

Run migrations once to create tables:

```bash
docker-compose run --rm api alembic upgrade head
```

API: `http://localhost:8000`  
OpenAPI docs: `http://localhost:8000/docs`  
Postgres: `localhost:15432` (user/password/db `intentbid`)

## Local development (SQLite)

Install deps and run migrations against SQLite (default):

```bash
pip install -e .
alembic upgrade head
```

Run the API:

```bash
uvicorn intentbid.app.main:app --reload
```

This creates `intentbid.db` in the repo root unless `DATABASE_URL` is set.

## Configuration

Environment variables:

- `DATABASE_URL` (default `sqlite:///./intentbid.db`)
- `SECRET_KEY` (used to hash API keys)
- `ENV` (`dev` enables SQL echo)

## Core API endpoints

Vendor registration (returns API key once):

```bash
curl -X POST http://localhost:8000/v1/vendors/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme"}'
```

Create an RFO:

```bash
curl -X POST http://localhost:8000/v1/rfo \
  -H "Content-Type: application/json" \
  -d '{
    "category": "sneakers",
    "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
    "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1}
  }'
```

Submit an offer (requires `X-API-Key`):

```bash
curl -X POST http://localhost:8000/v1/offers \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <api_key>" \
  -d '{
    "rfo_id": 1,
    "price_amount": 109.99,
    "currency": "USD",
    "delivery_eta_days": 2,
    "warranty_months": 12,
    "return_days": 30,
    "stock": true,
    "metadata": {"sku": "ABC"}
  }'
```

Get RFO details and best offers:

```bash
curl http://localhost:8000/v1/rfo/1
curl "http://localhost:8000/v1/rfo/1/best?top_k=3"
```

Check current vendor (requires `X-API-Key`):

```bash
curl http://localhost:8000/v1/vendors/me -H "X-API-Key: <api_key>"
```

## Scoring logic

The scoring model is intentionally transparent:

- Hard filters (score = 0):
  - `price_amount > budget_max`
  - `stock == false`
  - `delivery_eta_days > delivery_deadline_days`
- Normalized components:
  - `price_score = clamp01(1 - price_amount / budget_max)`
  - `delivery_score = clamp01(1 - delivery_eta_days / delivery_deadline_days)`
  - `warranty_score = clamp01(warranty_months / 24)`
- Final score uses weights from `preferences` (defaults: `w_price=0.5`, `w_delivery=0.3`, `w_warranty=0.2`).

The `/v1/rfo/{id}/best` response includes an `explain` field with the breakdown.

## Vendor dashboard

A minimal UI for vendors (Jinja2 templates):

- Login: `http://localhost:8000/dashboard/login`
- Open RFO list: `http://localhost:8000/dashboard/rfos`
- RFO detail + submit offer: `http://localhost:8000/dashboard/rfos/<id>`
- Your offers + win/loss: `http://localhost:8000/dashboard/offers`

You can also pass `?api_key=...` to `/dashboard/rfos` if you want a direct link; the API key is stored in a cookie for convenience.

## Demo data

Seed demo vendors/RFOs/offers (also creates tables and writes `intentbid/scripts/demo_vendors.json`):

```bash
python intentbid/scripts/seed_demo.py
```

Simulate vendors posting offers:

```bash
python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3
```

Docker equivalents:

```bash
docker-compose run --rm api python intentbid/scripts/seed_demo.py
docker-compose run --rm api python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3
```

## Tests

```bash
pip install ".[dev]"
pytest
```

## Notes

- RFOs are stored with `constraints` and `preferences` as JSON; the scoring logic only uses `budget_max` and `delivery_deadline_days`, but other fields are preserved.
- Offers can only be submitted while the RFO status is `OPEN`.
- API keys are hashed in the database; treat the raw key as a secret.
---
# IntentBid MVP

IntentBid — это минимальный сервис торгов по Request for Offer (RFO). Покупатели публикуют RFO с ограничениями и весами предпочтений; продавцы регистрируются, отправляют офферы, а система считает и ранжирует их по прозрачной rule-based формуле. Включена простая панель продавца для просмотра открытых RFO и отслеживания офферов.

## Как это работает

- Продавец регистрируется и получает одноразовый API-ключ (в базе хранится хеш).
- Покупатель создает RFO с ограничениями и весами предпочтений.
- Продавец отправляет офферы для RFO со статусом OPEN с помощью `X-API-Key`.
- `/v1/rfo/{id}/best` возвращает лучшие офферы с пояснением скоринга.
- Панель предоставляет страницы логина и списка RFO/офферов для продавца.

## Технологии

- FastAPI + SQLModel для API и слоя данных.
- Postgres через docker-compose; SQLite по умолчанию для локальной разработки.
- Миграции Alembic в `intentbid/app/db/migrations`.
- Jinja2 шаблоны для панели.
- Pytest для тестов.

## Структура проекта

- `intentbid/app/main.py`: FastAPI приложение + `/health`.
- `intentbid/app/api/*`: REST маршруты для vendors, RFO, offers, dashboard.
- `intentbid/app/core/scoring.py`: rule-based скоринг с explain результатом.
- `intentbid/app/db/models.py`: модели Vendor, RFO, Offer.
- `intentbid/scripts/seed_demo.py`: сид данных + запись ключей вендоров.
- `intentbid/scripts/vendor_simulator.py`: симуляция отправки офферов.
- `intentbid/tests/*`: тесты API + скоринга.

## Быстрый старт (Docker + Postgres)

Запустите сервисы:

```bash
docker-compose up --build
```

Один раз выполните миграции, чтобы создать таблицы:

```bash
docker-compose run --rm api alembic upgrade head
```

API: `http://localhost:8000`  
OpenAPI docs: `http://localhost:8000/docs`  
Postgres: `localhost:15432` (user/password/db `intentbid`)

## Локальная разработка (SQLite)

Установите зависимости и выполните миграции для SQLite (по умолчанию):

```bash
pip install -e .
alembic upgrade head
```

Запуск API:

```bash
uvicorn intentbid.app.main:app --reload
```

Это создаст `intentbid.db` в корне репозитория, если не задан `DATABASE_URL`.

## Конфигурация

Переменные окружения:

- `DATABASE_URL` (по умолчанию `sqlite:///./intentbid.db`)
- `SECRET_KEY` (используется для хеширования API ключей)
- `ENV` (`dev` включает вывод SQL)

## Основные эндпоинты API

Регистрация продавца (API-ключ возвращается один раз):

```bash
curl -X POST http://localhost:8000/v1/vendors/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme"}'
```

Создание RFO:

```bash
curl -X POST http://localhost:8000/v1/rfo \
  -H "Content-Type: application/json" \
  -d '{
    "category": "sneakers",
    "constraints": {"budget_max": 120, "size": 42, "delivery_deadline_days": 3},
    "preferences": {"w_price": 0.6, "w_delivery": 0.3, "w_warranty": 0.1}
  }'
```

Отправка оффера (требуется `X-API-Key`):

```bash
curl -X POST http://localhost:8000/v1/offers \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <api_key>" \
  -d '{
    "rfo_id": 1,
    "price_amount": 109.99,
    "currency": "USD",
    "delivery_eta_days": 2,
    "warranty_months": 12,
    "return_days": 30,
    "stock": true,
    "metadata": {"sku": "ABC"}
  }'
```

Детали RFO и лучшие офферы:

```bash
curl http://localhost:8000/v1/rfo/1
curl "http://localhost:8000/v1/rfo/1/best?top_k=3"
```

Проверить текущего продавца (требуется `X-API-Key`):

```bash
curl http://localhost:8000/v1/vendors/me -H "X-API-Key: <api_key>"
```

## Логика скоринга

Скоринг намеренно прозрачен:

- Жесткие фильтры (score = 0):
  - `price_amount > budget_max`
  - `stock == false`
  - `delivery_eta_days > delivery_deadline_days`
- Нормализованные компоненты:
  - `price_score = clamp01(1 - price_amount / budget_max)`
  - `delivery_score = clamp01(1 - delivery_eta_days / delivery_deadline_days)`
  - `warranty_score = clamp01(warranty_months / 24)`
- Итоговый score использует веса из `preferences` (по умолчанию: `w_price=0.5`, `w_delivery=0.3`, `w_warranty=0.2`).

Ответ `/v1/rfo/{id}/best` включает поле `explain` с деталями расчета.

## Панель продавца

Минимальный UI для продавцов (шаблоны Jinja2):

- Логин: `http://localhost:8000/dashboard/login`
- Список открытых RFO: `http://localhost:8000/dashboard/rfos`
- Детали RFO + отправка оффера: `http://localhost:8000/dashboard/rfos/<id>`
- Мои офферы + win/loss: `http://localhost:8000/dashboard/offers`

Можно также передать `?api_key=...` в `/dashboard/rfos` для прямой ссылки; для удобства ключ сохраняется в cookie.

## Демо-данные

Сидирование демо-данных (также создает таблицы и пишет `intentbid/scripts/demo_vendors.json`):

```bash
python intentbid/scripts/seed_demo.py
```

Симуляция отправки офферов продавцами:

```bash
python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3
```

Эквивалентные команды для Docker:

```bash
docker-compose run --rm api python intentbid/scripts/seed_demo.py
docker-compose run --rm api python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3
```

## Тесты

```bash
pip install ".[dev]"
pytest
```

## Примечания

- RFO хранят `constraints` и `preferences` как JSON; логика скоринга использует только `budget_max` и `delivery_deadline_days`, остальные поля сохраняются.
- Офферы можно отправлять только пока статус RFO равен `OPEN`.
- API-ключи хешируются в базе; исходный ключ нужно хранить как секрет.
