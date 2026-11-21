"""Local dev server with the same routes as Vercel, no Vercel CLI needed.
Reads .env.local (like `vercel dev`). Usage: python3 scripts/serve.py [port]      (default 8000)
"""
import importlib.util
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

env_file = os.path.join(ROOT, ".env.local")
if os.path.exists(env_file):
    for line in open(env_file, encoding="utf-8"):
        k, sep, v = line.strip().partition("=")
        if sep and k and not k.startswith("#"):
            os.environ.setdefault(k.strip(), v.strip().strip('"'))
from athens.http import ROUTES, respond, run  # noqa: E402

for f in sorted(os.listdir(os.path.join(ROOT, "api"))):
    if f.endswith(".py"):
        spec = importlib.util.spec_from_file_location(f"api_{f[:-3]}", os.path.join(ROOT, "api", f))
        spec.loader.exec_module(importlib.util.module_from_spec(spec))  # registers into ROUTES


class Dispatch(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # log paths without query strings: /api/here carries the user's location
        args = tuple(a.split("?", 1)[0] if isinstance(a, str) and "?" in a else a for a in args)
        super().log_message(fmt, *args)

    def do_GET(self):
        route = ROUTES.get(urlparse(self.path).path.rstrip("/"))
        if route is None:
            return respond(self, 404, {"error": "not found", "routes": sorted(ROUTES)})
        fn, cache = route
        respond(self, *run(fn, self.path), cache)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"http://localhost:{port}  routes: {', '.join(sorted(ROUTES))}")
    ThreadingHTTPServer(("127.0.0.1", port), Dispatch).serve_forever()
