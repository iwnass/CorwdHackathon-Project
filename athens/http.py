"""Shared plumbing for the Vercel Python handlers (BaseHTTPRequestHandler) and the local server."""
import json
import math
import sys
import time
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from .times import iso_utc

ROUTES = {}  # path → (fn, cache, method); used by scripts/serve.py
MAX_BODY = 16 * 1024
CACHE_CONTROL = "public, max-age=60, s-maxage=300, stale-while-revalidate=600"


class HttpError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def int_param(q, name, default=None, lo=None, hi=None):
    v = q.get(name)
    if v in (None, ""):
        return default
    try:
        n = int(v)
    except ValueError:
        raise HttpError(400, f"{name} must be an integer")
    if (lo is not None and n < lo) or (hi is not None and n > hi):
        raise HttpError(400, f"{name} must be between {lo} and {hi}")
    return n


def float_param(q, name, lo, hi):
    """Required float in [lo, hi]."""
    v = q.get(name)
    try:
        f = float(v)
    except (TypeError, ValueError):
        raise HttpError(400, f"{name} is required and must be a number")
    if not lo <= f <= hi:  # also rejects nan
        raise HttpError(400, f"{name} must be between {lo} and {hi}")
    return f


def with_meta(body, meta):
    """Adds where the data came from, how old it is, and two things the live map needs:
    - server_time_ms: the server's UTC clock when answering. The client syncs its clock with
      T_realtime = server_time_ms + Δt_network / 2 (Δt_network = measured round trip) and ticks locally from there.
    - next_refresh_s: when this data can change. wait = e_k − now, where e_k is when the cached copy expires
      (the brief's TTL formula, with the TTL of this dataset). Re-fetching earlier returns the same data.
    """
    now = time.time()
    fetched = datetime.fromtimestamp(meta["fetched_at"], timezone.utc)
    return {**body, "meta": {"source": "opendata.cityofathens.gr", "fetched_at": iso_utc(fetched), "stale": meta["stale"],
                             "server_time": datetime.fromtimestamp(now, timezone.utc).isoformat(timespec="milliseconds"),
                             "server_time_ms": int(now * 1000),
                             "next_refresh_s": max(1, math.ceil(meta["expires_at"] - now))}}


def respond(handler, status, body, cache=CACHE_CONTROL):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", cache if status == 200 else "no-store")
    handler.send_header("Access-Control-Allow-Origin", "*")  # public open data, read-only
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def run(fn, path):
    """fn(query) → (status, body). Never raises."""
    q = {k: v[0] for k, v in parse_qs(urlparse(path).query).items()}
    try:
        return 200, fn(q)
    except HttpError as e:
        return e.status, {"error": str(e)}
    except Exception as e:  # city API down and nothing cached
        traceback.print_exc(file=sys.stderr)
        return 502, {"error": f"upstream unavailable: {type(e).__name__}"}


def read_json(handler):
    """The request body as a JSON object; 413/400 on oversize or bad JSON."""
    try:
        n = int(handler.headers.get("Content-Length") or 0)
    except ValueError:
        raise HttpError(400, "bad Content-Length")
    if n > MAX_BODY:
        raise HttpError(413, f"body larger than {MAX_BODY} bytes")
    try:
        body = json.loads(handler.rfile.read(n) or b"{}")
    except ValueError:
        raise HttpError(400, "body must be JSON")
    if not isinstance(body, dict):
        raise HttpError(400, "body must be a JSON object")
    return body


def client_ip(handler):
    """The caller's IP. On Vercel the platform sets X-Forwarded-For (first entry = the client)."""
    fwd = (handler.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    return fwd or handler.client_address[0]


def preflight(handler):
    """CORS preflight: browsers send it before a cross-origin JSON POST."""
    handler.send_response(204)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Max-Age", "86400")
    handler.end_headers()


def make_handler(route, fn, cache=CACHE_CONTROL, method="GET"):
    """GET: fn(query). POST: fn(query, json_body, client_ip)."""
    ROUTES[route] = (fn, cache, method)

    class handler(BaseHTTPRequestHandler):
        if method == "POST":
            def do_POST(self):
                respond(self, *run(lambda q: fn(q, read_json(self), client_ip(self)), self.path), cache)

            def do_OPTIONS(self):
                preflight(self)
        else:
            def do_GET(self):
                respond(self, *run(fn, self.path), cache)

    return handler
