"""Build data/metro.json from the official STASY GTFS (metro M1–M3, tram T6/T7) on data.gov.gr.

The raw feed is ~8 MB / 1.8 M stop times — too heavy to parse in a serverless request — so this keeps only what
"next trains" needs: per station, line and direction, the departure minutes of one weekday (a Tuesday), one
Saturday and one Sunday (the latest of each in the feed). Run again whenever STASY publishes a new timetable:
    python3 scripts/build_metro.py [gtfs.zip]        (default: download from data.gov.gr)
"""
import csv
import io
import json
import os
import sys
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date

URL = ("https://data.gov.gr/dataset/4e897a75-975a-4ce7-af65-f32ea01f93b9/resource/"
       "5e3858ee-d9ba-48c2-9015-744ea160976d/download/stasy_gtfs.zip")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "metro.json")


def weekday(d):
    return date(int(d[:4]), int(d[4:6]), int(d[6:])).weekday()


def day_type(d):
    return {5: "saturday", 6: "sunday"}.get(weekday(d), "weekday")


def main(path=None):
    raw = open(path, "rb").read() if path else urllib.request.urlopen(URL, timeout=120).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    rows = lambda n: csv.DictReader(io.TextIOWrapper(z.open(n), encoding="utf-8-sig"))  # noqa: E731

    service_of = {r["date"]: r["service_id"] for r in rows("calendar_dates.txt") if r["exception_type"] == "1"}
    dates = sorted(service_of)
    pick = {}
    for d in reversed(dates):  # the latest Tuesday, Saturday and Sunday in the feed
        t = day_type(d)
        if t not in pick and (t != "weekday" or weekday(d) == 1):
            pick[t] = d
    services = {service_of[d]: t for t, d in pick.items()}

    line = {r["route_id"]: r["route_short_name"] for r in rows("routes.txt")}
    trips = {r["trip_id"]: (line[r["route_id"]], services[r["service_id"]]) for r in rows("trips.txt")
             if r["service_id"] in services}
    stops = {r["stop_id"]: r for r in rows("stops.txt")}

    by_trip = defaultdict(list)
    for r in rows("stop_times.txt"):
        if r["trip_id"] in trips:
            h, m, _ = (int(x) for x in r["departure_time"].split(":"))
            by_trip[r["trip_id"]].append((int(r["stop_sequence"]), r["stop_id"], h * 60 + m))
    deps = {t: defaultdict(lambda: defaultdict(list)) for t in pick}  # day type → stop → "M1|terminus" → minutes
    lines_at = defaultdict(set)
    for trip, seq in by_trip.items():
        seq.sort()
        ln, t = trips[trip]
        towards = stops[seq[-1][1]]["stop_name"]  # the feed has no headsigns for the metro: use the last stop
        for _, stop, minute in seq[:-1]:  # no departure from the stop where the train ends
            deps[t][stop][f"{ln}|{towards}"].append(minute)
            lines_at[stop].add(ln)

    # the feed has one stop per platform (Syntagma = 4): merge stops with the same name and place into one station
    station_of, members = {}, defaultdict(list)
    for s, r in stops.items():
        if lines_at[s]:
            members[(r["stop_name"], round(float(r["stop_lat"]), 4), round(float(r["stop_lon"]), 4))].append(s)
    stations = []
    for (name, _, _), ids in members.items():
        sid = min(ids, key=int)
        for s in ids:
            station_of[s] = sid
        r = stops[sid]
        stations.append({"id": sid, "name": name, "lat": float(r["stop_lat"]), "lon": float(r["stop_lon"]),
                         # step-free only if every platform is: an accessibility flag must not overclaim
                         "step_free": all(stops[s].get("wheelchair_boarding") == "1" for s in ids),
                         "lines": sorted(set().union(*(lines_at[s] for s in ids)))})
    merged = {t: defaultdict(lambda: defaultdict(list)) for t in pick}
    for t, st in deps.items():
        for s, d in st.items():
            for k, v in d.items():
                merged[t][station_of[s]][k] += v
    out = {"source": URL, "valid_from": dates[0], "valid_to": dates[-1], "days": pick, "stations": stations,
           "departures": {t: {s: {k: sorted(v) for k, v in d.items()} for s, d in st.items()} for t, st in merged.items()}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    n = sum(len(v) for st in out["departures"].values() for d in st.values() for v in d.values())
    print(f"{OUT}: {len(stations)} stations, {n} departures, days {pick}, valid {dates[0]}–{dates[-1]}, "
          f"{os.path.getsize(OUT) // 1024} KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
