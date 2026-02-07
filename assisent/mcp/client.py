import time
import json
from urllib.parse import urljoin
import httpx
from .rate_limiter import TokenBucket
from .cache import TTLCacheLRU


class MCPClient:
    def __init__(self, registry, monitor):
        self.registry = registry
        self.monitor = monitor
        self.buckets = {}
        self.cache = TTLCacheLRU()

    def _bucket(self, service: str):
        b = self.buckets.get(service)
        if not b:
            b = TokenBucket(capacity=20, refill_per_second=10)
            self.buckets[service] = b
        return b

    async def call(self, service: str, path: str, method: str = "GET", payload=None, headers=None, timeout=10.0):
        method = method.upper()
        if not self._bucket(service).allow():
            return {"status": 429, "body": {"error": "rate_limited"}}
        cache_key = None
        if method == "GET":
            cache_key = json.dumps([service, path, headers], ensure_ascii=False)
            cached = self.cache.get(cache_key)
            if cached is not None:
                return {"status": 200, "body": cached}
        tried = 0
        max_tries = 3
        last_error = None
        while tried < max_tries:
            ep = self.registry.next_endpoint(service)
            if not ep:
                return {"status": 404, "body": {"error": "service_not_found"}}
            base = ep.get("url")
            if not base:
                return {"status": 502, "body": {"error": "invalid_endpoint"}}
            url = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
            t0 = time.time()
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    if method == "GET":
                        r = await client.get(url, headers=headers)
                    elif method == "POST":
                        r = await client.post(url, json=payload, headers=headers)
                    elif method == "PUT":
                        r = await client.put(url, json=payload, headers=headers)
                    elif method == "DELETE":
                        r = await client.delete(url, headers=headers)
                    else:
                        return {"status": 405, "body": {"error": "method_not_allowed"}}
                lat = (time.time() - t0) * 1000.0
                body = None
                try:
                    body = r.json()
                except Exception:
                    body = r.text
                self.monitor.record(service, base, path, method, r.status_code, lat)
                if r.status_code < 400 and cache_key is not None:
                    self.cache.set(cache_key, body)
                return {"status": r.status_code, "body": body}
            except Exception as e:
                last_error = str(e)
                lat = (time.time() - t0) * 1000.0
                self.monitor.record(service, base, path, method, 599, lat)
                tried += 1
        return {"status": 503, "body": {"error": "unavailable", "detail": last_error}}