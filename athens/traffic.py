"""Footfall ("traffic") from the city's public WiFi stations.

The city publishes no vehicle-traffic data. What it does publish, per WiFi station and per day:
  visits          cumulative_traffic   Αθροιστική Επισκεψιμότητα   total connections that day
  visitors        active_visitors      Πληθυσμιακή Συγκέντρωση     distinct people that day
  peak_visitors   highest_visitors     Μέγιστη Επισκεψιμότητα      highest simultaneous count
Sources: wifi-stations-registry (names, addresses, resource ids) + the three *-all-stations datasets
(one request each for the whole city) + wifi-cumulative-traffic-NNN-… for coordinates.
"""
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from statistics import mean

from . import cache, ckan
from .geo import haversine

REGISTRY = "wifi-stations-registry"
TTL_S = int(os.environ.get("ATHENS_WIFI_TTL_S", 1800))  # the data is daily
DAYS = 15
ROWS = DAYS * 120  # ~81 stations per day, newest first
METRICS = {  # our name → (registry column with the aggregated resource id, value column)
    "visits": ("agg_cumulative_traffic_resource_id", "cumulative_traffic"),
    "visitors": ("agg_active_visitors_resource_id", "active_visitors"),
    "peak_visitors": ("agg_highest_visitors_resource_id", "highest_visitors"),
}
BUSY, QUIET = 1.25, 0.75  # visits vs the station's own previous-7-day average
MAX_HISTORY_DAYS = 90


def _locations(get):
    out = {}
    for p in ckan.packages("wifi-cumulative-traffic-", get):
        n, loc = ckan.station_number(p["name"]), ckan.location(p)
        if n is not None and loc:
            out[n] = loc
    return out


def _resources(registry):
    for row in registry:
        ids = {m: row.get(col) for m, (col, _) in METRICS.items()}
        if all(ids.values()):
            return ids
    raise ckan.CkanError(f"{REGISTRY}: no aggregated resource ids")


def _merge(metric_rows):
    """{metric: rows} → {station_id: {date: {visits, visitors, peak_visitors}}}"""
    days = defaultdict(lambda: defaultdict(dict))
    for m, rows in metric_rows.items():
        col = METRICS[m][1]
        for r in rows:
            sid, v = ckan.as_int(r.get("station_id")), ckan.num(r.get(col))
            if sid is not None and r.get("date") and v is not None:
                days[sid][str(r["date"])[:10]][m] = int(v) if v.is_integer() else v
    return days


def _day(s, n=0):
    return (date.fromisoformat(s) + timedelta(days=n)).isoformat()


def load(get=ckan.http_get):
    registry = ckan.datastore(ckan.datastore_resource(ckan.action("package_show", {"id": REGISTRY}, get)), get, limit=1000)
    resources = _resources(registry)
    with ThreadPoolExecutor(4) as ex:
        locs = ex.submit(_locations, get)
        rows = {m: ex.submit(ckan.datastore, rid, get, sort="_id desc", limit=ROWS) for m, rid in resources.items()}
        rows = {m: f.result() for m, f in rows.items()}
        locs = locs.result()
    info = {}
    for r in registry:
        sid = r.get("station_id")
        if sid is None:
            continue
        loc = locs.get(sid) or {}
        info[sid] = {"station_id": sid, "name": ckan.clean_name(r.get("station_name")),
                     "address": r.get("station_address") or None,
                     "neighbourhood": r.get("neighbourhood_name") or loc.get("neighbourhood"),
                     "district_id": r.get("municipal_district_id"), "district": r.get("municipal_district_name"),
                     "lat": loc.get("lat"), "lon": loc.get("lon")}
    return {"stations": info, "resources": resources, "days": _merge(rows)}


def data():
    return cache.cached("wifi", TTL_S, load)


def _busyness(v, avg):
    if v is None or not avg:
        return None, None
    ratio = v / avg
    return round((ratio - 1) * 100, 1), "busy" if ratio >= BUSY else "quiet" if ratio <= QUIET else "usual"


def overview(d):
    st = []
    for sid, info in d["stations"].items():
        days = d["days"].get(sid) or {}
        dates = sorted(days)
        if not dates:
            st.append({**info, "date": None})
            continue
        last = dates[-1]
        today = days[last]
        # calendar days, not "the previous 7 rows": gaps in the feed must not stretch the window
        prev = [days[x].get("visits") for x in dates[:-1] if x >= _day(last, -7)]
        prev = [v for v in prev if v is not None]
        avg = round(mean(prev)) if prev else None
        change, level = _busyness(today.get("visits"), avg)
        st.append({**info, "date": last, "visits": today.get("visits"), "visitors": today.get("visitors"),
                   "peak_visitors": today.get("peak_visitors"),
                   "visits_prev_day": (days.get(_day(last, -1)) or {}).get("visits"),
                   "visits_7d_avg": avg, "change_vs_7d_pct": change, "busyness": level})
    st.sort(key=lambda s: -(s.get("visits") or 0))

    totals = defaultdict(lambda: {"visits": 0, "visitors": 0, "stations": 0})
    for days in d["days"].values():
        for date, m in days.items():
            t = totals[date]
            t["visits"] += m.get("visits") or 0
            t["visitors"] += m.get("visitors") or 0
            t["stations"] += 1
    daily = [{"date": k, **v} for k, v in sorted(totals.items())][-14:]
    city = None
    if daily:
        # the newest day may still be half-published; use the newest one most stations have reported
        most = max(x["stations"] for x in daily)
        latest = next(x for x in reversed(daily) if x["stations"] >= 0.5 * most)
        # compare like with like: the previous 7 days, summed over the same stations only
        same = [sid for sid, days in d["days"].items() if latest["date"] in days]
        prev = [x["date"] for x in daily if _day(latest["date"], -7) <= x["date"] < latest["date"]]
        prev = [[d["days"][sid][x]["visits"] for sid in same if "visits" in d["days"][sid].get(x, {})] for x in prev]
        # a day missing for most of these stations would look like a collapse; leave it out
        prev = [sum(vs) for vs in prev if len(vs) >= 0.8 * len(same)]
        avg = round(mean(prev)) if prev else None
        change, level = _busyness(latest["visits"], avg)
        city = {**latest, "visits_7d_avg": avg, "change_vs_7d_pct": change, "busyness": level,
                "busiest": [s["station_id"] for s in st if s.get("date") == latest["date"]][:10]}
    return {"kind": "wifi_footfall", "city": city, "daily": daily, "stations": st}


def nearest(d, lat, lon, k):
    """The k closest WiFi spots with their latest footfall, with distance_m."""
    st = [dict(s) for s in overview(d)["stations"] if s.get("lat") is not None and s.get("date")]
    for s in st:
        s["distance_m"] = round(haversine(lat, lon, s["lat"], s["lon"]))
    return sorted(st, key=lambda s: s["distance_m"])[:k]


def history(d, station_id, days, get=ckan.http_get):
    """Daily series for one station, newest last; None if the station is unknown."""
    info = d["stations"].get(station_id)
    if info is None:
        return None

    def load_one():
        with ThreadPoolExecutor(3) as ex:
            fs = {m: ex.submit(ckan.datastore, rid, get, filters={"station_id": station_id}, sort="date desc",
                               limit=MAX_HISTORY_DAYS) for m, rid in d["resources"].items()}
            return _merge({m: f.result() for m, f in fs.items()}).get(station_id, {})

    # one cache entry per station (not per days value), so varying ?days= can't multiply calls to the city
    merged, meta = cache.cached(f"wifi:{station_id}", TTL_S, load_one)
    return {"station": info, "daily": [{"date": k, **v} for k, v in sorted(merged.items())][-days:]}, meta
