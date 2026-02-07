import time


class TokenBucket:
    def __init__(self, capacity: int, refill_per_second: float):
        self.capacity = float(capacity)
        self.refill = float(refill_per_second)
        self.tokens = float(capacity)
        self.last = time.time()

    def allow(self) -> bool:
        now = time.time()
        elapsed = now - self.last
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill)
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False