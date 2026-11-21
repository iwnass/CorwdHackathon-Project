"""Air quality and heat from the Smart Sense stations.

Source: dataset env-all-stations — one row per station per hour, all stations, timestamps in UTC.
One request returns the last ~24 h for the whole city; station coordinates come from the
per-station datasets (env-NNN-…) via spatial_coverage.
"""
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from statistics import mean

from . import cache, ckan
from .geo import distance_to_boundary_m, haversine, in_polygon
from .indices import eaqi_label, heat_index, heat_level, pollution, pollution_level, us_aqi, us_aqi_category
from .times import iso_local, iso_utc, now_utc, parse_utc

ALL_STATIONS = "env-all-stations"
TTL_S = int(os.environ.get("ATHENS_ENV_TTL_S", 600))  # the data is hourly
ROWS = int(os.environ.get("ATHENS_ENV_ROWS", 4000))   # newest rows; ≈ 24 h × ~100 stations
WINDOW_H = 24
FRESH_H = 3  # a station counts toward the city's "now" only if its last reading is this recent
POLLUTANTS = ("pm1", "pm2_5", "pm10", "no2", "o3", "co", "so2", "no")
# Above the top of the EPA scale: a faulty sensor (seen live: one station stuck at ~1900 µg/m³).
# Such rows stay visible with suspect=True but are left out of city averages and rankings.
SUSPECT = {"pm2_5": 500, "pm10": 604}


def _optional(future, default):
    """Neighbourhoods and district names only enrich the data; their failure must not fail the load."""
    try:
        return future.result()
    except Exception:
        return default


def load(get=ckan.http_get):
    with ThreadPoolExecutor(2) as ex:
        hoods = ex.submit(ckan.neighbourhoods, get)
        names = ex.submit(ckan.districts, get)
        pkgs = ckan.packages("env-", get)
        agg = next((p for p in pkgs if p["name"] == ALL_STATIONS), None)
        if agg is None:
            raise ckan.CkanError(f"dataset {ALL_STATIONS} not found")
        rows = _window(ckan.datastore(ckan.datastore_resource(agg), get, sort="_id desc", limit=ROWS))
        hoods, names = _optional(hoods, {}), _optional(names, {})
    locations = {}
    for p in pkgs:
        n, loc = ckan.station_number(p["name"]), ckan.location(p)
        if n is not None and loc:
            locations[n] = loc
    for r in rows:
        hood = hoods.get(str(r.get("neighbourhood_name") or "").strip().upper()) or {}
        # ~20 stations have no dataset of their own: place them at their neighbourhood's centre
        if r["station_id"] not in locations and hood:
            locations[r["station_id"]] = hood
        if r["district_id"] is None:
            r["district_id"] = hood.get("district_id")
    unique = {id(h): h for h in hoods.values()}.values()  # each neighbourhood is indexed under 2 names
    return {"rows": rows, "locations": locations, "districts": _districts(names, hoods, rows),
            "neighbourhoods": [h for h in unique if h.get("polygon")]}


def _districts(names, hoods, rows):
    """{id: {name, lat, lon, neighbourhoods}}; the centre is the mean of the district's neighbourhood centres."""
    members = defaultdict(dict)
    for h in hoods.values():
        if h.get("district_id") is not None:
            members[h["district_id"]][h["neighbourhood"]] = h
    out = {}
    for i in sorted(set(names) | set(members) | {r["district_id"] for r in rows if r["district_id"] is not None}):
        hs = sorted(members.get(i, {}).values(), key=lambda h: h["neighbourhood"])
        out[i] = {"name": names.get(i) or f"{i}ο Δημοτικό Διαμέρισμα Αθήνας",
                  "lat": _avg((h["lat"] for h in hs), 6), "lon": _avg((h["lon"] for h in hs), 6),
                  "neighbourhoods": [h["neighbourhood"] for h in hs]}
    return out


def data():
    return cache.cached("env", TTL_S, load)


def _window(rows):
    """Last 24 h, one row per station per clock hour (stray off-hour readings fold into their hour)."""
    by_hour, future = {}, now_utc() + timedelta(hours=1)
    for r in rows:
        sid = ckan.as_int(r.get("station_id"))
        if sid is None or not r.get("timestamp"):
            continue
        try:
            t = parse_utc(r["timestamp"])
        except ValueError:
            continue
        if t > future:  # a sensor with a wrong clock must not drag the window away from everyone else
            continue
        r = {**r, "station_id": sid, "aqi": ckan.as_int(r.get("aqi")),
             "district_id": ckan.as_int(r.get("municipal_district_id")),
             **{k: ckan.num(r.get(k)) for k in (*POLLUTANTS, "temperature", "humidity", "pressure")}}
        key = (sid, t.replace(minute=0, second=0, microsecond=0))
        if key not in by_hour or t > by_hour[key][0]:
            by_hour[key] = (t, r)
    if not by_hour:
        return []
    last = max(h for _, h in by_hour)
    out = [{**r, "_t": h, "suspect": _suspect(r)} for (_, h), (_, r) in by_hour.items()
           if h > last - timedelta(hours=WINDOW_H)]
    out.sort(key=lambda r: r["_t"])
    return out


def _suspect(r):
    return any(isinstance(r.get(k), (int, float)) and r[k] > limit for k, limit in SUSPECT.items())


def _avg(values, nd=1):
    vs = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return round(mean(vs), nd) if vs else None


def _info(r, locations):
    loc = locations.get(r["station_id"]) or {}
    return {"station_id": r["station_id"], "name": ckan.clean_name(r.get("station_name")),
            "neighbourhood": r.get("neighbourhood_name") or loc.get("neighbourhood"),
            "district_id": r["district_id"], "lat": loc.get("lat"), "lon": loc.get("lon")}


def _time(t):
    return {"time": iso_utc(t), "time_local": iso_local(t)}


def _latest(rows):
    out = {}
    for r in rows:  # sorted by time, so the last one wins
        out[r["station_id"]] = r
    return out


def _by_hour(rows):
    hours = defaultdict(list)
    for r in rows:
        hours[r["_t"]].append(r)
    return sorted(hours.items())


def _age_h(t, ref):
    return round((ref - t).total_seconds() / 3600, 1)


def stations(d):
    """Station directory: id, name, neighbourhood, coordinates."""
    return sorted((_info(r, d["locations"]) for r in _latest(d["rows"]).values()), key=lambda s: s["station_id"])


# ---------- Air ----------
def _air_row(r):
    """Headline: one general pollution percentage. Every individual pollutant goes into `details`
    (for the frontend's analytic view). A faulty sensor gets no percentage instead of a false 100 %."""
    pct, level, main = (None, None, None) if r["suspect"] else pollution(r)
    u = us_aqi(r.get("pm2_5"), r.get("pm10"))
    return {"pollution_pct": pct, "pollution_level": level, "main_pollutant": main, "suspect": r["suspect"],
            "details": {"aqi": r.get("aqi"), "aqi_label": eaqi_label(r.get("aqi")),
                        "us_aqi": u, "us_aqi_category": us_aqi_category(u), **{k: r.get(k) for k in POLLUTANTS}}}


def _air_stations(d, rows):
    """Latest reading per station, most polluted first (faulty sensors last)."""
    now, last = now_utc(), d["rows"][-1]["_t"]
    st = [{**_info(r, d["locations"]), **_time(r["_t"]), "age_hours": _age_h(r["_t"], now),
           "fresh": _age_h(r["_t"], last) <= FRESH_H, **_air_row(r)} for r in _latest(rows).values()]
    st.sort(key=lambda s: (s["suspect"], s["pollution_pct"] is None, -(s["pollution_pct"] or 0)))
    return st


def _air_summary(st):
    """Over fresh, non-suspect stations: the average and worst percentage up front, the rest in details."""
    fresh = [s for s in st if s["fresh"] and not s["suspect"]]
    pct = _avg((s["pollution_pct"] for s in fresh), 0)
    pct = None if pct is None else int(pct)
    us = _avg((s["details"]["us_aqi"] for s in fresh), 0)
    return {"stations": len(fresh), "pollution_pct_avg": pct, "pollution_level": pollution_level(pct),
            "pollution_pct_max": max((s["pollution_pct"] for s in fresh if s["pollution_pct"] is not None), default=None),
            "worst": [s["station_id"] for s in fresh[:5]],
            "suspect": [s["station_id"] for s in st if s["suspect"]],
            "details": {"aqi_avg": _avg(s["details"]["aqi"] for s in fresh),
                        "aqi_max": max((s["details"]["aqi"] for s in fresh if s["details"]["aqi"] is not None), default=None),
                        "us_aqi_avg": None if us is None else int(us), "us_aqi_category": us_aqi_category(us),
                        **{f"{k}_avg": _avg(s["details"][k] for s in fresh) for k in ("pm2_5", "pm10", "no2", "o3", "so2")}}}


def _air_hourly(rows):
    hourly = []
    for t, rs in _by_hour(r for r in rows if not r["suspect"]):
        pct = _avg((pollution(r)[0] for r in rs), 0)
        u = _avg((us_aqi(r.get("pm2_5"), r.get("pm10")) for r in rs), 0)
        hourly.append({**_time(t), "stations": len(rs), "pollution_pct_avg": None if pct is None else int(pct),
                       "details": {"aqi_avg": _avg(r.get("aqi") for r in rs), "us_aqi_avg": None if u is None else int(u),
                                   **{f"{k}_avg": _avg(r.get(k) for r in rs) for k in ("pm2_5", "pm10", "no2", "o3", "so2")}}})
    return hourly


def air(d):
    rows = d["rows"]
    if not rows:
        return {"stations": [], "city": None, "hourly": []}
    st = _air_stations(d, rows)
    return {"city": {**_time(rows[-1]["_t"]), **_air_summary(st)}, "stations": st, "hourly": _air_hourly(rows)}


# ---------- Zones = municipal districts ----------
def _zone(d, district_id, rows, detail):
    """One district: {…identity, air: {summary, hourly}, heat: {summary, hourly}, [stations]}."""
    info = d["districts"].get(district_id) or {}
    z = {"district_id": district_id, "name": info.get("name"), "lat": info.get("lat"), "lon": info.get("lon"),
         "neighbourhoods": info.get("neighbourhoods", []), "stations_count": len({r["station_id"] for r in rows}),
         "air": None, "heat": None}
    if rows:
        air_st, heat_st, heat_h = _air_stations(d, rows), _heat_stations(d, rows), _heat_hourly(rows)
        z["air"] = {**_air_summary(air_st), "hourly": _air_hourly(rows)}
        z["heat"] = {**_heat_summary(heat_st, heat_h), "hourly": heat_h}
        if detail:
            z["stations"] = _combined(air_st, heat_st)
    elif detail:
        z["stations"] = []
    return z


def _combined(air_st, heat_st):
    """One row per station with both its air and its heat fields (air order kept)."""
    heat_by = {s["station_id"]: s for s in heat_st}
    keys = ("temperature", "humidity", "feels_like", "heat_level", "min_24h", "max_24h")
    return [{**s, **{k: heat_by[s["station_id"]][k] for k in keys}} for s in air_st]


def _ranked(zs, block, field):
    """District ids, highest value first; zones without data last."""
    val = lambda z: (z[block] or {}).get(field)  # noqa: E731
    return [z["district_id"] for z in sorted(zs, key=lambda z: (val(z) is None, -(val(z) or 0)))]


def zones(d):
    """Air quality and heat per municipal district (1–7), worst air first."""
    rows = d["rows"]
    by = defaultdict(list)
    for r in rows:
        by[r["district_id"]].append(r)
    out = [_zone(d, i, by.get(i, []), False) for i in d["districts"]]
    order = _ranked(out, "air", "pollution_pct_avg")
    out.sort(key=lambda z: order.index(z["district_id"]))
    return {**(_time(rows[-1]["_t"]) if rows else {}),
            "ranking": {"worst_air": order, "hottest": _ranked(out, "heat", "temperature_avg")},
            "zones": out,
            "unassigned_stations": sorted({r["station_id"] for r in rows if r["district_id"] not in d["districts"]})}


def zone(d, district_id):
    """One district with its stations, or None if unknown."""
    if district_id not in d["districts"]:
        return None
    rows = [r for r in d["rows"] if r["district_id"] == district_id]
    return {**(_time(rows[-1]["_t"]) if rows else {}), "zone": _zone(d, district_id, rows, True)}


# ---------- Heat ----------
def _heat_row(r):
    feels = heat_index(r.get("temperature"), r.get("humidity"))
    return {"temperature": r.get("temperature"), "humidity": r.get("humidity"),
            "feels_like": feels, "heat_level": heat_level(feels)}


def _heat_stations(d, rows):
    """Latest reading per station with its 24 h min/max, hottest first."""
    now, last = now_utc(), d["rows"][-1]["_t"]
    temps = defaultdict(list)
    for r in rows:
        if r.get("temperature") is not None:
            temps[r["station_id"]].append(r["temperature"])
    st = []
    for sid, r in _latest(rows).items():
        ts = temps.get(sid)
        st.append({**_info(r, d["locations"]), **_time(r["_t"]), "age_hours": _age_h(r["_t"], now),
                   "fresh": _age_h(r["_t"], last) <= FRESH_H, **_heat_row(r),
                   "min_24h": min(ts) if ts else None, "max_24h": max(ts) if ts else None})
    st.sort(key=lambda s: (s["temperature"] is None, -(s["temperature"] or 0)))
    return st


def _heat_hourly(rows):
    hourly = []
    for t, rs in _by_hour(rows):
        tv = [r["temperature"] for r in rs if r.get("temperature") is not None]
        hourly.append({**_time(t), "stations": len(rs), "temperature_avg": _avg(tv),
                       "temperature_min": min(tv) if tv else None, "temperature_max": max(tv) if tv else None,
                       "humidity_avg": _avg(r.get("humidity") for r in rs),
                       "feels_like_avg": _avg(heat_index(r.get("temperature"), r.get("humidity")) for r in rs)})
    return hourly


def _heat_summary(st, hourly):
    """Now (fresh stations) + the warmest and coolest hour of the last 24 h."""
    fresh = [s for s in st if s["fresh"] and s["temperature"] is not None]
    with_t = [h for h in hourly if h["temperature_avg"] is not None]
    peak = max(with_t, key=lambda h: h["temperature_avg"]) if with_t else None
    low = min(with_t, key=lambda h: h["temperature_avg"]) if with_t else None
    feels = _avg(s["feels_like"] for s in fresh)
    return {"stations": len(fresh), "temperature_avg": _avg(s["temperature"] for s in fresh),
            "temperature_min": min((s["temperature"] for s in fresh), default=None),
            "temperature_max": max((s["temperature"] for s in fresh), default=None),
            "humidity_avg": _avg(s["humidity"] for s in fresh), "feels_like_avg": feels, "heat_level": heat_level(feels),
            "hottest": [s["station_id"] for s in fresh[:5]], "coolest": [s["station_id"] for s in fresh[::-1][:5]],
            "peak_hour_24h": peak and {"time": peak["time"], "time_local": peak["time_local"], "temperature_avg": peak["temperature_avg"]},
            "low_hour_24h": low and {"time": low["time"], "time_local": low["time_local"], "temperature_avg": low["temperature_avg"]}}


def heat(d):
    rows = d["rows"]
    if not rows:
        return {"stations": [], "city": None, "hourly": []}
    st, hourly = _heat_stations(d, rows), _heat_hourly(rows)
    return {"city": {**_time(rows[-1]["_t"]), **_heat_summary(st, hourly)}, "stations": st, "hourly": hourly}


# ---------- Where the user is ----------
EDGE_M = 1500  # outside every neighbourhood but this close to one: GPS error at a border, not another city


def _find_hood(d, lat, lon):
    hoods = d.get("neighbourhoods") or []
    hood = next((h for h in hoods if in_polygon(lat, lon, h["polygon"])), None)
    if hood:
        return hood, "inside"
    if hoods:
        near = min(hoods, key=lambda h: haversine(lat, lon, h["lat"], h["lon"]))
        if haversine(lat, lon, near["lat"], near["lon"]) <= EDGE_M:
            return near, "nearest"
    return None, "outside"


def locate(d, lat, lon):
    """The neighbourhood and zone containing (lat, lon). match = inside | nearest | outside."""
    hood, match = _find_hood(d, lat, lon)
    return {"lat": lat, "lon": lon, "match": match,
            "neighbourhood": hood and hood["neighbourhood"], "district_id": hood and hood["district_id"]}


def nearest(d, lat, lon, k):
    """The k closest stations with a recent, trustworthy reading, air + heat, with distance_m.
    Faulty (suspect) sensors are skipped: on a map they would show the user a false "Hazardous"."""
    return [s for _, s in _by_distance(d, lat, lon)[:k]]


def _by_distance(d, lat, lon):
    """[(exact distance, station)] for every trustworthy station, nearest first; ties broken by id so that
    co-located stations always come out in the same order."""
    rows = d["rows"]
    if not rows:
        return []
    out = []
    for s in _combined(_air_stations(d, rows), _heat_stations(d, rows)):
        if s["lat"] is not None and s["fresh"] and not s["suspect"]:
            dist = haversine(lat, lon, s["lat"], s["lon"])
            out.append((dist, {**s, "distance_m": round(dist)}))
    out.sort(key=lambda x: (x[0], x[1]["station_id"]))
    return out


RECHECK_MIN_M, RECHECK_MAX_M = 1, 500  # below ~GPS accuracy (5–10 m) the user is at a border: call on every fix
TRACK_FIELDS = ("station_id", "name", "lat", "lon", "distance_m", "pollution_pct", "pollution_level", "main_pollutant",
                "temperature", "feels_like", "heat_level", "time")


def track(d, lat, lon, k):
    """Light answer for live tracking (~1–2 KB): where the user is, the k nearest stations (compact), and
    recheck_after_m — how far they can move before this answer could change, so the client only calls again then."""
    hood, match = _find_hood(d, lat, lon)
    ranked = _by_distance(d, lat, lon)
    near = [s for _, s in ranked[:k]]
    # Moving δ metres changes any two distances' difference by at most 2δ, so the order is safe for half the gap.
    # Stations at the very same point never swap; when the k-th place is shared like that, look past the group.
    same = lambda a, b: (a["lat"], a["lon"]) == (b["lat"], b["lon"])  # noqa: E731
    end = min(k, len(ranked))  # pairs (i, i+1) for i < end decide the top k
    while 0 < end < len(ranked) and same(ranked[end][1], ranked[end - 1][1]):
        end += 1
    pairs = zip(ranked[:end], ranked[1:end + 1])
    safe = [(b[0] - a[0]) / 2 for a, b in pairs if not same(a[1], b[1])]
    if hood and match == "inside":
        safe.append(distance_to_boundary_m(lat, lon, hood["polygon"]))
    recheck = round(min(max(min(safe, default=RECHECK_MAX_M), RECHECK_MIN_M), RECHECK_MAX_M))
    return {"location": {"lat": lat, "lon": lon, "match": match, "neighbourhood": hood and hood["neighbourhood"],
                         "district_id": hood and hood["district_id"]},
            "nearest_stations": [{f: s.get(f) for f in TRACK_FIELDS} for s in near],
            "recheck_after_m": recheck}


def here(d, lat, lon, k):
    """Everything the map needs for one position: zone (air + heat, 24 h curves), nearest stations, city context."""
    loc = locate(d, lat, lon)
    z = zone(d, loc["district_id"]) if loc["district_id"] is not None else None
    city_air, city_heat = air(d)["city"], heat(d)["city"]
    return {"location": loc, "zone": z and z["zone"], "nearest_stations": nearest(d, lat, lon, k),
            "city": {"air": city_air, "heat": city_heat}}


# ---------- One station ----------
def station(d, station_id):
    """Hourly air + heat for one station over the last 24 h, or None if unknown."""
    rows = [r for r in d["rows"] if r["station_id"] == station_id]
    if not rows:
        return None
    return {"station": _info(rows[-1], d["locations"]),
            "hourly": [{**_time(r["_t"]), **_air_row(r), **_heat_row(r), "pressure": r.get("pressure")} for r in rows]}
