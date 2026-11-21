# GET /api/events[?days=30|when=today|weekend|week][&category=Music][&limit=50]
#   → upcoming concerts and events in Athens (Ticketmaster), soonest first. Each venue carries its
#     neighbourhood and district_id, so the app groups events by the user's location (from /api/track) itself:
#     the URL holds no position, every user gets the same CDN-cached answer. 503 if TICKETMASTER_API_KEY is unset.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import env, events  # noqa: E402
from athens.http import HttpError, int_param, make_handler, with_meta  # noqa: E402


def get(q):
    days = int_param(q, "days", 30, 1, events.HORIZON_DAYS)
    limit = int_param(q, "limit", 50, 1, 200)
    when = q.get("when")
    if when is not None and when not in events.WHEN:
        raise HttpError(400, f"when must be one of {', '.join(events.WHEN)}")
    try:
        d, meta = events.data()
    except events.NotConfigured as e:
        raise HttpError(503, f"events unavailable: {e}")
    body = with_meta(events.upcoming(d, days, q.get("category"), limit, when), meta)
    body["meta"]["source"] = "Ticketmaster Discovery API"
    try:
        city, _ = env.data()
    except Exception:  # zones only enrich events
        city = None
    for e in body["events"]:
        v = e["venue"]
        loc = env.locate(city, v["lat"], v["lon"]) if city and v["lat"] is not None else {}
        if loc.get("match") != "inside":  # a venue has an exact address: no GPS-border tolerance (Allwyn Arena is not Athens)
            loc = {}
        v["neighbourhood"], v["district_id"] = loc.get("neighbourhood"), loc.get("district_id")
    return body


handler = make_handler("/api/events", get)
