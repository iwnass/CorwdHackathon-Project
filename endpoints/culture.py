# GET /api/culture[?when=today]
#   → City of Athens cultural events (cultureisathens.gr, the municipality's culture portal): from today on plus
#     what's running now, soonest first; when=today: only today's. Each has date, time, venue, free/price, lat/lon
#     and its page's url. The same for every user, so it's CDN-cached.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import culture, events  # noqa: E402
from athens.http import HttpError, make_handler, with_meta  # noqa: E402


def get(q):
    when = q.get("when")
    if when not in (None, "today"):
        raise HttpError(400, "when must be today")
    d, meta = culture.data()
    today = events.when_range("today")[0].isoformat()
    items = culture.on(d, today) if when == "today" else culture.upcoming(d, today)
    body = with_meta({"count": len(items), "events": items}, meta)
    body["meta"]["source"] = "cultureisathens.gr (City of Athens)"
    return body


handler = make_handler("/api/culture", get, cache="public, max-age=300, s-maxage=1800")
