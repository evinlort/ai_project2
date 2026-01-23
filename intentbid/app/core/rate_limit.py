import time
from collections import deque
from threading import Lock


class RateLimiter:
    def __init__(self) -> None:
        self._lock = Lock()
        self._buckets: dict[str, deque[float]] = {}

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        if limit <= 0:
            return True
        now = time.time()
        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            cutoff = now - window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


rate_limiter = RateLimiter()
