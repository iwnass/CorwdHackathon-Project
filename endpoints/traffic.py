# GET /api/traffic                          → footfall per WiFi station (latest day) + city daily totals
# GET /api/traffic?station_id=113&days=30   → one station, daily series (1–90 days)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import traffic  # noqa: E402
from athens.http import HttpError, int_param, make_handler, with_meta  # noqa: E402


def get(q):
    sid = int_param(q, "station_id")
    days = int_param(q, "days", 30, 1, traffic.MAX_HISTORY_DAYS)
    d, meta = traffic.data()
    if sid is None:
        return with_meta(traffic.overview(d), meta)
    out = traffic.history(d, sid, days)
    if out is None:
        raise HttpError(404, f"unknown WiFi station {sid}")
    body, meta = out
    return with_meta({"kind": "wifi_footfall", **body}, meta)


handler = make_handler("/api/traffic", get)
