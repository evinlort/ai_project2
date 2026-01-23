# IntentBid MVP

IntentBid is a minimal Request for Offer (RFO) bidding service. Buyers post RFOs with constraints and weighted preferences; vendors register, submit offers, and the system scores and ranks them with a transparent rule-based formula. Vendor and buyer dashboards are included for creating RFOs, browsing open requests, and tracking offers.

## Aggregator overview

IntentBid acts as an aggregator: buyers publish buyer requests (RFOs), and vendors respond with vendor offers.

Glossary:

- Buyer request = RFO
- Vendor offer = Offer

Flow:

- Buyer posts a request -> vendors submit offers -> ranking returns the best offers.

The UI calls the same API endpoints used by automation.

## Hardware Procurement

IntentBid is being productized for urgent B2B procurement of high-demand compute components where supply is fragmented and quotes are slow.

- Problem: GPU, memory, and enterprise storage shortages create fragmented, slow quoting across distributors and brokers.
- Supported categories: `gpu`, `memory`, `ssd`, `nic`.
- Deal cycle promise: quotes in hours, award in a day.
- Why IntentBid differs: transparent scoring + explain, webhook outbox, Python SDK, and enforceable plan limits.
- Target ICP:
  - Buyers: AI startups, labs, SMB data centers, system integrators, MSPs sourcing GPUs/memory/SSD urgently.
  - Vendors: authorized distributors + vetted brokers with inventory, lead times, and traceability docs.
- Pilot checklist: see `docs/pilot_checklist.md`.

## How it works

- Vendor registers and receives a one-time API key (stored hashed).
- Buyer creates an RFO with constraints and preference weights.
- Vendor submits offers for an OPEN RFO using `X-API-Key`.
- `/v1/rfo/{id}/best` returns the top offers with a score breakdown.
- Dashboards expose buyer RFO creation/checks plus vendor offer tracking views.

## Tech stack

- FastAPI + SQLModel for the API and data layer.
- Postgres via docker-compose; SQLite by default for local dev.
- Alembic migrations in `intentbid/app/db/migrations`.
- Jinja2 templates for the dashboards.
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

Start everything (db + migrations + API) with one command:

```bash
./scripts/start_dashboard.sh
```

Or start services manually:

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

## Automation guide for robots and agents

Automate the workflow with HTTP or the SDK. Typical bot flow: list requests, submit offers, fetch rankings.

HTTP (curl):

```bash
curl "http://localhost:8000/v1/rfo?status=OPEN&limit=5"
curl -X POST http://localhost:8000/v1/offers \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <api_key>" \
  -d '{"rfo_id": 1, "price_amount": 109.99, "currency": "USD", "delivery_eta_days": 2}'
curl http://localhost:8000/v1/buyers/rfo/1/ranking -H "X-Buyer-API-Key: <buyer_key>"
```

SDK (Python):

```python
from intentbid.sdk import IntentBidClient

client = IntentBidClient(base_url="http://localhost:8000", api_key="<vendor_key>")
rfos = client.list_rfos(status="OPEN", limit=5)
client.submit_offer({"rfo_id": 1, "price_amount": 109.99, "currency": "USD", "delivery_eta_days": 2})

buyer = client.register_buyer("Demo Buyer")
ranking = client.get_buyer_ranking(1, buyer["api_key"])
```

Limits: offer throttles are controlled by `settings.max_offers_per_vendor_rfo` and
`settings.offer_cooldown_seconds` in `intentbid.app.core.config`; monthly plan caps are enforced by
`PlanLimit` and return `429 Plan limit exceeded` when exceeded.

## Access control & onboarding

- `POST /v1/vendors/keys` creates a new API key for the logged-in vendor; the raw key is returned once while the database stores a hashed copy and tracks `last_used_at`.
- `POST /v1/vendors/keys/{key_id}/revoke` updates the key status to `revoked` and records `revoked_at` so rotated keys can be retired without affecting other tokens.
- `POST /v1/vendors/webhooks` registers a webhook that receives signed events (`rfo.created`, `offer.created`, `rfo.closed`, `rfo.awarded`), while `EventOutbox` ensures retries, backoff, and `last_delivery_at` updates even if deliveries fail temporarily.
- `GET /v1/vendors/onboarding/status` summarizes whether the vendor has an active API key and webhook so dashboards can highlight next steps.

## Buyer access & ranking

- `POST /v1/buyers/register` issues a buyer-scoped API key that must be sent as `X-Buyer-API-Key` on subsequent requests.
- `GET /v1/buyers/me` mirrors the vendor `/me` so buyers can confirm their identity.
- `GET /v1/buyers/rfo/{rfo_id}/ranking` returns every offer for the RFO together with `score` and the `explain` payload so buyers can inspect the ranking in detail.

## RFO lifecycle & scoring

- Status transitions follow the `OPEN -> CLOSED -> AWARDED` lifecycle with dedicated endpoints: `/rfo/{id}/close`, `/award`, and `/reopen` (idempotent checks prevent invalid transitions, and each change writes an `audit_log` entry with the optional reason).
- `/v1/rfo/{id}/scoring` accepts a new `scoring_version` and per-component `weights`, making it possible to lock a version for auditability while tweaking individual RFO priorities.
- `/v1/rfo/{id}/ranking/explain` shows the resolved `scoring_version`, per-component breakdown, and any active penalties so every decision is traceable on a per-RFO basis.

## Validation & billing

- Offer submission enforces `price_amount`, `delivery_eta_days`, and warranty/return ranges along with a configurable `max_offers_per_vendor_rfo` and `offer_cooldown_seconds` (set via environment or `.env` through `intentbid.app.core.config.settings`).
- Vendors are matched to `Subscription` records and `PlanLimit` caps; creation of an offer records a `UsageEvent` and fails with `429 Plan limit exceeded` when the monthly cap is reached.

## Notifications & webhooks

- `enqueue_event` writes signed webhook payloads to `EventOutbox` for `rfo.created`, `offer.created`, `rfo.closed`, and `rfo.awarded`; `dispatch_outbox` (e.g., from a worker or cron) polls pending events, signs them with the webhook secret, and retries with exponential backoff before moving to dead lettering.
- Webhook deliveries include the `X-IntentBid-Signature` header so receivers can verify authenticity and vendors can manage retry metrics via `last_delivery_at`.

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

### Dashboard links (English)

- Login: [http://localhost:8000/dashboard/login](http://localhost:8000/dashboard/login)
- Open RFO list: [http://localhost:8000/dashboard/rfos](http://localhost:8000/dashboard/rfos)
- RFO detail + submit offer: [http://localhost:8000/dashboard/rfos/<id>](http://localhost:8000/dashboard/rfos/<id>)
- Your offers + win/loss: [http://localhost:8000/dashboard/offers](http://localhost:8000/dashboard/offers)

### Buyer dashboard (UI)

- Create an RFO: [http://localhost:8000/buyer/rfos/new](http://localhost:8000/buyer/rfos/new)
- Check an RFO: [http://localhost:8000/buyer/rfos/check](http://localhost:8000/buyer/rfos/check)
- Best offers: [http://localhost:8000/buyer/rfos/best](http://localhost:8000/buyer/rfos/best)
- Buyer scoring: [http://localhost:8000/buyer/rfos/scoring](http://localhost:8000/buyer/rfos/scoring)

Buyer scoring expects a buyer API key from `POST /v1/buyers/register`.

### Buyer dashboard (API)

- Register buyer: `POST /v1/buyers/register` (returns buyer key)
- Confirm identity: `GET /v1/buyers/me` with `X-Buyer-API-Key`
- Ranking transcript: `GET /v1/buyers/rfo/{id}/ranking` to inspect every offer + explain

You can also pass `?api_key=...` to `/dashboard/rfos` if you want a direct link; the API key is stored in a cookie for convenience.

### Dashboard API reference (English)

After you log in through `/dashboard/login`, the new `/dashboard/apis` page displays cards for every API call. Each card links to `/dashboard/apis/<slug>` where the dashboard shows the HTTP method, endpoint, required authentication, a runnable curl example, and any notes about validation or auditing.

- `POST /v1/vendors/register` → `/dashboard/apis/vendor-registration`
- `POST /v1/vendors/keys` → `/dashboard/apis/vendor-keys`
- `POST /v1/vendors/keys/{key_id}/revoke` → `/dashboard/apis/vendor-revoke-key`
- `POST /v1/vendors/webhooks` → `/dashboard/apis/vendor-webhooks`
- `GET /v1/vendors/onboarding/status` → `/dashboard/apis/vendor-onboarding`
- `GET /v1/vendors/me` → `/dashboard/apis/vendor-me`
- `POST /v1/buyers/register` → `/dashboard/apis/buyer-registration`
- `GET /v1/buyers/me` → `/dashboard/apis/buyer-me`
- `GET /v1/buyers/rfo/{rfo_id}/ranking` → `/dashboard/apis/buyer-ranking`
- `POST /v1/rfo` → `/dashboard/apis/rfo-create`
- `GET /v1/rfo/{id}` → `/dashboard/apis/rfo-detail`
- `GET /v1/rfo/{id}/best` → `/dashboard/apis/rfo-best`
- `POST /v1/offers` → `/dashboard/apis/offer-create`
- `POST /v1/rfo/{id}/close` → `/dashboard/apis/rfo-close`
- `POST /v1/rfo/{id}/award` → `/dashboard/apis/rfo-award`
- `POST /v1/rfo/{id}/reopen` → `/dashboard/apis/rfo-reopen`
- `POST /v1/rfo/{id}/scoring` → `/dashboard/apis/rfo-scoring`
- `GET /v1/rfo/{id}/ranking/explain` → `/dashboard/apis/rfo-ranking-explain`

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

## Обзор агрегатора

IntentBid работает как агрегатор: покупатели публикуют запросы покупателя (RFO), а продавцы отвечают офферами продавца.

Глоссарий:

- Запрос покупателя = RFO
- Оффер продавца = Offer

Поток:

- Покупатель публикует запрос -> продавцы отправляют офферы -> ранжирование возвращает лучшие офферы.

UI использует те же API эндпоинты, что и автоматизация.

## Аппаратные закупки

IntentBid развивается как продукт для срочных B2B закупок дефицитных вычислительных компонентов, где поставки фрагментированы, а котировки приходят медленно.

- Проблема: дефицит GPU, памяти и enterprise SSD приводит к фрагментированным и медленным котировкам у дистрибьюторов и брокеров.
- Поддерживаемые категории: `gpu`, `memory`, `ssd`, `nic`.
- Обещание по циклу сделки: котировки за часы, решение по награждению за день.
- Почему IntentBid отличается: прозрачный скоринг с explain, outbox webhooks, Python SDK и контролируемые лимиты планов.
- Целевая аудитория:
  - Покупатели: AI стартапы, лаборатории, SMB дата-центры, интеграторы, MSP с срочными потребностями в GPU/памяти/SSD.
  - Продавцы: авторизованные дистрибьюторы и проверенные брокеры с наличием, сроками поставки и документами трассируемости.
- Чеклист пилота: `docs/pilot_checklist.md`.

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

Запуск всего одной командой (db + migrations + API):

```bash
./scripts/start_dashboard.sh
```

Или вручную:

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

## Гид по автоматизации для роботов и агентов

Автоматизируйте поток через HTTP или SDK. Типичный сценарий: list requests, submit offers, fetch rankings.

HTTP (curl):

```bash
curl "http://localhost:8000/v1/rfo?status=OPEN&limit=5"
curl -X POST http://localhost:8000/v1/offers \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <api_key>" \
  -d '{"rfo_id": 1, "price_amount": 109.99, "currency": "USD", "delivery_eta_days": 2}'
curl http://localhost:8000/v1/buyers/rfo/1/ranking -H "X-Buyer-API-Key: <buyer_key>"
```

SDK (Python):

```python
from intentbid.sdk import IntentBidClient

client = IntentBidClient(base_url="http://localhost:8000", api_key="<vendor_key>")
rfos = client.list_rfos(status="OPEN", limit=5)
client.submit_offer({"rfo_id": 1, "price_amount": 109.99, "currency": "USD", "delivery_eta_days": 2})

buyer = client.register_buyer("Demo Buyer")
ranking = client.get_buyer_ranking(1, buyer["api_key"])
```

Лимиты: ограничители офферов задаются `settings.max_offers_per_vendor_rfo` и
`settings.offer_cooldown_seconds` из `intentbid.app.core.config`; месячные лимиты тарифов контролируются
`PlanLimit` и возвращают `429 Plan limit exceeded`, когда лимит исчерпан.

## Доступ и онбординг

- `POST /v1/vendors/keys` создает новый API-ключ для текущего продавца; сырый ключ возвращается один раз, а в базе сохраняется хеш и обновляется `last_used_at`.
- `POST /v1/vendors/keys/{key_id}/revoke` переводит ключ в статус `revoked` и фиксирует `revoked_at`, чтобы новые токены переключались без влияния на другие.
- `POST /v1/vendors/webhooks` регистрирует webhook для событий `rfo.created`, `offer.created`, `rfo.closed`, `rfo.awarded`, а `EventOutbox` обрабатывает ретраи, backoff и обновление `last_delivery_at` даже при временных отказах доставки.
- `GET /v1/vendors/onboarding/status` показывает, есть ли у продавца активный API-ключ и webhook, чтобы UI мог подсказать следующий шаг.

## Доступ покупателей и ранжирование

- `POST /v1/buyers/register` выдает buyer-ключ, который нужно передавать в заголовке `X-Buyer-API-Key`.
- `GET /v1/buyers/me` позволяет покупателям проверять свою сущность, аналогично `/v1/vendors/me`.
- `GET /v1/buyers/rfo/{rfo_id}/ranking` возвращает все офферы по RFO вместе с `score` и `explain`, чтобы покупатель видел, как формируется ранжирование.

## Жизненный цикл RFO и скоринг

- Статусы RFO идут по цепочке `OPEN -> CLOSED -> AWARDED` через отдельные эндпоинты `/close`, `/award` и `/reopen`. Валидация допускает только корректные переходы, а каждый переход логируется в `audit_log` с указанием причины.
- `/v1/rfo/{id}/scoring` позволяет назначать `scoring_version` и веса по компонентам (например, `w_price`), чтобы настройка однозначно фиксировалась и была обратимой.
- `/v1/rfo/{id}/ranking/explain` отдает выбранную `scoring_version`, разбивку по компонентам и активные штрафы, поэтому решение легко сверить и отладить.

## Валидация и биллинг

- Отправка оффера проверяет `price_amount`, `delivery_eta_days`, а также гарантии и сроки возврата; валидация дополнительно следит за `max_offers_per_vendor_rfo` и `offer_cooldown_seconds`, которые настраиваются через `.env` (`intentbid.app.core.config.settings`).
- Поставщики подписаны на `Subscription`, у каждой подписки есть `PlanLimit`. Если в текущем месяце уже исчерпан лимит, запрос возвращает `429 Plan limit exceeded`, а создание оффера фиксируется как `UsageEvent`.

## Уведомления и webhook

- `enqueue_event` пишет подписанные события `rfo.created`, `offer.created`, `rfo.closed`, `rfo.awarded` в `EventOutbox`; `dispatch_outbox` (например, из фонового worker-а) забирает pending события, подписывает данные секретом webhook-а и пытается доставить повторно с backoff, прежде чем пометить как доставленное или dead-letter.
- В заголовке `X-IntentBid-Signature` передается подпись содержимого, чтобы получатель мог проверить целостность, а продавец видит обновления `last_delivery_at` по каждому webhook-у.

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

### Ссылки на панели

- Вход (английская панель): [http://localhost:8000/dashboard/login](http://localhost:8000/dashboard/login)
- Список RFO (английская панель): [http://localhost:8000/dashboard/rfos](http://localhost:8000/dashboard/rfos)
- Детали RFO + отправка (английская панель): [http://localhost:8000/dashboard/rfos/<id>](http://localhost:8000/dashboard/rfos/<id>)
- Мои офферы (английская панель): [http://localhost:8000/dashboard/offers](http://localhost:8000/dashboard/offers)
- Вход (русская панель): [http://localhost:8000/ru/dashboard/login](http://localhost:8000/ru/dashboard/login)
- Список RFO (русская панель): [http://localhost:8000/ru/dashboard/rfos](http://localhost:8000/ru/dashboard/rfos)
- Детали RFO + отправка (русская панель): [http://localhost:8000/ru/dashboard/rfos/<id>](http://localhost:8000/ru/dashboard/rfos/<id>)
- Мои офферы (русская панель): [http://localhost:8000/ru/dashboard/offers](http://localhost:8000/ru/dashboard/offers)

Можно также передать `?api_key=...` в `/dashboard/rfos` для прямой ссылки; для удобства ключ сохраняется в cookie.

### Панель покупателя (UI)

- Создание RFO: [http://localhost:8000/buyer/rfos/new](http://localhost:8000/buyer/rfos/new)
- Проверка RFO: [http://localhost:8000/buyer/rfos/check](http://localhost:8000/buyer/rfos/check)
- Лучшие офферы: [http://localhost:8000/buyer/rfos/best](http://localhost:8000/buyer/rfos/best)
- Скоринг покупателя: [http://localhost:8000/buyer/rfos/scoring](http://localhost:8000/buyer/rfos/scoring)

### Панель покупателя (API)

- Регистрация покупателя: `POST /v1/buyers/register` (возвращает ключ покупателя)
- Подтверждение идентичности: `GET /v1/buyers/me` с `X-Buyer-API-Key`
- Протокол ранжирования: `GET /v1/buyers/rfo/{id}/ranking` для просмотра всех офферов вместе с `explain`

### Справочник API (английская панель)

После входа через `/dashboard/login` перейдите на `/dashboard/apis`. Эта страница показывает карточки для каждого API-запроса, а поткликая по карточке вы попадете на `/dashboard/apis/<slug>` — там указаны HTTP-метод, маршрут, авторизация, пример curl и примечания.

- `POST /v1/vendors/register` — регистрация продавца → `/dashboard/apis/vendor-registration`
- `POST /v1/vendors/keys` — новые ключи → `/dashboard/apis/vendor-keys`
- `POST /v1/vendors/keys/{key_id}/revoke` — отзыв ключа → `/dashboard/apis/vendor-revoke-key`
- `POST /v1/vendors/webhooks` — регистрация webhook → `/dashboard/apis/vendor-webhooks`
- `GET /v1/vendors/onboarding/status` — статус онбординга → `/dashboard/apis/vendor-onboarding`
- `GET /v1/vendors/me` — профиль продавца → `/dashboard/apis/vendor-me`
- `POST /v1/buyers/register` — регистрация покупателя → `/dashboard/apis/buyer-registration`
- `GET /v1/buyers/me` — профиль покупателя → `/dashboard/apis/buyer-me`
- `GET /v1/buyers/rfo/{rfo_id}/ranking` — ранжирование → `/dashboard/apis/buyer-ranking`
- `POST /v1/rfo` — создание RFO → `/dashboard/apis/rfo-create`
- `GET /v1/rfo/{id}` — детали RFO → `/dashboard/apis/rfo-detail`
- `GET /v1/rfo/{id}/best` — лучшие офферы → `/dashboard/apis/rfo-best`
- `POST /v1/offers` — отправить оффер → `/dashboard/apis/offer-create`
- `POST /v1/rfo/{id}/close` — закрыть RFO → `/dashboard/apis/rfo-close`
- `POST /v1/rfo/{id}/award` — выбрать победителя → `/dashboard/apis/rfo-award`
- `POST /v1/rfo/{id}/reopen` — повторно открыть → `/dashboard/apis/rfo-reopen`
- `POST /v1/rfo/{id}/scoring` — обновить скоринг → `/dashboard/apis/rfo-scoring`
- `GET /v1/rfo/{id}/ranking/explain` — explain ранжирования → `/dashboard/apis/rfo-ranking-explain`

### Справочник API (русская панель)

Тех же карточек ожидать на `/ru/dashboard/apis` после входа через `/ru/dashboard/login`. Доступны тот же набор эндпоинтов, но вся информация выводится на русском языке.

- `POST /v1/vendors/register` — регистрация продавца → `/ru/dashboard/apis/vendor-registration`
- `POST /v1/vendors/keys` — новые ключи → `/ru/dashboard/apis/vendor-keys`
- `POST /v1/vendors/keys/{key_id}/revoke` — отзыв ключа → `/ru/dashboard/apis/vendor-revoke-key`
- `POST /v1/vendors/webhooks` — регистрация webhook → `/ru/dashboard/apis/vendor-webhooks`
- `GET /v1/vendors/onboarding/status` — статус онбординга → `/ru/dashboard/apis/vendor-onboarding`
- `GET /v1/vendors/me` — профиль продавца → `/ru/dashboard/apis/vendor-me`
- `POST /v1/buyers/register` — регистрация покупателя → `/ru/dashboard/apis/buyer-registration`
- `GET /v1/buyers/me` — профиль покупателя → `/ru/dashboard/apis/buyer-me`
- `GET /v1/buyers/rfo/{rfo_id}/ranking` — ранжирование → `/ru/dashboard/apis/buyer-ranking`
- `POST /v1/rfo` — создание RFO → `/ru/dashboard/apis/rfo-create`
- `GET /v1/rfo/{id}` — детали RFO → `/ru/dashboard/apis/rfo-detail`
- `GET /v1/rfo/{id}/best` — лучшие офферы → `/ru/dashboard/apis/rfo-best`
- `POST /v1/offers` — отправить оффер → `/ru/dashboard/apis/offer-create`
- `POST /v1/rfo/{id}/close` — закрыть RFO → `/ru/dashboard/apis/rfo-close`
- `POST /v1/rfo/{id}/award` — выбрать победителя → `/ru/dashboard/apis/rfo-award`
- `POST /v1/rfo/{id}/reopen` — повторно открыть → `/ru/dashboard/apis/rfo-reopen`
- `POST /v1/rfo/{id}/scoring` — обновить скоринг → `/ru/dashboard/apis/rfo-scoring`
- `GET /v1/rfo/{id}/ranking/explain` — explain ранжирования → `/ru/dashboard/apis/rfo-ranking-explain`

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
