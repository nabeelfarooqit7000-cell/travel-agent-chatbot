from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone


class AdminRateLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._attempts: dict[str, list[datetime]] = {}

    def check(self, client_key: str, limit_per_minute: int) -> bool:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)
        with self._lock:
            attempts = self._attempts.get(client_key, [])
            attempts = [attempt for attempt in attempts if attempt >= window_start]
            if len(attempts) >= limit_per_minute:
                self._attempts[client_key] = attempts
                return False
            attempts.append(now)
            self._attempts[client_key] = attempts
        return True
