# GET /api/zones                → air quality per municipal district (7 zones), worst first, with 24 h curves
# GET /api/zones?district_id=6  → one zone with its stations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import env  # noqa: E402
from athens.http import HttpError, int_param, make_handler, with_meta  # noqa: E402


def get(q):
    did = int_param(q, "district_id")
    d, meta = env.data()
    if did is None:
        return with_meta(env.zones(d), meta)
    out = env.zone(d, did)
    if out is None:
        raise HttpError(404, f"unknown district {did}; districts are {sorted(d['districts'])}")
    return with_meta(out, meta)


handler = make_handler("/api/zones", get)
