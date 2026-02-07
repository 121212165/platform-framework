from collections import OrderedDict
import time
import json


class TTLCacheLRU:
    def __init__(self, max_items: int = 1000, ttl_seconds: int = 600, max_bytes: int = 5 * 1024 * 1024):
        self.store = OrderedDict()
        self.max_items = max_items
        self.ttl = ttl_seconds
        self.max_bytes = max_bytes
        self.bytes = 0

    def _size_of(self, value) -> int:
        try:
            return len(json.dumps(value, ensure_ascii=False))
        except Exception:
            return 0

    def get(self, key):
        now = time.time()
        item = self.store.get(key)
        if not item:
            return None
        expires_at, value, size = item
        if expires_at < now:
            try:
                del self.store[key]
                self.bytes -= size
            except Exception:
                pass
            return None
        self.store.move_to_end(key)
        return value

    def set(self, key, value):
        size = self._size_of(value)
        if size > 10 * 1024:
            value = str(value)[:10 * 1024]
            size = self._size_of(value)
        now = time.time()
        expires_at = now + self.ttl
        existing = self.store.get(key)
        if existing:
            _, _, old_size = existing
            self.bytes -= old_size
        self.store[key] = (expires_at, value, size)
        self.store.move_to_end(key)
        self.bytes += size
        while (len(self.store) > self.max_items) or (self.bytes > self.max_bytes):
            _, (_, _, s) = self.store.popitem(last=False)
            self.bytes -= s