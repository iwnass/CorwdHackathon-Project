"""EV chargers in the Athens area from the national registry (ΜΥΦΑΗ, electrokinisi.yme.gov.gr): public OCPI files,
no key — static data refreshed daily, live availability every 10 minutes.
"""
import io
import json
import urllib.request
import zipfile
from collections import Counter

from . import cache, ckan
from .geo import haversine

BASE = "https://electrokinisi.yme.gov.gr/public/static_files"
STATIC_URL, LIVE_URL = f"{BASE}/GR.IDRO.static.data.latest.json.zip", f"{BASE}/GR.IDRO.dynamic.data.latest.json.zip"
CENTER, RADIUS_M = (37.9838, 23.7275), 25000  # Athens and around (Attica basin)
STATIC_TTL_S, LIVE_TTL_S = 24 * 3600, 600
STATUS = {"AVAILABLE": "ev_available", "CHARGING": "ev_in_use", "RESERVED": "ev_in_use", "BLOCKED": "ev_in_use",
          "OUTOFORDER": "ev_out_of_order", "INOPERATIVE": "ev_out_of_order"}  # anything else → ev_unknown
PLUG = {"IEC_62196_T2": "Type 2", "IEC_62196_T2_COMBO": "CCS", "CHADEMO": "CHAdeMO", "IEC_62196_T1": "Type 1",
        "IEC_62196_T1_COMBO": "CCS1", "DOMESTIC_F": "Schuko", "TESLA_S": "Tesla"}


def zip_get(url):
    """The registry serves zips and answers 406 to the JSON-only Accept header of ckan.http_get."""
    req = urllib.request.Request(url, headers={"User-Agent": "athens-monitor/1.0", "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(ckan.MAX_BYTES)


def _locations(url, get):
    z = zipfile.ZipFile(io.BytesIO(get(url)))
    return json.loads(z.read(z.namelist()[0])).get("Locations") or []


def _point(loc):
    c = loc.get("coordinates") or {}
    return ckan.num(c.get("latitude")), ckan.num(c.get("longitude"))


def load_static(get=zip_get):
    out = {}
    for loc in _locations(STATIC_URL, get):
        lat, lon = _point(loc)
        if lat is None or lon is None or haversine(*CENTER, lat, lon) > RADIUS_M or loc.get("publish") is False:
            continue
        conns = [c for e in loc.get("evses") or [] for c in e.get("connectors") or []]
        kw = [c["max_electric_power"] / 1000 for c in conns if isinstance(c.get("max_electric_power"), (int, float))]
        out[loc["id"]] = {"id": loc["id"], "name": (loc.get("name") or "").strip() or None,
                          "address": " ".join(x for x in (loc.get("address"), loc.get("city")) if x).strip() or None,
                          "operator": (loc.get("operator") or {}).get("name") or loc.get("party_id"),
                          "lat": lat, "lon": lon, "points": len(loc.get("evses") or []),
                          "plugs": sorted({PLUG.get(c.get("standard"), c.get("standard")) for c in conns if c.get("standard")}),
                          "max_kw": round(max(kw), 1) if kw else None,
                          "fast": any(str(c.get("power_type", "")).startswith("DC") for c in conns),
                          "status": Counter(STATUS.get(e.get("status"), "ev_unknown") for e in loc.get("evses") or [])}
    return out


def load_live(get=zip_get):
    return {loc["id"]: Counter(STATUS.get(e.get("status"), "ev_unknown") for e in loc.get("evses") or [])
            for loc in _locations(LIVE_URL, get)}


def chargers():
    """Athens-area chargers, each with `available` and per-status counts; `live` says if availability is fresh."""
    static, meta = cache.cached("ev_static", STATIC_TTL_S, load_static)
    try:
        live, _ = cache.cached("ev_live", LIVE_TTL_S, load_live)
    except Exception:  # availability is extra: the daily snapshot still says where the chargers are
        live = {}
    out = []
    for c in static.values():
        st = live.get(c["id"]) or c["status"]
        out.append({**{k: v for k, v in c.items() if k != "status"}, "status": dict(st),
                    "available": st.get("ev_available", 0), "live": c["id"] in live})
    return out, meta


def near(items, lat, lon, radius_m=3000, k=3):
    found = sorted(((haversine(lat, lon, c["lat"], c["lon"]), c) for c in items), key=lambda x: x[0])
    return [{**c, "distance_m": round(d)} for d, c in found if d <= radius_m][:k]
