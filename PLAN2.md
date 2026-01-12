# IntentBid — детализированный план (по WORK2.md)

## 0) Принципы и порядок работ
- Каждый блок начинается с тестов (pytest) и только потом реализация.
- Миграции БД идут маленькими шагами, с обратимой логикой.
- Новые фичи по возможности за флагами/конфигами.
- Логи/аудит не пишут секреты; ключи храним хэшами.

## 1) Безопасность и модель доступа (API keys v2)
- **Цель**: снизить риск утечек/злоупотреблений и подготовить пилот.
- **Данные**: `vendor_api_keys` (id, vendor_id, hashed_key, status, scopes, last_used_at, created_at, revoked_at), `vendor_key_ip_allowlist` (key_id, ip_cidr).
- **API/поведение**:
  - `POST /v1/vendors/{id}/keys` (create) + `POST /v1/vendors/{id}/keys/{key_id}/revoke`.
  - Поддержка нескольких активных ключей, ротация, last_used_at.
  - Auth middleware валидирует scope, IP allowlist, rate limit.
- **UI/операции**: экран управления ключами в dashboard, просмотр last_used_at.
- **Тесты (сначала)**: создание/отзыв/ротация ключей, проверка scope, IP allowlist, rate limit, логи `vendor_id/key_id`.
- **Acceptance**: ключи создаются/отзываются через API и UI, логи и тесты покрывают revoke/rotate.

## 2) Жизненный цикл RFO (state machine) + аудит
- **Цель**: предсказуемое поведение сделок.
- **Данные**: `rfo.status`, `rfo.status_reason`, `rfo.deleted_at` (soft delete); `audit_log` (actor, action, target, payload, created_at).
- **API/поведение**:
  - Статусы `OPEN -> CLOSED -> AWARDED -> EXPIRED`, явные переходы.
  - Endpoints `POST /rfo/{id}/close`, `/award`, `/reopen` (если разрешено).
  - Идемпотентность для close/award (idempotency_key).
- **UI/операции**: история изменений статуса и действий.
- **Тесты (сначала)**: запрет офферов для CLOSED/EXPIRED, audit trail, идемпотентность.
- **Acceptance**: офферы нельзя отправлять на CLOSED/EXPIRED, есть audit trail.

## 3) Buyer/Agent API
- **Цель**: открыть buyer-интеграции и разделить доступ.
- **Данные**: `buyers`, `buyer_api_keys` (hashed_key, status), привязка к RFO.
- **API/поведение**:
  - `POST /v1/buyers/register`, buyer-auth header.
  - Политики доступа: vendor видит свои офферы, buyer — полный ranking.
  - Optional: public RFO view по secure token.
- **UI/операции**: регистрация buyer, ключи, список RFO.
- **Тесты (сначала)**: доступы vendor/buyer, публичный токен, ограничение данных.
- **Acceptance**: buyer API работает, политика доступа описана и покрыта тестами.

## 4) Конфигурируемый скоринг (per-RFO weights + версия)
- **Цель**: управляемый скоринг без деплоя.
- **Данные**: `rfo.weights`/`preference_profile`, `rfo.scoring_version`, `scoring_configs`.
- **API/поведение**:
  - Endpoint обновления веса для RFO.
  - Ranking включает `score`, `components`, `penalties`, `scoring_version`.
  - `GET /rfo/{id}/ranking/explain` (raw explain).
- **UI/операции**: UI для настройки веса, просмотр explain.
- **Тесты (сначала)**: стабильность результатов при фиксированном version, корректность explain.
- **Acceptance**: одинаковые офферы → одинаковый результат при одной версии.

## 5) Валидация и анти-спам/анти-гейминг
- **Цель**: защита от мусора и попыток манипуляций.
- **Данные**: лимиты per vendor/RFO, флаги `suspicious`, `cooldown_until`.
- **API/поведение**:
  - Ограничения частоты и количества офферов.
  - Валидация диапазонов, ETA, подтверждение наличия.
  - Возврат 429/400 с подробным reason.
- **UI/операции**: отображение причин отклонения, flags в dashboard.
- **Тесты (сначала)**: спам → 429/400, cooldown, suspicious флаги.
- **Acceptance**: нагрузочные тесты показывают корректные ответы.

## 6) Уведомления и realtime-каналы
- **Цель**: ускорить реакцию vendor.
- **Данные**: таблица outbox/events, `vendor_webhooks` (url, secret, status).
- **API/поведение**:
  - Регистрация webhook и подпись payload.
  - Ретраи с backoff, dead-letter для фейлов.
  - Email слой (stub или провайдер).
- **UI/операции**: управление webhook, просмотр последней доставки.
- **Тесты (сначала)**: подпись, ретраи, событие на RFO/offer.
- **Acceptance**: webhook работает, ретраи и подпись есть.

## 7) Платежный слой (MVP billing)
- **Цель**: подготовить монетизацию без вмешательства в core flow.
- **Данные**: `billing_accounts`, `subscriptions`, `usage_events`, `plan_limits`.
- **API/поведение**:
  - Stripe интеграция (webhooks), win fee как usage event.
  - Middleware enforcing quotas по плану.
- **UI/операции**: Billing страница с лимитами/статусом.
- **Тесты (сначала)**: лимиты, win event → usage, обработка webhook.
- **Acceptance**: лимиты enforced, Billing страница отражает статус.

## 8) Наблюдаемость
- **Цель**: диагностика на пилоте.
- **Данные/инфра**: Prometheus + (опц.) Grafana, OTel tracing.
- **API/поведение**:
  - Метрики latency/errors/offers/rfo/win-rate.
  - Correlation-id в логах, JSON логи с redaction.
- **UI/операции**: базовый dashboard.
- **Тесты (сначала)**: smoke-test метрик и трассировки.
- **Acceptance**: docker-compose поднимает стек, базовый dashboard доступен.

## 9) Production-ready деплой
- **Цель**: стабильный релиз и миграции.
- **Данные/инфра**: GitHub Actions, env разделение, health/readiness.
- **API/поведение**:
  - CI: lint/typecheck/test/build image + migration check.
  - One-command deploy на staging.
- **Тесты (сначала)**: CI пайплайн на PR, smoke test.
- **Acceptance**: деплой и миграции проходят автоматом.

## 10) Offer Exchange готовность
- **Цель**: быстрый онбординг SMB-вендоров.
- **Данные**: `vendor_catalog`, capability profile, sandbox tokens.
- **API/поведение**:
  - SDK, Postman, sandbox RFO/offer flow.
  - Vendor onboarding wizard (key → webhook → test call → live).
- **UI/операции**: onboarding в dashboard, публичная страница интеграции.
- **Тесты (сначала)**: sandbox flow, onboarding шаги.
- **Acceptance**: новый vendor интегрируется ≤30 минут по инструкции.

