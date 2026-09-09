"""
FedSanitize Auth — Login Rate Limiting
========================================
Minimal in-memory sliding-window limiter, keyed by client IP + the
username/client_id being attempted (so one bad actor can't lock out a
legitimate user sharing the same IP, e.g. behind NAT). Good enough to
blunt naive brute-force/credential-stuffing against a single-process
deployment. For multi-worker or multi-instance deployments, back this
with Redis (`INCR` + `EXPIRE`) instead.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, status

from .config import settings


class LoginRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._attempts: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)

    def check(self, key_ip: str, key_identity: str) -> None:
        """Raises HTTP 429 if the (ip, identity) pair has exceeded the attempt budget."""
        key = (key_ip, key_identity)
        now = time.monotonic()
        with self._lock:
            attempts = self._attempts[key]
            while attempts and now - attempts[0] > self.window_seconds:
                attempts.popleft()
            if len(attempts) >= self.max_attempts:
                retry_after = int(self.window_seconds - (now - attempts[0]))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts. Please wait before retrying.",
                    headers={"Retry-After": str(max(retry_after, 1))},
                )

    def record_failure(self, key_ip: str, key_identity: str) -> None:
        key = (key_ip, key_identity)
        with self._lock:
            self._attempts[key].append(time.monotonic())

    def record_success(self, key_ip: str, key_identity: str) -> None:
        key = (key_ip, key_identity)
        with self._lock:
            self._attempts.pop(key, None)


login_rate_limiter = LoginRateLimiter(
    max_attempts=settings.login_rate_limit_attempts,
    window_seconds=settings.login_rate_limit_window_seconds,
)
