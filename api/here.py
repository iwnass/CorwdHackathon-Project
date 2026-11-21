# GET /api/here?lat=37.99&lon=23.73[&k=3]
#   → the user's neighbourhood and zone (air + heat, 24 h curves), the k nearest air/heat stations and
#     WiFi spots, and city context. One call per position for the live map.
# Coordinates are personal data: the response is never stored by the CDN, and this code never logs them.
# (Vercel's own request logs do record URLs; the frontend can round to 3 decimals, ~100 m, before calling.)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import env, traffic  # noqa: E402
from athens.http import float_param, int_param, make_handler, with_meta  # noqa: E402


def get(q):
    lat, lon = float_param(q, "lat", -90, 90), float_param(q, "lon", -180, 180)
    k = int_param(q, "k", 3, 1, 10)
    d, meta = env.data()
    body = env.here(d, lat, lon, k)
    try:
        w, _ = traffic.data()
        body["nearest_wifi"] = traffic.nearest(w, lat, lon, k)
    except Exception:  # footfall is extra; air and heat still answer
        body["nearest_wifi"] = None
    return with_meta(body, meta)


handler = make_handler("/api/here", get, cache="private, no-store")
