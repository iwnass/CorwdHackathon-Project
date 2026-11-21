# GET /api/stations → every environmental and WiFi station with coordinates (for the map)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import env, traffic  # noqa: E402
from athens.http import make_handler, with_meta  # noqa: E402


def get(q):
    e, meta_e = env.data()
    w, meta_w = traffic.data()
    meta = {"fetched_at": min(meta_e["fetched_at"], meta_w["fetched_at"]),
            "expires_at": min(meta_e["expires_at"], meta_w["expires_at"]), "stale": meta_e["stale"] or meta_w["stale"]}
    wifi = sorted(w["stations"].values(), key=lambda s: s["station_id"])
    return with_meta({"environment": env.stations(e), "wifi": wifi}, meta)


handler = make_handler("/api/stations", get)
