"""Live crowds from the app's own users (opt-in), traffic-style.

The app pings POST /api/presence every ~2 min while open; GET /api/crowds returns how many users are in each
~220 m cell in the last 15 min. Privacy by design:
- the position is snapped to its cell; no coordinates are stored;
- the app's random session id is stored only hashed with the day, so a user can't be followed across days;
- everything expires after 15–30 min; a cell is shown only with ≥ MIN_COUNT users;
- IPs only as a hashed per-10-min ping counter (anti-abuse).
Storage: Upstash Redis REST (Vercel Marketplace sets KV_REST_API_URL / KV_REST_API_TOKEN), shared by all instances.
"""
import hashlib
import json
import math
import os
import re
import time
import urllib.error
import urllib.request

WINDOW_S = 15 * 60
CELL_LAT, CELL_LON = 0.002, 0.0025  # ≈ 220 m × 220 m in Athens
MIN_COUNT = int(os.environ.get("PRESENCE_MIN_COUNT", 3))  # never reveal a cell with 1–2 people
LEVELS = ((30, "crowd_high"), (10, "crowd_medium"), (0, "crowd_low"))  # app users in the cell
PINGS_PER_IP = int(os.environ.get("PRESENCE_PINGS_PER_IP", 60))  # per 10 min: a few phones behind one NAT
SESSION = re.compile(r"^[A-Za-z0-9-]{16,64}$")


class NotConfigured(Exception):
    pass


class RateLimited(Exception):
    pass


def http(url, headers, body):
    """The only function that touches the network; tests replace it."""
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


class MemoryStore:
    """The few Redis commands used here, in memory, for tests and the local dev server (PRESENCE_STORE=memory).
    Never use it on Vercel: each serverless instance would count only its own users."""

    def __init__(self):
        self.kv, self.z, self.exp = {}, {}, {}

    def _alive(self, k):
        if k in self.exp and self.exp[k] <= time.time():
            self.kv.pop(k, None), self.z.pop(k, None), self.exp.pop(k, None)

    def run(self, c):
        op, k = c[0].upper(), c[1]
        self._alive(k)
        f = lambda x: float(x.replace("inf", "Infinity"))  # noqa: E731
        if op == "INCR":
            self.kv[k] = str(int(self.kv.get(k, 0)) + 1)
            return int(self.kv[k])
        if op == "EXPIRE":
            self.exp[k] = time.time() + int(c[2])
            return 1
        if op == "SET":  # SET k v EX n GET
            old, self.kv[k] = self.kv.get(k), c[2]
            self.exp[k] = time.time() + int(c[4])
            return old
        z = self.z.setdefault(k, {})
        if op == "ZADD":
            z[c[3]] = float(c[2])
            return 1
        if op == "ZREM":
            return int(z.pop(c[2], None) is not None)
        if op == "ZREMRANGEBYSCORE":
            gone = [m for m, s in z.items() if f(c[2]) <= s <= f(c[3])]
            for m in gone:
                del z[m]
            return len(gone)
        if op == "ZRANGEBYSCORE":
            return [m for m, s in sorted(z.items(), key=lambda x: x[1]) if f(c[2]) <= s <= f(c[3])]
        if op == "ZCOUNT":
            return sum(1 for s in z.values() if f(c[2]) <= s <= f(c[3]))
        raise ValueError(op)


_memory = MemoryStore()


def redis(*commands, request=None):
    """Run Redis commands in one Upstash pipeline → their results."""
    if os.environ.get("PRESENCE_STORE") == "memory" and request is None:
        return [_memory.run([str(x) for x in c]) for c in commands]
    url, token = os.environ.get("KV_REST_API_URL", "").rstrip("/"), os.environ.get("KV_REST_API_TOKEN", "")
    if not url or not token:
        raise NotConfigured("KV_REST_API_URL / KV_REST_API_TOKEN are not set")
    body = json.dumps([[str(x) for x in c] for c in commands]).encode()
    try:
        out = (request or http)(f"{url}/pipeline", {"Authorization": f"Bearer {token}",
                                                     "Content-Type": "application/json"}, body)
    except urllib.error.HTTPError as e:  # `from None`: the request carries the token
        raise RuntimeError(f"presence store HTTP {e.code}") from None
    return [r.get("result") for r in out]


def _hash(*parts):
    return hashlib.sha256(":".join(parts).encode()).hexdigest()[:16]


def cell_of(lat, lon):
    return f"{math.floor(lat / CELL_LAT)}:{math.floor(lon / CELL_LON)}"


def cell_center(cell):
    i, j = (int(x) for x in cell.split(":"))
    return round((i + 0.5) * CELL_LAT, 6), round((j + 0.5) * CELL_LON, 6)


def ping(session, lat, lon, ip, now=None, request=None):
    """Record that this (anonymous) app user is in the cell of (lat, lon) now."""
    if not isinstance(session, str) or not SESSION.match(session):
        raise ValueError("session must be 16–64 letters, digits or '-'")
    now = now or time.time()
    ip_key = f"ip:{_hash(ip or '-')}:{int(now // 600)}"
    count, _ = redis(["INCR", ip_key], ["EXPIRE", ip_key, 600], request=request)
    if int(count) > PINGS_PER_IP:
        raise RateLimited("too many pings from this network, slow down")
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    user, cell = _hash(os.environ.get("PRESENCE_SALT", ""), day, session), cell_of(lat, lon)
    old, = redis(["SET", f"s:{user}", cell, "EX", WINDOW_S, "GET"], request=request)
    cmds = [["ZADD", f"c:{cell}", now, user], ["ZREMRANGEBYSCORE", f"c:{cell}", "-inf", now - WINDOW_S],
            ["EXPIRE", f"c:{cell}", 2 * WINDOW_S], ["ZADD", "cells", now, cell]]
    if old and old != cell:  # moved: count them in the new cell only
        cmds.append(["ZREM", f"c:{old}", user])
    redis(*cmds, request=request)
    return {"cell": cell, "window_s": WINDOW_S}


def crowds(now=None, request=None):
    """Every cell with ≥ MIN_COUNT app users in the last WINDOW_S: centre, size, count, level."""
    now = now or time.time()
    _, cells = redis(["ZREMRANGEBYSCORE", "cells", "-inf", now - WINDOW_S],
                     ["ZRANGEBYSCORE", "cells", now - WINDOW_S, "+inf"], request=request)
    cells = cells or []
    counts = redis(*[["ZCOUNT", f"c:{c}", now - WINDOW_S, "+inf"] for c in cells], request=request) if cells else []
    out = []
    for c, n in zip(cells, counts):
        n = int(n or 0)
        if n >= MIN_COUNT:
            lat, lon = cell_center(c)
            out.append({"cell": c, "lat": lat, "lon": lon, "size_m": 220,
                        "count": n if n < 10 else n // 10 * 10,  # "10+", "20+": no exact numbers for big crowds
                        "level": next(code for low, code in LEVELS if n >= low)})
    out.sort(key=lambda x: -x["count"])
    return {"window_min": WINDOW_S // 60, "min_count": MIN_COUNT, "cells": out}
