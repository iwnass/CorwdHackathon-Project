# POST /api/presence  {"session": "<random id the app makes>", "lat": 37.97, "lon": 23.73}
#   → counts this (anonymous, opted-in) app user in their ~220 m cell for the next 15 min. Call every ~2 min while
#   the app is open. Nothing personal is stored: see athens/presence.py. 503 until the store is configured.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import presence  # noqa: E402
from athens.http import HttpError, float_param, make_handler  # noqa: E402


def get(q, body, ip=None):
    lat = float_param({"lat": body.get("lat")}, "lat", -90, 90)
    lon = float_param({"lon": body.get("lon")}, "lon", -180, 180)
    try:
        return presence.ping(body.get("session"), lat, lon, ip)
    except ValueError as e:
        raise HttpError(400, str(e))
    except presence.RateLimited as e:
        raise HttpError(429, str(e))
    except presence.NotConfigured as e:
        raise HttpError(503, f"presence unavailable: {e}")


handler = make_handler("/api/presence", get, cache="private, no-store", method="POST")
