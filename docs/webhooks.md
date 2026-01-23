# Webhook Contract

## Event Types

- `rfo.created`
- `offer.created`
- `rfo.closed`
- `rfo.awarded`

## Payload Format

Every webhook delivery is JSON with the following envelope:

```json
{
  "event_type": "offer.created",
  "data": {
    "offer_id": 123,
    "rfo_id": 45,
    "vendor_id": 7
  }
}
```

## Signature Verification (Python)

```python
import hmac
import hashlib

raw_body = request.data  # raw bytes from your framework
signature = request.headers.get("X-IntentBid-Signature", "")
secret = WEBHOOK_SECRET  # from /v1/vendors/webhooks response

expected = hmac.new(
    secret.encode("utf-8"),
    raw_body,
    hashlib.sha256,
).hexdigest()

if not hmac.compare_digest(signature, expected):
    raise ValueError("invalid webhook signature")
```

## Retry Semantics

- Events are stored in `event_outbox` and delivered asynchronously.
- Failed deliveries are retried with backoff (up to 5 minutes between attempts).
- `last_delivery_at` on the webhook record updates after a successful delivery.
