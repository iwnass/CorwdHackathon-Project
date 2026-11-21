"""Next metro (M1–M3) and tram (T6/T7) departures from data/metro.json, built by scripts/build_metro.py from the
official STASY timetable (GTFS on data.gov.gr). There is no live train data: these are timetable estimates, and the
latest timetable STASY published may be older than today (see `timetable_valid`).

shortcut: Greek public holidays run on the Sunday timetable — not handled; they use their weekday's timetable.
"""
import json
import os
from datetime import datetime, timedelta

from .geo import haversine
from .places import transliterate
from .times import iso_local, now_utc

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "metro.json")
_data = {}


def data():
    if not _data:
        with open(PATH, encoding="utf-8") as f:
            _data.update(json.load(f))
    return _data


def _day_type(d):
    return {5: "saturday", 6: "sunday"}.get(d.weekday(), "weekday")


def _hhmm(minute):
    return "%02d:%02d" % divmod(minute % 1440, 60)


def info():
    d = data()
    f, t = d["valid_from"], d["valid_to"]
    return {"estimated": True, "timetable_valid": f"{f[:4]}-{f[4:6]}-{f[6:]} – {t[:4]}-{t[4:6]}-{t[6:]}",
            "source": "STASY timetable (GTFS, data.gov.gr)"}


def station(s):
    return {"id": s["id"], "name": s["name"], "name_en": transliterate(s["name"]), "lat": s["lat"], "lon": s["lon"],
            "lines": s["lines"], "step_free": s["step_free"]}


def departures(station_id, now=None, n=3):
    """Per line and direction: the next n departures, minutes until them, first and last train today."""
    local = datetime.fromisoformat(iso_local(now or now_utc()))
    minute, today, yesterday = local.hour * 60 + local.minute, local.date(), local.date() - timedelta(days=1)
    deps = data()["departures"]
    out = []
    for key, times in deps[_day_type(today)].get(station_id, {}).items():
        # trains after midnight belong to yesterday's timetable (times ≥ 24:00 there)
        late = [m - 1440 for m in deps[_day_type(yesterday)].get(station_id, {}).get(key, []) if m >= 1440]
        upcoming = [m for m in late + times if m >= minute][:n]
        line, towards = key.split("|", 1)
        out.append({"line": line, "towards": towards, "towards_en": transliterate(towards),
                    "next": [_hhmm(m) for m in upcoming], "in_min": [m - minute for m in upcoming],
                    "first": _hhmm(times[0]), "last": _hhmm(times[-1])})
    return sorted(out, key=lambda x: (x["in_min"][:1] or [10 ** 6], x["line"]))


def near(lat, lon, radius_m=1000, k=2, now=None):
    """The k nearest stations within radius_m, each with its next departures."""
    found = sorted((haversine(lat, lon, s["lat"], s["lon"]), s["id"], s) for s in data()["stations"])
    return [{**station(s), "distance_m": round(d), "departures": departures(s["id"], now)}
            for d, _, s in found if d <= radius_m][:k]
