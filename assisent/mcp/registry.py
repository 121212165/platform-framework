import json
import os
from pathlib import Path
import itertools
import time
import httpx


class ServiceRegistry:
    def __init__(self):
        self.services = {}
        self.iters = {}
        self.load()

    def load(self):
        fp = Path("config/mcp_services.json")
        if fp.exists():
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        else:
            data = {}
        for name, cfg in data.items():
            endpoints = cfg.get("endpoints", [])
            self.services[name] = {"endpoints": endpoints, "meta": cfg.get("meta", {})}
            self.iters[name] = itertools.cycle(endpoints)

    def list(self):
        out = {}
        for name, cfg in self.services.items():
            out[name] = {"endpoints": cfg.get("endpoints", []), "meta": cfg.get("meta", {})}
        return out

    def next_endpoint(self, name: str):
        it = self.iters.get(name)
        if not it:
            return None
        try:
            return next(it)
        except Exception:
            return None

    async def health_scan(self, timeout=2.0):
        for name, cfg in self.services.items():
            eps = cfg.get("endpoints", [])
            for ep in eps:
                url = ep.get("url")
                hp = ep.get("health_path") or "/health"
                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        r = await client.get(url.rstrip("/") + hp)
                        ep["up"] = (r.status_code == 200)
                except Exception:
                    ep["up"] = False