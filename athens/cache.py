"""In-memory TTL cache, per serverless instance.

- One loader runs per key at a time; concurrent requests wait for it instead of all hitting the city API.
- If a refresh fails and an older value exists, that value is served with stale=True instead of an error.
"""
import threading
import time

_store = {}
_locks = {}
_guard = threading.Lock()
MAX_ENTRIES = 500  # hard cap: expired entries go first, then the oldest
RETRY_S = 30       # after a failed refresh, serve stale this long before trying the city again


def cached(key, ttl, loader):
    """→ (value, {"fetched_at": epoch, "expires_at": epoch, "stale": bool})"""
    e = _store.get(key)
    if e and time.time() < e["exp"]:
        return e["value"], {"fetched_at": e["at"], "expires_at": e["exp"], "stale": False}
    with _guard:
        lock = _locks.setdefault(key, threading.Lock())
    with lock:
        e = _store.get(key)
        if e and time.time() < e["exp"]:
            return e["value"], {"fetched_at": e["at"], "expires_at": e["exp"], "stale": False}
        try:
            value = loader()
        except Exception:
            if e:  # back off: the next requests get the stale value at once instead of retrying a dead API
                e["exp"] = time.time() + min(ttl, RETRY_S)
                return e["value"], {"fetched_at": e["at"], "expires_at": e["exp"], "stale": True}
            raise
        now = time.time()
        _store[key] = {"value": value, "at": now, "exp": now + ttl}
        _evict(now)
        return value, {"fetched_at": now, "expires_at": now + ttl, "stale": False}


def _evict(now):
    if len(_store) <= MAX_ENTRIES:
        return
    with _guard:
        for k in [k for k, e in list(_store.items()) if e["exp"] < now]:
            _store.pop(k, None)
        for k in sorted(_store, key=lambda k: _store[k]["at"])[: max(0, len(_store) - MAX_ENTRIES)]:
            _store.pop(k, None)
        for k in [k for k in _locks if k not in _store and not _locks[k].locked()]:
            del _locks[k]


def status():
    """Counts only: which station histories were requested is nobody's business."""
    now, items = time.time(), dict(list(_store.items()))  # snapshot: other threads may be writing
    return {"entries": len(items), "expired": sum(1 for e in items.values() if e["exp"] < now),
            **{f"{k}_age_s": round(now - items[k]["at"]) for k in ("env", "wifi") if k in items}}


def clear():
    _store.clear()
