import time
from collections import deque, defaultdict


class Monitor:
    def __init__(self, max_logs: int = 1000):
        self.requests = defaultdict(int)
        self.errors = defaultdict(int)
        self.latency_sum = defaultdict(float)
        self.latency_count = defaultdict(int)
        self.logs = deque(maxlen=max_logs)

    def record(self, service: str, endpoint: str, path: str, method: str, status: int, latency_ms: float):
        self.requests[service] += 1
        if status >= 400:
            self.errors[service] += 1
        self.latency_sum[service] += latency_ms
        self.latency_count[service] += 1
        self.logs.append({
            "ts": int(time.time() * 1000),
            "service": service,
            "endpoint": endpoint,
            "path": path,
            "method": method,
            "status": status,
            "latency_ms": latency_ms,
        })

    def stats(self):
        out = {}
        for s in set(list(self.requests.keys()) + list(self.errors.keys())):
            cnt = self.requests.get(s, 0)
            err = self.errors.get(s, 0)
            lat_sum = self.latency_sum.get(s, 0.0)
            lat_cnt = self.latency_count.get(s, 0)
            avg = (lat_sum / lat_cnt) if lat_cnt else 0.0
            out[s] = {"requests": cnt, "errors": err, "avg_latency_ms": round(avg, 2)}
        return {"services": out, "recent": list(self.logs)}