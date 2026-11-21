"""Thin client for the City of Athens CKAN open-data API (stdlib only)."""
import json
import os
import re
import urllib.parse
import urllib.request

from .geo import parse_wkt_polygon

BASE = os.environ.get("CKAN_BASE", "https://opendata.cityofathens.gr/api/3/action")
TIMEOUT = float(os.environ.get("ATHENS_HTTP_TIMEOUT_S", 15))
MAX_BYTES = 20 * 1024 * 1024


class CkanError(Exception):
    pass


def http_get(url):
    """The only function that touches the network; tests replace it."""
    req = urllib.request.Request(url, headers={"User-Agent": "athens-monitor/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise CkanError("response larger than 20 MB")
    return data


def action(name, params, get=http_get):
    q = urllib.parse.urlencode({k: json.dumps(v) if isinstance(v, dict) else v for k, v in params.items()})
    body = json.loads(get(f"{BASE}/{name}?{q}").decode("utf-8"))
    if not body.get("success", True) or "result" not in body:
        raise CkanError(f"{name}: {body.get('error') or 'no result'}")
    return body["result"]


def datastore(resource_id, get=http_get, **params):
    return action("datastore_search", {"resource_id": resource_id, **params}, get)["records"]


def packages(prefix, get=http_get):
    """All datasets whose name starts with prefix (e.g. "env-")."""
    return action("package_search", {"fq": f"name:{prefix}*", "rows": 1000}, get)["results"]


def datastore_resource(pkg):
    for r in pkg.get("resources", []):
        if r.get("datastore_active"):
            return r["id"]
    raise CkanError(f"{pkg.get('name')}: no datastore resource")


def station_number(name):
    """env-102-fokionos-negri → 102; env-all-stations → None."""
    m = re.match(r"^[a-z-]+?-(\d{3})-", name or "")
    return int(m.group(1)) if m else None


def location(pkg):
    """(lat, lon, neighbourhood) from the dataset's spatial_coverage, or None."""
    for sc in pkg.get("spatial_coverage") or []:
        try:
            if sc.get("centroid"):
                lon, lat = json.loads(sc["centroid"])["coordinates"][:2]
            elif sc.get("bbox"):
                ring = json.loads(sc["bbox"])["coordinates"][0]
                lon, lat = (sum(p[i] for p in ring) / len(ring) for i in (0, 1))
            else:
                continue
            lat, lon = round(float(lat), 6), round(float(lon), 6)
        except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError):
            continue
        return {"lat": lat, "lon": lon, "neighbourhood": (sc.get("text") or "").strip() or None}
    return None


def num(v):
    """CKAN numeric columns can arrive as numbers or strings; → float, or None if not a finite number."""
    if isinstance(v, bool) or v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f and f not in (float("inf"), float("-inf")) else None


def as_int(v):
    f = num(v)
    return int(f) if f is not None and f.is_integer() else None


def neighbourhoods(get=http_get):
    """{NAME: {lat, lon, neighbourhood}} for all 144 neighbourhoods (dataset neighbourhoods-athens)."""
    pkg = action("package_show", {"id": "neighbourhoods-athens"}, get)
    out = {}
    for r in datastore(datastore_resource(pkg), get, limit=1000):
        try:
            loc = {"lat": round(float(r["position_lat"]), 6), "lon": round(float(r["position_lon"]), 6)}
        except (KeyError, TypeError, ValueError):
            continue
        name = (r.get("friendly_name") or r.get("name") or "").strip()
        hood = {**loc, "neighbourhood": name, "district_id": as_int(r.get("municipal_district_id")),
                "polygon": parse_wkt_polygon(r.get("polygon_geo"))}
        for key in (r.get("name"), r.get("friendly_name")):
            if key:
                out.setdefault(key.strip().upper(), hood)
    return out


def districts(get=http_get):
    """{1: "1ο Δημοτικό Διαμέρισμα Αθήνας", …} — the 7 municipal districts (dataset municipal-districts-athens)."""
    pkg = action("package_show", {"id": "municipal-districts-athens"}, get)
    return {i: (r.get("name") or "").strip() for r in datastore(datastore_resource(pkg), get, limit=100)
            if (i := as_int(r.get("id"))) is not None}


def clean_name(name):
    """"Φωκίωνος Νέγρη_206" → "Φωκίωνος Νέγρη" (the suffix is an internal device code)."""
    return re.sub(r"_\d+$", "", (name or "").strip()) or None
