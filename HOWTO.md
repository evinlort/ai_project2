# HOWTO

## User (buyer) walkthrough

### Step-by-step
1. Start the service (Docker or local).
   - What you will see: the API at `http://localhost:8000`, OpenAPI docs at `/docs`, and `/health` returning `{"status":"ok"}`.
2. Create an RFO with `POST /v1/rfo`.
   - What you will see: a response with `rfo_id` and `status` (usually `OPEN`).
3. Inspect the RFO with `GET /v1/rfo/{id}`.
   - What you will see: `id`, `category`, `constraints`, `preferences`, `status`, `created_at`, and `offers_count`.
4. Review best offers with `GET /v1/rfo/{id}/best?top_k=3`.
   - What you will see: `top_offers` entries with `vendor_id`, `score`, `explain`, and offer fields like `price_amount`, `currency`, `delivery_eta_days`, `warranty_months`, `return_days`, `stock`, `metadata`, `created_at`.
5. Choose the winning offer based on the scores.
   - What you will see: scores and winners update as new offers arrive.

### Dashboard views
- There is no buyer dashboard. The only web UI is the vendor dashboard described below.

## Vendor walkthrough

### Step-by-step
1. Register with `POST /v1/vendors/register` and store the API key.
   - What you will see: `vendor_id` and a one-time `api_key` in the response.
2. Open the vendor login page at `/dashboard/login` (Russian UI: `/ru/dashboard/login`).
   - What you will see: an API key field and an error message for invalid keys; on success the key is stored in a cookie.
3. Browse open RFOs at `/dashboard/rfos` (or add `?api_key=...`).
   - What you will see: cards for each OPEN RFO with the ID, category, created date, and budget max; if you are not logged in you are redirected to the login page.
4. Open an RFO detail page and submit an offer.
   - What you will see: the RFO status, constraints, and preferences; a form for price, currency, delivery ETA, warranty months, return days, and stock; after submit you return to the same page.
5. Track results on `/dashboard/offers`.
   - What you will see: a table of your offers with score and a `won` or `lost` status per RFO.

### Dashboard views explained
- Login: used to enter the API key; shows a validation error if the key is incorrect.
- Open requests for offer: lists OPEN RFOs; each card shows the RFO number, category, created date, and budget max with a link to details.
- RFO detail: shows the RFO header (id, category, status, constraints, preferences), the "Submit an offer" form, and the "Existing offers" table with ID, price, ETA, warranty, and stock for all offers on that RFO.
- My offers: shows your offers with RFO id, price, ETA, warranty, score, and status; `won` means the highest score for that RFO among current offers, `lost` means lower than the current best.

## Extended workflows

- Rotate vendor API keys with `POST /v1/vendors/keys` and retire individual keys through `POST /v1/vendors/keys/{key_id}/revoke`; `GET /v1/vendors/onboarding/status` reports which onboarding steps (API key, webhook) are complete.
- Register webhook callbacks via `POST /v1/vendors/webhooks` and run `dispatch_outbox` from a worker/cron so signed `offer.created` events reach registered URLs with the `X-IntentBid-Signature` header.
- Buyers `POST /v1/buyers/register` and include that key in `X-Buyer-API-Key` to call `GET /v1/buyers/rfo/{rfo_id}/ranking`, receiving every offer once again with `score` and `explain`.
- Manage RFO states with `/v1/rfo/{id}/close`, `/award`, `/reopen` (each transition writes to `audit_log`), tune per-RFO `weights` and `scoring_version` via `/v1/rfo/{id}/scoring`, and examine the breakdown with `/v1/rfo/{rfo_id}/ranking/explain`.
- Offer validation keeps `price_amount`, `delivery_eta_days`, warranty, and return days in range while enforcing `max_offers_per_vendor_rfo`/`offer_cooldown_seconds` (configured via `intentbid.app.core.config.settings`) and monthly plan caps driven by `PlanLimit`/`Subscription` with each offer recording a `UsageEvent`.

## Project setup

### Tech stack & layout
- FastAPI + SQLModel drive the API layer (`intentbid/app/main.py`, `intentbid/app/api/*`) while Alembic keeps the DB schema in sync (`intentbid/app/db/migrations`).
- Jinja2 templates power the vendor dashboard, scoring logic lives in `intentbid/app/core/scoring.py`, and models (Vendor/RFO/Offer) sit in `intentbid/app/db/models.py`.
- Utility scripts such as `intentbid/scripts/seed_demo.py` and `intentbid/scripts/vendor_simulator.py` help populate demo data and exercise the service.

### Quick start (Docker + Postgres)
- Run `./scripts/start_dashboard.sh` to bring up Postgres, migrations, and the API in one go.
- Alternatively, `docker-compose up --build` boots the stack, then `docker-compose run --rm api alembic upgrade head` creates the tables.
- API: `http://localhost:8000`; docs: `http://localhost:8000/docs`; Postgres: `localhost:15432` (user/password/db `intentbid`).

### Local development (SQLite)
- Install dependencies with `pip install -e .`, apply migrations via `alembic upgrade head`, and start the API with `uvicorn intentbid.app.main:app --reload`.
- The default SQLite file is `intentbid.db` in the repo root unless `DATABASE_URL` overrides it.

### Configuration & scripts
- `DATABASE_URL` (default `sqlite:///./intentbid.db`), `SECRET_KEY` (hashes API keys), and `ENV` (`dev` enables SQL echo) control the runtime.
- Seed demo vendors, RFOs, and offers with `python intentbid/scripts/seed_demo.py` (also writes `scripts/demo_vendors.json`).
- Simulate vendors posting offers via `python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3` (also available through `docker-compose run --rm api`).

### Testing
- Install dev dependencies with `pip install ".[dev]"` and run `pytest` to exercise the API and scoring suites.

---

# HOWTO

## Руководство для пользователя (покупателя)

### Пошагово
1. Запустите сервис (Docker или локально).
   - Что вы увидите: API по адресу `http://localhost:8000`, OpenAPI по пути `/docs`, а `/health` возвращает `{"status":"ok"}`.
2. Создайте RFO через `POST /v1/rfo`.
   - Что вы увидите: ответ с `rfo_id` и `status` (обычно `OPEN`).
3. Проверьте RFO через `GET /v1/rfo/{id}`.
   - Что вы увидите: `id`, `category`, `constraints`, `preferences`, `status`, `created_at` и `offers_count`.
4. Посмотрите лучшие офферы через `GET /v1/rfo/{id}/best?top_k=3`.
   - Что вы увидите: элементы `top_offers` с `vendor_id`, `score`, `explain` и полями оффера вроде `price_amount`, `currency`, `delivery_eta_days`, `warranty_months`, `return_days`, `stock`, `metadata`, `created_at`.
5. Выберите победителя по скорингу.
   - Что вы увидите: очки и победители обновляются по мере поступления новых офферов.

### Представления панели
- Отдельной панели для покупателя нет. Единственный веб-интерфейс - панель продавца, она описана ниже.

## Руководство для продавца

### Пошагово
1. Зарегистрируйтесь через `POST /v1/vendors/register` и сохраните API-ключ.
   - Что вы увидите: `vendor_id` и одноразовый `api_key` в ответе.
2. Откройте страницу входа `/dashboard/login` (русский UI: `/ru/dashboard/login`).
   - Что вы увидите: поле для API-ключа и сообщение об ошибке при неверном ключе; при успехе ключ сохраняется в cookie.
3. Откройте список открытых RFO по адресу `/dashboard/rfos` (или добавьте `?api_key=...`).
   - Что вы увидите: карточки всех RFO со статусом OPEN с ID, категорией, датой создания и максимальным бюджетом; без входа произойдет редирект на страницу логина.
4. Откройте страницу RFO и отправьте оффер.
   - Что вы увидите: статус RFO, constraints и preferences; форму для цены, валюты, срока доставки, гарантии, срока возврата и наличия; после отправки вы вернетесь на эту же страницу.
5. Отслеживайте результат на `/dashboard/offers`.
   - Что вы увидите: таблицу своих офферов со скором и статусом `won` или `lost` для каждого RFO.

### Что означают страницы панели
- Вход: ввод API-ключа; показывает ошибку при неверном ключе.
- Открытые RFO: список RFO со статусом OPEN; карточка показывает номер RFO, категорию, дату создания и максимальный бюджет, есть ссылка на детали.
- Детали RFO: заголовок RFO (id, category, status, constraints, preferences), форма "Submit an offer" и таблица "Existing offers" с ID, ценой, ETA, гарантией и наличием для всех офферов по этому RFO.
- Мои офферы: таблица с RFO id, ценой, ETA, гарантией, скором и статусом; `won` означает лучший скор по этому RFO среди текущих офферов, `lost` означает более низкий скор.

## Расширенные сценарии

- Ротация API-ключей продавца через `POST /v1/vendors/keys` и отзыв отдельных ключей через `POST /v1/vendors/keys/{key_id}/revoke`; `GET /v1/vendors/onboarding/status` показывает, какие шаги (API-ключ, webhook) уже завершены.
- Регистрируйте webhook-ы через `POST /v1/vendors/webhooks` и запускайте `dispatch_outbox` из фонового воркера/cron, чтобы подписанные события `offer.created` приходили на адреса с заголовком `X-IntentBid-Signature`.
- Покупатели вызывают `POST /v1/buyers/register` и передают выдаваемый ключ в `X-Buyer-API-Key`, затем получают `GET /v1/buyers/rfo/{rfo_id}/ranking`, где снова видны все офферы с `score` и `explain`.
- Управляйте статусами RFO через `/v1/rfo/{id}/close`, `/award`, `/reopen` (каждый переход пишется в `audit_log`), настраивайте `weights`/`scoring_version` через `/v1/rfo/{id}/scoring` и смотрите разбор через `/v1/rfo/{rfo_id}/ranking/explain`.
- Валидация офферов проверяет `price_amount`, `delivery_eta_days`, гарантию и возврат, соблюдает `max_offers_per_vendor_rfo`/`offer_cooldown_seconds` из `intentbid.app.core.config.settings` и месячные лимиты из `PlanLimit`/`Subscription`, при этом каждый оффер записывается как `UsageEvent`.

## Настройка проекта

### Стек и структура
- FastAPI + SQLModel строят API (`intentbid/app/main.py`, `intentbid/app/api/*`), миграции обрабатываются Alembic (`intentbid/app/db/migrations`).
- Панель продавца реализована на Jinja2, логика скоринга — в `intentbid/app/core/scoring.py`, модели (Vendor/RFO/Offer) — в `intentbid/app/db/models.py`.
- Вспомогательные скрипты `intentbid/scripts/seed_demo.py` и `intentbid/scripts/vendor_simulator.py` заполняют демо-данные и моделируют поведение продавцов.

### Быстрый старт (Docker + Postgres)
- С помощью `./scripts/start_dashboard.sh` поднимаются Postgres, миграции и API одновременно.
- Или `docker-compose up --build` + `docker-compose run --rm api alembic upgrade head` для ручного запуска.
- API: `http://localhost:8000`, документация: `http://localhost:8000/docs`, Postgres: `localhost:15432` (user/password/db `intentbid`).

### Локальная разработка (SQLite)
- Установите зависимости `pip install -e .`, примените миграции `alembic upgrade head`, запустите сервис `uvicorn intentbid.app.main:app --reload`.
- SQLite-файл по умолчанию — `intentbid.db` в корне репозитория, если `DATABASE_URL` не переопределён.

### Конфигурация и скрипты
- Переменные `DATABASE_URL` (по умолчанию `sqlite:///./intentbid.db`), `SECRET_KEY` (хеширует API-ключи) и `ENV` (`dev` включает SQL echo) управляют окружением.
- Заполните демо-данные `python intentbid/scripts/seed_demo.py` (создаёт `scripts/demo_vendors.json`).
- Промоделируйте отправку офферов `python intentbid/scripts/vendor_simulator.py --api-url http://localhost:8000 --mode mixed --limit 3` (можно запускать через `docker-compose run --rm api`).

### Тесты
- Установите dev-зависимости `pip install ".[dev]"` и запустите `pytest`, чтобы проверить API и логики скоринга.
