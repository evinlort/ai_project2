import hashlib
import hmac
import secrets

from intentbid.app.core.config import settings


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_api_key(raw_key: str) -> str:
    digest = hmac.new(
        settings.secret_key.encode("utf-8"),
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest


def verify_api_key(raw_key: str, hashed_key: str) -> bool:
    expected = hash_api_key(raw_key)
    return hmac.compare_digest(expected, hashed_key)
