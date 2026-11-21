"""Upcoming concerts and events in Athens from the Ticketmaster Discovery API (v2).

One city-wide request set per refresh (not per user): the user's position never goes to Ticketmaster. Needs TICKETMASTER_API_KEY (free "Consumer Key" from developer.ticketmaster.com).
Limits on the free tier: 5000 calls/day, 5/s — a 30 min cache uses ≤ 3 × 48 per instance per day.
"""
import json
import os
import urllib.error
import urllib.parse
from datetime import date, timedelta

from . import cache, ckan
from .geo import haversine
from .times import iso_local, iso_utc, now_utc, parse_utc

BASE = os.environ.get("TICKETMASTER_BASE", "https://app.ticketmaster.com/discovery/v2")
CENTER = (37.9838, 23.7275)  # Athens
RADIUS_KM = int(os.environ.get("TICKETMASTER_RADIUS_KM", 25))
HORIZON_DAYS = 90
PAGE_SIZE, MAX_PAGES = 200, 3  # Discovery API: size ≤ 200 and size × page < 1000
TTL_S = int(os.environ.get("TICKETMASTER_TTL_S", 1800))


class NotConfigured(Exception):
    pass


class TicketmasterError(Exception):
    pass


def _key():
    key = os.environ.get("TICKETMASTER_API_KEY", "").strip()
    if not key:
        raise NotConfigured("TICKETMASTER_API_KEY is not set")
    return key


def _page(page, get):
    now = now_utc().replace(microsecond=0)
    q = {"apikey": _key(), "latlong": f"{CENTER[0]},{CENTER[1]}", "radius": RADIUS_KM, "unit": "km",
         "startDateTime": iso_utc(now), "endDateTime": iso_utc(now + timedelta(days=HORIZON_DAYS)),
         "sort": "date,asc", "size": PAGE_SIZE, "page": page, "locale": "*"}
    try:
        raw = get(f"{BASE}/events.json?{urllib.parse.urlencode(q)}")
    except urllib.error.HTTPError as e:  # 401 bad key, 429 rate limit, …
        raise TicketmasterError(f"Ticketmaster HTTP {e.code}") from None
    except Exception as e:  # `from None`: the URL carries the API key and must not reach the logs
        raise TicketmasterError(f"Ticketmaster request failed: {type(e).__name__}") from None
    return json.loads(raw.decode("utf-8"))


def _image(ev):
    imgs = [i for i in ev.get("images") or [] if i.get("url")]
    wide = [i for i in imgs if i.get("ratio") == "16_9"] or imgs
    return max(wide, key=lambda i: i.get("width") or 0)["url"] if wide else None


def _defined(name):
    return None if (name or "").strip().lower() in ("", "undefined") else name.strip()


def _normalize(ev):
    """Discovery API event → the few fields a map needs."""
    venue = ((ev.get("_embedded") or {}).get("venues") or [{}])[0]
    loc = venue.get("location") or {}
    start = (ev.get("dates") or {}).get("start") or {}
    classes = ev.get("classifications") or [{}]
    cls = next((c for c in classes if c.get("primary")), classes[0])
    price = (ev.get("priceRanges") or [None])[0]
    return {
        "id": ev.get("id"), "name": ev.get("name"), "url": ev.get("url"), "image": _image(ev),
        "category": _defined((cls.get("segment") or {}).get("name")), "genre": _defined((cls.get("genre") or {}).get("name")),
        "date": start.get("localDate"), "time": start.get("localTime"), "start": start.get("dateTime"),
        "status": ((ev.get("dates") or {}).get("status") or {}).get("code"),
        "venue": {"name": venue.get("name"), "address": (venue.get("address") or {}).get("line1"),
                  "city": (venue.get("city") or {}).get("name"),
                  "lat": ckan.num(loc.get("latitude")), "lon": ckan.num(loc.get("longitude"))},
        "price": price and {"min": price.get("min"), "max": price.get("max"), "currency": price.get("currency")},
        "performers": [a.get("name") for a in (ev.get("_embedded") or {}).get("attractions") or [] if a.get("name")],
    }


def load(get=ckan.http_get):
    raw, total = [], 0
    for page in range(MAX_PAGES):
        body = _page(page, get)
        raw += (body.get("_embedded") or {}).get("events") or []
        info = body.get("page") or {}
        total = info.get("totalElements", len(raw))
        if page + 1 >= (info.get("totalPages") or 0):
            break
    seen, out = set(), []
    for ev in raw:
        e = _normalize(ev)
        # "TO BE DELETED_…" are Ticketmaster test leftovers seen in live Athens data
        if e["id"] in seen or e["status"] == "cancelled" or (e["name"] or "").upper().startswith("TO BE DELETED"):
            continue
        seen.add(e["id"])
        out.append(e)
    return {"events": out, "total": total}


def data():
    return cache.cached("events", TTL_S, load)


WHEN = ("today", "weekend", "week")


def when_range(when, today=None):
    """Athens-local dates (first, last) for today / this weekend / the next 7 days."""
    today = today or date.fromisoformat(iso_local(now_utc())[:10])
    if when == "today":
        return today, today
    if when == "weekend":  # on Saturday or Sunday: the rest of this weekend
        sat = today + timedelta(days=(5 - today.weekday()) % 7) if today.weekday() < 5 else today
        return sat, sat + timedelta(days=6 - sat.weekday())
    return today, today + timedelta(days=6)


def upcoming(d, days=30, category=None, limit=50, when=None):
    """Events in the next `days` (or `when`), soonest first. The same for every user, so it can be cached by the CDN."""
    until = now_utc() + timedelta(days=days)
    first, last = when_range(when) if when else (None, None)
    out = []
    for e in d["events"]:
        if when and not (e["date"] and first.isoformat() <= e["date"] <= last.isoformat()):
            continue
        try:
            if e["start"] and parse_utc(e["start"]) > until:
                continue
        except ValueError:
            pass
        if category and (e["category"] or "").lower() != category.lower():
            continue
        out.append(dict(e, venue=dict(e["venue"])))
    return {"count": len(out), "categories": sorted({e["category"] for e in d["events"] if e["category"]}),
            "events": out[:limit]}


def nearby(d, lat, lon, radius_m=2000, k=5, days=7):
    """The next show of each event within radius_m in the next `days`, soonest first, with distance_m."""
    seen, out = set(), []
    for e in upcoming(d, days=days, limit=10 ** 6)["events"]:
        v = e["venue"]
        key = (e["name"], v["name"])  # theatres list the same play many times
        if v["lat"] is None or key in seen:
            continue
        dist = haversine(lat, lon, v["lat"], v["lon"])
        if dist <= radius_m:
            seen.add(key)
            out.append({**e, "distance_m": round(dist)})
    return out[:k]
