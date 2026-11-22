"""Local dev server with the same routes as Vercel, no Vercel CLI needed; / = the test UI (devtools/test-ui.html).
Reads .env.local (like `vercel dev`). Usage: python3 scripts/serve.py [port]      (default 8000)
"""
import os
import sys
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

env_file = os.path.join(ROOT, ".env.local")
if os.path.exists(env_file):
    for line in open(env_file, encoding="utf-8"):
        k, sep, v = line.strip().partition("=")
        if sep and k and not k.startswith("#"):
            os.environ.setdefault(k.strip(), v.strip().strip('"'))
if not os.environ.get("KV_REST_API_URL"):  # no Upstash locally: count live crowds in this process
    os.environ.setdefault("PRESENCE_STORE", "memory")
from athens import http  # noqa: E402

http.load_endpoints(os.path.join(ROOT, "endpoints"))
ROUTES = http.ROUTES


class Dispatch(http.Dispatch):
    def log_message(self, fmt, *args):  # log paths without query strings: /api/here carries the user's location
        args = tuple(a.split("?", 1)[0] if isinstance(a, str) and "?" in a else a for a in args)
        super().log_message(fmt, *args)

    def do_GET(self):
        if urlparse(self.path).path == "/":  # the test UI: one fixed file, nothing else is served from disk
            data = open(os.path.join(ROOT, "devtools", "test-ui.html"), "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        super().do_GET()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"http://localhost:{port}  routes: {', '.join(sorted(ROUTES))}")
    ThreadingHTTPServer(("127.0.0.1", port), Dispatch).serve_forever()
