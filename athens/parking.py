"""Parking stations near the centre from OpenStreetMap (Overpass API, no key): garages, underground and
multi-storey car parks, and named public lots. The city publishes only parking zones and disabled spaces.
If Overpass is down, the snapshot in data/parking.json.
"""
import json
import os
import urllib.parse
import urllib.request

from . import cache, ckan

OVERPASS = os.environ.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
SNAPSHOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "parking.json")
TTL_S = 24 * 3600
QUERY = ('[out:json][timeout:40];nwr["amenity"="parking"]["access"!~"private|customers|no"]'
         '["parking"!~"street_side|lane|on_street"](around:6000,37.9838,23.7275);out center tags;')
GARAGE = {"underground", "multi-storey", "garage", "rooftop"}


def overpass_get():
    body = urllib.parse.urlencode({"data": QUERY}).encode()
    req = urllib.request.Request(OVERPASS, data=body, headers={"User-Agent": "athens-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read(ckan.MAX_BYTES))


def normalize(osm):
    """Overpass elements → parking stations; unnamed surface lots are left out (hundreds of them, no use to a visitor)."""
    out = []
    for e in osm.get("elements", []):
        t = e.get("tags") or {}
        kind = t.get("parking")
        if kind not in GARAGE and not t.get("name"):
            continue
        lat, lon = e.get("lat") or (e.get("center") or {}).get("lat"), e.get("lon") or (e.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        street = " ".join(x for x in (t.get("addr:street"), t.get("addr:housenumber")) if x) or None
        out.append({"id": f"{e['type']}/{e['id']}", "name": t.get("name") or t.get("operator"),
                    "name_en": t.get("name:en") or t.get("int_name"), "lat": lat, "lon": lon,
                    "type": kind if kind in GARAGE else "surface", "address": street,
                    "capacity": ckan.num(t.get("capacity")), "ev_points": ckan.num(t.get("capacity:charging")),
                    "fee": {"yes": True, "no": False}.get(t.get("fee")), "hours": t.get("opening_hours"),
                    "operator": t.get("operator"), "wheelchair": t.get("wheelchair") == "yes",
                    "park_ride": t.get("park_ride") == "yes"})
    return out


def load(get=overpass_get):
    try:
        return normalize(get())
    except Exception:
        with open(SNAPSHOT, encoding="utf-8") as f:
            return normalize(json.load(f))


def stations():
    return cache.cached("parking", TTL_S, load)
