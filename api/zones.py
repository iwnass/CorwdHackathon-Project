# GET /api/zones                → air quality per municipal district (7 zones), worst first, with 24 h curves
# GET /api/zones?district_id=6  → one zone with its stations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import env, traffic  # noqa: E402
from athens.http import HttpError, int_param, make_handler, with_meta  # noqa: E402


def _footfall():
    try:  # WiFi footfall per district is extra; air and heat still answer
        return traffic.by_district(traffic.data()[0])
    except Exception:
        return {}


def get(q):
    did = int_param(q, "district_id")
    d, meta = env.data()
    if did is None:
        body, foot = env.zones(d), _footfall()
        for z in body["zones"]:
            z["footfall"] = foot.get(z["district_id"])
        return with_meta(body, meta)
    out = env.zone(d, did)
    if out is None:
        raise HttpError(404, f"unknown district {did}; districts are {sorted(d['districts'])}")
    out["zone"]["footfall"] = _footfall().get(did)
    return with_meta(out, meta)


handler = make_handler("/api/zones", get)
