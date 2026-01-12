import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from sqlmodel import Session, select

from intentbid.app.db.models import EventOutbox, VendorWebhook


def register_vendor_webhook(session: Session, vendor_id: int, url: str) -> VendorWebhook:
    secret = secrets.token_urlsafe(32)
    webhook = VendorWebhook(vendor_id=vendor_id, url=url, secret=secret, is_active=True)
    session.add(webhook)
    session.commit()
    session.refresh(webhook)
    return webhook


def enqueue_event(
    session: Session,
    vendor_id: int,
    event_type: str,
    payload: dict,
) -> EventOutbox:
    event = EventOutbox(
        vendor_id=vendor_id,
        event_type=event_type,
        payload=payload,
        status="pending",
        attempts=0,
        next_attempt_at=datetime.now(timezone.utc),
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def _serialize_payload(event: EventOutbox) -> str:
    envelope = {"event_type": event.event_type, "data": event.payload}
    return json.dumps(envelope, separators=(",", ":"), sort_keys=True)


def _sign_payload(secret: str, payload: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), "sha256").hexdigest()


def dispatch_outbox(
    session: Session,
    client: httpx.Client,
    *,
    max_attempts: int = 3,
    now: datetime | None = None,
) -> int:
    current_time = now or datetime.now(timezone.utc)
    events = session.exec(
        select(EventOutbox).where(
            EventOutbox.status == "pending",
            EventOutbox.attempts < max_attempts,
        )
    ).all()
    delivered = 0

    for event in events:
        if event.next_attempt_at:
            next_attempt_at = event.next_attempt_at
            if next_attempt_at.tzinfo is None:
                next_attempt_at = next_attempt_at.replace(tzinfo=timezone.utc)
            if next_attempt_at > current_time:
                continue
        webhooks = session.exec(
            select(VendorWebhook).where(
                VendorWebhook.vendor_id == event.vendor_id,
                VendorWebhook.is_active.is_(True),
            )
        ).all()
        if not webhooks:
            continue

        payload = _serialize_payload(event)
        success = True
        last_error = None
        for webhook in webhooks:
            signature = _sign_payload(webhook.secret, payload)
            try:
                response = client.post(
                    webhook.url,
                    content=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-IntentBid-Signature": signature,
                    },
                    timeout=5.0,
                )
                if response.status_code >= 400:
                    success = False
                    last_error = f"status_{response.status_code}"
            except httpx.HTTPError as exc:
                success = False
                last_error = str(exc)

        event.attempts += 1
        if success:
            event.status = "delivered"
            event.delivered_at = datetime.now(timezone.utc)
            delivered += 1
            for webhook in webhooks:
                webhook.last_delivery_at = event.delivered_at
                session.add(webhook)
        else:
            event.status = "pending"
            event.last_error = last_error
            backoff_seconds = min(60 * event.attempts, 300)
            event.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
        session.add(event)
        session.commit()

    return delivered
