# Production Checklist

## Database

- Use Postgres in production (no SQLite).
- Run migrations before starting the API: `alembic upgrade head`.

## Security

- Set a strong `SECRET_KEY`.
- Set `require_https=true` behind your reverse proxy (ensure `X-Forwarded-Proto` is set).
- Configure `allow_insecure_webhooks=false` to require HTTPS webhook endpoints.
- Set `ADMIN_API_KEY` for admin-only vendor verification endpoints.

## Webhooks & Outbox

- Run `dispatch_outbox` as a background worker or cron.
- Monitor `event_outbox` for retries and failures.

## Observability

- Ensure structured logs are collected.
- Scrape `/metrics` for request counts.

## Rate Limiting

- Review `rate_limit_requests` and `rate_limit_window_seconds` for your traffic profile.

## Scaling

- Run multiple API instances behind a load balancer.
- Use a shared DB and centralized logging.
