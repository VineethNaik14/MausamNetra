import hashlib
import time
from collections import OrderedDict
from typing import Any


class TTLSeenCache:
    """Small in-memory duplicate cache for a streaming worker.

    This is an ingestion-level safeguard, not the project's final verification engine.
    Member 4 can perform richer cross-source verification later.
    """

    def __init__(self, ttl_seconds: int = 300, max_items: int = 10000):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._seen: OrderedDict[str, float] = OrderedDict()

    @staticmethod
    def fingerprint(report: dict[str, Any]) -> str:
        text = " ".join(str(report.get("text", "")).lower().split())
        key = "|".join([
            text,
            str(round(float(report.get("latitude", 0)), 4)),
            str(round(float(report.get("longitude", 0)), 4)),
            str(report.get("source", "")),
            str(report.get("timestamp", ""))[:16],
        ])
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def is_duplicate(self, report: dict[str, Any]) -> bool:
        now = time.time()
        self._purge(now)
        key = self.fingerprint(report)
        if key in self._seen:
            return True
        self._seen[key] = now
        self._seen.move_to_end(key)
        while len(self._seen) > self.max_items:
            self._seen.popitem(last=False)
        return False

    def _purge(self, now: float) -> None:
        cutoff = now - self.ttl_seconds
        expired = [key for key, timestamp in self._seen.items() if timestamp < cutoff]
        for key in expired:
            self._seen.pop(key, None)
