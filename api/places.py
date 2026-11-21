# GET /api/places[?kind=museum,metro_station] → places for visitors (city GIS): cultural venues, named places,
#   metro/tram/rail stations, free WiFi4EU, accessible parking, drinking fountains, pocket parks, pools.
#   Same for every user → CDN-cached. Labels for `kind` in 9 languages: /api/i18n.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import places  # noqa: E402
from athens.http import make_handler, with_meta  # noqa: E402


def get(q):
    items, meta = places.all_places()
    kinds = {k for k in (q.get("kind") or "").split(",") if k}
    if kinds:
        items = [p for p in items if p["kind"] in kinds]
    return with_meta({"count": len(items), "kinds": sorted({p["kind"] for p in items}), "places": items}, meta)


handler = make_handler("/api/places", get)
