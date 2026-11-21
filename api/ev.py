# GET /api/ev[?available=1][&fast=1] → EV chargers in the Athens area (national registry ΜΥΦΑΗ): name, operator,
#   address, lat/lon, charging points, plugs, max_kw, fast (DC), live availability (`available`, `status` counts).
#   Same for every user → CDN-cached; "nearest to me" is in /api/here (`ev_nearby`).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import ev  # noqa: E402
from athens.http import make_handler, with_meta  # noqa: E402


def get(q):
    items, meta = ev.chargers()
    if q.get("available") == "1":
        items = [c for c in items if c["available"]]
    if q.get("fast") == "1":
        items = [c for c in items if c["fast"]]
    return with_meta({"count": len(items), "chargers": items}, meta)


handler = make_handler("/api/ev", get, cache="public, max-age=60, s-maxage=120")
