# GET /api/ev[?available=1][&fast=1] → EV chargers in the Athens area (national registry ΜΥΦΑΗ): name, operator,
#   address, lat/lon, charging points, plugs, max_kw, fast (DC), live availability (`available`, `status` counts).
#   Same for every user → CDN-cached; "nearest to me" is in /api/here (`ev_nearby`).
# GET /api/ev?history=1 → {"history": [{"time": epoch_s, "occupancy": %}]}: last 24 h, one sample per 10 min
#   (recorded on chargers requests; needs the presence store, 503 without it).
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import ev, presence  # noqa: E402
from athens.http import HttpError, make_handler, with_meta  # noqa: E402


def get(q):
    if q.get("history") == "1":  # today's occupancy curve, from our own 10-minute samples
        try:
            return {"history": ev.occupancy_history(time.time(), presence.redis)}
        except presence.NotConfigured as e:
            raise HttpError(503, f"history unavailable: {e}")
    items, meta = ev.chargers()
    try:
        ev.record_occupancy(items, time.time(), presence.redis)
    except Exception:  # history is extra: never break the charger list over it
        pass
    if q.get("available") == "1":
        items = [c for c in items if c["available"]]
    if q.get("fast") == "1":
        items = [c for c in items if c["fast"]]
    return with_meta({"count": len(items), "chargers": items}, meta)


handler = make_handler("/api/ev", get, cache="public, max-age=60, s-maxage=120")
