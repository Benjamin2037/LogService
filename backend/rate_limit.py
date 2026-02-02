import time
from dataclasses import dataclass
from threading import Lock


@dataclass
class BucketState:
    tokens: float
    last: float


class TokenBucketLimiter:
    def __init__(self, rate_per_sec: float, burst: int) -> None:
        self.rate_per_sec = rate_per_sec
        self.burst = burst
        self._lock = Lock()
        self._buckets: dict[str, BucketState] = {}

    def allow(self, key: str) -> tuple[bool, float]:
        now = time.monotonic()
        with self._lock:
            state = self._buckets.get(key)
            if state is None:
                state = BucketState(tokens=float(self.burst), last=now)
                self._buckets[key] = state

            elapsed = now - state.last
            state.tokens = min(self.burst, state.tokens + elapsed * self.rate_per_sec)
            state.last = now

            if state.tokens >= 1:
                state.tokens -= 1
                return True, 0.0

            retry_after = (1 - state.tokens) / self.rate_per_sec if self.rate_per_sec > 0 else 1.0
            return False, max(retry_after, 0.0)
