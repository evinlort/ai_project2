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
