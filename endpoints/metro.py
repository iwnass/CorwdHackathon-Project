# GET /api/metro                → every metro/tram station (lines, step-free access) + timetable info
# GET /api/metro?station=233    → next departures per line and direction, first/last train today
#   Timetable estimates (no live train data from STASY). Same for every user → CDN-cached; "near me" is in /api/here.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import metro  # noqa: E402
from athens.http import HttpError, make_handler  # noqa: E402


def get(q):
    sid = q.get("station")
    if sid is None:
        return {**metro.info(), "stations": [metro.station(s) for s in metro.data()["stations"]]}
    s = next((s for s in metro.data()["stations"] if s["id"] == sid), None)
    if s is None:
        raise HttpError(404, f"unknown station {sid}")
    return {**metro.info(), "station": metro.station(s), "departures": metro.departures(sid)}


handler = make_handler("/api/metro", get, cache="public, max-age=30, s-maxage=30")
