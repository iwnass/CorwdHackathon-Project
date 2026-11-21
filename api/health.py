# GET /api/health → liveness + what this instance has cached (never calls the city API)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import cache  # noqa: E402
from athens.http import make_handler  # noqa: E402

handler = make_handler("/api/health", lambda q: {"ok": True, "cache": cache.status()})
