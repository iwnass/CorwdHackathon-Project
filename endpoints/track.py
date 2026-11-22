# GET /api/track?lat=37.99&lon=23.73[&k=3]
#   → live tracking, called on GPS updates: neighbourhood + zone id, the k nearest stations (compact),
#     the nearest WiFi spot, and recheck_after_m (call again only after moving that far).
# Stateless: the server never stores positions or trails. Never cached by the CDN; this code never logs coordinates.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import env, traffic  # noqa: E402
from athens.http import float_param, int_param, make_handler, with_meta  # noqa: E402

WIFI_FIELDS = ("station_id", "name", "lat", "lon", "distance_m", "date", "visits", "busyness")


def get(q):
    lat, lon = float_param(q, "lat", -90, 90), float_param(q, "lon", -180, 180)
    k = int_param(q, "k", 3, 1, 10)
    d, meta = env.data()
    body = env.track(d, lat, lon, k)
    try:
        w, _ = traffic.data()
        body["nearest_wifi"] = [{f: s.get(f) for f in WIFI_FIELDS} for s in traffic.nearest(w, lat, lon, 1)]
    except Exception:  # footfall is extra
        body["nearest_wifi"] = None
    return with_meta(body, meta)


handler = make_handler("/api/track", get, cache="private, no-store")
