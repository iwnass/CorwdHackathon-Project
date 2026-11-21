"""Places to cool down: drinking fountains, pocket parks and public pools (City of Athens GIS, WFS GeoJSON).

shortcut: plain http — gis.cityofathens.gr only offers outdated TLS (https fails); switch when the city upgrades it.
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor

from . import cache, ckan
from .geo import haversine

WFS = os.environ.get("ATHENS_GIS_WFS", "http://gis.cityofathens.gr/geoserver/ows")
TTL_S = 24 * 3600  # these layers change a few times a year
LAYERS = {  # kind → (layer, name field, address field)
    "fountain": ("geonode:pidakes", "name", "address"),
    "pocket_park": ("geonode:PocketParks2", "descr", "streetname"),
    "pool": ("geonode:kolimbitiria", "name", "tax_diefth"),
}


def layer(name, get):
    q = f"service=WFS&version=1.0.0&request=GetFeature&typename={name}&outputFormat=application/json&srsName=EPSG:4326"
    return json.loads(get(f"{WFS}?{q}").decode("utf-8")).get("features", [])


def layers(names, get):
    """Several layers at once: the city GIS can take 5–15 s per request, so one after another could pass 30 s."""
    with ThreadPoolExecutor(len(names)) as ex:
        return dict(zip(names, ex.map(lambda n: layer(n, get), names)))


def load(get=ckan.http_get):
    out = []
    got = layers([name for name, _, _ in LAYERS.values()], get)
    for kind, (layer_name, name_f, addr_f) in LAYERS.items():
        for f in got[layer_name]:
            p, g = f.get("properties") or {}, f.get("geometry") or {}
            if p.get("status") == "ΑΝΕΝΕΡΓΟ":  # fountain out of service (upgrade works, removed)
                continue
            pt = g.get("coordinates")
            pt = pt[0] if g.get("type") == "MultiPoint" and pt else pt
            lon, lat = (ckan.num(pt[0]), ckan.num(pt[1])) if pt and len(pt) >= 2 else (None, None)
            if lat is None or lon is None:
                continue
            out.append({"kind": kind, "name": (p.get(name_f) or "").strip() or None,
                        "address": (p.get(addr_f) or "").strip() or None, "lat": lat, "lon": lon})
    return out


def data():
    return cache.cached("cooling", TTL_S, load)


def nearest(spots, lat, lon):
    """The closest spot of each kind, with distance_m."""
    best = {}
    for s in spots:
        dist = haversine(lat, lon, s["lat"], s["lon"])
        if s["kind"] not in best or dist < best[s["kind"]][0]:
            best[s["kind"]] = (dist, s)
    return {k: {**s, "distance_m": round(dist)} for k, (dist, s) in best.items()}
