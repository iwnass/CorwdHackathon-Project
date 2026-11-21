# GET /api/here?lat=37.99&lon=23.73[&k=3]
#   → the user's neighbourhood and zone (air + heat, 24 h curves), the k nearest air/heat stations, footfall
#     around the point (WiFi spots within 1 km + how busy vs usual), cool-down spots and city context.
# Coordinates are personal data: the response is never stored by the CDN, and this code never logs them.
# (Vercel's own request logs do record URLs; the frontend can round to 3 decimals, ~100 m, before calling.)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import cooling, env, events, places, traffic  # noqa: E402
from athens.http import float_param, int_param, make_handler, with_meta  # noqa: E402


def get(q):
    lat, lon = float_param(q, "lat", -90, 90), float_param(q, "lon", -180, 180)
    k = int_param(q, "k", 3, 1, 10)
    d, meta = env.data()
    body = env.here(d, lat, lon, k)
    try:
        w, _ = traffic.data()
        body["footfall"] = traffic.at_point(w, lat, lon)
    except Exception:  # footfall is extra; air and heat still answer
        body["footfall"] = None
    try:  # nearest fountain, pocket park and pool — what to do about the heat
        body["cooling"] = cooling.nearest(cooling.data()[0], lat, lon)
    except Exception:
        body["cooling"] = None
    try:  # for visitors: what is around (1 km) and the nearest accessible parking (2 km)
        everything, _ = places.all_places()
        body["places_nearby"] = places.near([p for p in everything if p["kind"] != "accessible_parking"], lat, lon)
        body["accessible_parking"] = places.near(everything, lat, lon, 2000, 1, {"accessible_parking"})
    except Exception:
        body["places_nearby"] = body["accessible_parking"] = None
    try:  # next shows within 2 km this week (from the cached city-wide list: no extra Ticketmaster call)
        body["events_nearby"] = events.nearby(events.data()[0], lat, lon)
    except Exception:  # includes TICKETMASTER_API_KEY not set
        body["events_nearby"] = None
    return with_meta(body, meta)


handler = make_handler("/api/here", get, cache="private, no-store")
