# GET /api/heat                 → city temperature now, hottest/coolest, peak hour, hourly curve (24 h)
# GET /api/heat?station_id=102  → one station, hourly air + heat (24 h)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import env  # noqa: E402
from athens.http import HttpError, int_param, make_handler, with_meta  # noqa: E402


def get(q):
    sid = int_param(q, "station_id")
    d, meta = env.data()
    if sid is None:
        return with_meta(env.heat(d), meta)
    out = env.station(d, sid)
    if out is None:
        raise HttpError(404, f"no recent data for station {sid}")
    return with_meta(out, meta)


handler = make_handler("/api/heat", get)
