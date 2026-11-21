# GET /api/parking → parking stations within 6 km of the centre (OpenStreetMap): name, lat/lon, type (underground,
#   multi-storey, garage, rooftop, surface), address, capacity, ev_points, fee, hours, operator, wheelchair, park_ride.
#   Same for every user → CDN-cached.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import parking  # noqa: E402
from athens.http import make_handler, with_meta  # noqa: E402


def get(q):
    items, meta = parking.stations()
    return with_meta({"count": len(items), "parking": items}, meta)


handler = make_handler("/api/parking", get)
