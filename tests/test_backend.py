import importlib.util
import io
import json
import os
import sys
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from athens import cache, ckan, env, events, traffic  # noqa: E402
from athens.geo import distance_to_boundary_m, haversine, in_polygon, parse_wkt_polygon  # noqa: E402
from athens.http import ROUTES, HttpError, float_param, int_param, run  # noqa: E402
from athens.indices import eaqi_label, heat_index, heat_level, pollution, pollution_level, us_aqi, us_aqi_category  # noqa: E402


def fake_ckan(packages=(), datastore=None, show=None):
    """A stand-in for http_get: routes CKAN actions to the given dicts."""
    datastore, show, calls = datastore or {}, show or {}, []

    def get(url):
        u = urlparse(url)
        action, q = u.path.rsplit("/", 1)[-1], {k: v[0] for k, v in parse_qs(u.query).items()}
        calls.append((action, q))
        if action == "package_search":
            prefix = q["fq"][len("name:"):-1]
            result = {"count": 0, "results": [p for p in packages if p["name"].startswith(prefix)]}
        elif action == "package_show":
            result = show[q["id"]]
        elif action == "datastore_search":
            rows = datastore[q["resource_id"]]
            if "filters" in q:
                f = json.loads(q["filters"])
                rows = [r for r in rows if all(r.get(k) == v for k, v in f.items())]
            result = {"records": rows[: int(q.get("limit", 100))]}
        else:
            raise AssertionError(url)
        return json.dumps({"success": True, "result": result}).encode()

    get.calls = calls
    return get


def pkg(name, rid, lat=None, lon=None, hood=None):
    sc = [{"centroid": json.dumps({"type": "Point", "coordinates": [lon, lat]}), "text": hood}] if lat else []
    return {"name": name, "spatial_coverage": sc, "resources": [{"id": rid, "datastore_active": True}]}


HOODS = {"neighbourhoods-athens": pkg("neighbourhoods-athens", "hoods"),
         "municipal-districts-athens": pkg("municipal-districts-athens", "districts")}
HOOD_ROWS = [{"name": "ΚΟΥΚΑΚΙ", "friendly_name": "Κουκάκι", "position_lat": "37.9640", "position_lon": "23.7260",
              "municipal_district_id": "4"},
             {"name": "ΚΥΨΕΛΗ", "friendly_name": "Κυψέλη", "position_lat": "38.0000", "position_lon": "23.7400",
              "municipal_district_id": "6",
              "polygon_geo": "POLYGON ((23.735 37.995, 23.745 37.995, 23.745 38.005, 23.735 38.005, 23.735 37.995))"},
             {"name": "ΑΓΙΟΣ ΝΙΚΟΛΑΟΣ", "position_lat": "38.0100", "position_lon": "23.7300", "municipal_district_id": "6"}]
DISTRICT_ROWS = [{"id": str(i), "name": f"{i}ο Δημοτικό Διαμέρισμα Αθήνας"} for i in range(1, 8)]


def env_row(sid, ts, **kw):
    base = {"station_id": sid, "station_name": f"Σταθμός {sid}_101", "neighbourhood_name": kw.pop("hood", "ΚΥΨΕΛΗ"),
            "municipal_district_id": 6, "timestamp": ts, "aqi": 2, "temperature": 20.0, "humidity": 50.0,
            "pm2_5": 10.0, "pm10": 20.0, "no2": 10.0, "o3": 50.0}
    return {**base, **kw}


class Indices(unittest.TestCase):
    def test_us_aqi_breakpoints(self):
        self.assertEqual(us_aqi(9.0, None), 50)
        self.assertEqual(us_aqi(35.4, None), 100)
        self.assertEqual(us_aqi(35.49, None), 100)  # truncated to 35.4, not rounded to 35.5
        self.assertEqual(us_aqi(None, 154), 100)
        self.assertEqual(us_aqi(15.0, 200), 123)    # the worse pollutant wins
        self.assertEqual(us_aqi(1000, None), 500)
        self.assertIsNone(us_aqi(None, None))

    def test_pollution_pct(self):
        self.assertEqual(pollution({"pm2_5": 10}), (17, "Good", "pm2_5"))      # top of band 1 is still Good
        self.assertEqual(pollution({"pm2_5": 15}), (25, "Fair", "pm2_5"))      # middle of band 2
        self.assertEqual(pollution({"pm2_5": 10, "no2": 100})[::2], (39, "no2"))  # the worst pollutant decides
        self.assertEqual(pollution({"pm2_5": 10, "no2": 100})[1], "Moderate")
        self.assertEqual(pollution({"pm10": 5000}), (100, "Extremely poor", "pm10"))
        self.assertEqual(pollution({"pm2_5": "x", "co": 300}), (None, None, None))  # CO has no EAQI band
        self.assertEqual([pollution_level(p) for p in (0, 16, 17, 50, 51, 100)],
                         ["Good", "Good", "Fair", "Moderate", "Poor", "Extremely poor"])

    def test_categories(self):
        self.assertEqual(us_aqi_category(50), "Good")
        self.assertEqual(us_aqi_category(101), "Unhealthy for sensitive groups")
        self.assertEqual(eaqi_label(2), "Fair")
        self.assertIsNone(eaqi_label(None))

    def test_heat_index(self):
        self.assertEqual(heat_index(20.0, 50.0), 20.0)       # mild: feels like the air
        self.assertAlmostEqual(heat_index(32.2, 70), 41.1, delta=0.5)  # NWS table: 90 °F, 70 % → 106 °F
        self.assertEqual(heat_level(heat_index(32.2, 70)), "danger")
        self.assertEqual(heat_level(25.0), "none")
        self.assertIsNone(heat_index(None, 50))


class Times(unittest.TestCase):
    def test_dst_fallback_without_tz_database(self):
        from athens import times
        with mock.patch.object(times, "ATHENS", None):
            self.assertTrue(times.iso_local(times.parse_utc("2026-07-01T09:00:00")).endswith("12:00+03:00"))
            self.assertTrue(times.iso_local(times.parse_utc("2026-11-21T09:00:00")).endswith("11:00+02:00"))
            self.assertTrue(times.iso_local(times.parse_utc("2026-03-29T00:59:00")).endswith("02:59+02:00"))
            self.assertTrue(times.iso_local(times.parse_utc("2026-03-29T01:00:00")).endswith("04:00+03:00"))


class Geo(unittest.TestCase):
    def test_haversine(self):
        self.assertAlmostEqual(haversine(37.9755, 23.7348, 37.9842, 23.7281), 1135, delta=20)  # Syntagma → Omonia

    def test_polygon_with_hole(self):
        rings = parse_wkt_polygon("POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0), (4 4, 6 4, 6 6, 4 6, 4 4))")
        self.assertEqual(len(rings), 2)
        self.assertTrue(in_polygon(2, 2, rings))       # lat, lon
        self.assertFalse(in_polygon(5, 5, rings))      # in the hole
        self.assertFalse(in_polygon(20, 2, rings))
        self.assertIsNone(parse_wkt_polygon("POINT (1 2)"))

    def test_distance_to_boundary(self):
        sq = parse_wkt_polygon("POLYGON ((23.73 37.99, 23.75 37.99, 23.75 38.01, 23.73 38.01, 23.73 37.99))")
        self.assertAlmostEqual(distance_to_boundary_m(38.0, 23.74, sq), 877, delta=10)    # 0.01° of longitude
        self.assertAlmostEqual(distance_to_boundary_m(38.009, 23.74, sq), 111, delta=3)   # 0.001° below the top edge
        self.assertIsNone(parse_wkt_polygon(None))


class Ckan(unittest.TestCase):
    def test_station_number(self):
        self.assertEqual(ckan.station_number("env-102-fokionos-negri"), 102)
        self.assertEqual(ckan.station_number("wifi-cumulative-traffic-113-fokionos-negri"), 113)
        self.assertIsNone(ckan.station_number("env-all-stations"))

    def test_location(self):
        self.assertEqual(ckan.location(pkg("x", "r", 38.0, 23.7, "ΚΥΨΕΛΗ")), {"lat": 38.0, "lon": 23.7, "neighbourhood": "ΚΥΨΕΛΗ"})
        bbox = {"spatial_coverage": [{"bbox": json.dumps({"coordinates": [[[23.0, 37.0], [24.0, 38.0]]]})}]}
        self.assertEqual(ckan.location(bbox)["lat"], 37.5)
        self.assertIsNone(ckan.location({"spatial_coverage": [{"centroid": "not json"}]}))

    def test_clean_name(self):
        self.assertEqual(ckan.clean_name("Φωκίωνος Νέγρη_206"), "Φωκίωνος Νέγρη")

    def test_error_response(self):
        get = lambda url: json.dumps({"success": False, "error": {"message": "nope"}}).encode()  # noqa: E731
        with self.assertRaises(ckan.CkanError):
            ckan.action("package_show", {"id": "x"}, get)


class Cache(unittest.TestCase):
    def setUp(self):
        cache.clear()

    def test_hit_then_expire(self):
        calls = []
        with mock.patch("athens.cache.time.time", return_value=1000):
            cache.cached("k", 60, lambda: calls.append(1) or "a")
            cache.cached("k", 60, lambda: calls.append(1) or "b")
        self.assertEqual(len(calls), 1)
        with mock.patch("athens.cache.time.time", return_value=1061):
            v, meta = cache.cached("k", 60, lambda: "c")
        self.assertEqual((v, meta["stale"]), ("c", False))

    def test_stale_on_error(self):
        def boom():
            raise OSError("city API down")
        with mock.patch("athens.cache.time.time", return_value=1000):
            cache.cached("k", 60, lambda: "old")
        with mock.patch("athens.cache.time.time", return_value=2000):
            v, meta = cache.cached("k", 60, boom)
        self.assertEqual((v, meta["stale"]), ("old", True))
        with self.assertRaises(OSError):
            cache.cached("other", 60, boom)

    def test_backs_off_after_failure(self):
        calls = []

        def boom():
            calls.append(1)
            raise OSError("down")
        with mock.patch("athens.cache.time.time", return_value=1000):
            cache.cached("k", 60, lambda: "old")
        with mock.patch("athens.cache.time.time", return_value=2000):
            cache.cached("k", 60, boom)
            cache.cached("k", 60, boom)  # within the back-off: no second call to a dead API
        self.assertEqual(len(calls), 1)

    def test_bounded(self):
        with mock.patch.object(cache, "MAX_ENTRIES", 3):
            for i in range(10):
                cache.cached(f"k{i}", 60, lambda: i)
            self.assertEqual(cache.status()["entries"], 3)


class Env(unittest.TestCase):
    def build(self, rows):
        get = fake_ckan(
            packages=[pkg("env-all-stations", "all"), pkg("env-001-kypseli", "r1", 38.0, 23.74, "ΚΥΨΕΛΗ"),
                      pkg("env-002-x", "r2", 37.98, 23.73, "ΕΞΑΡΧΕΙΑ")],
            datastore={"all": rows, "hoods": HOOD_ROWS, "districts": DISTRICT_ROWS}, show=HOODS)
        return env.load(get)

    def test_window_hours_and_locations(self):
        rows = [env_row(1, "2026-11-21T09:00:00", temperature=24.0),
                env_row(1, "2026-11-21T09:36:57", temperature=25.0),  # stray reading → same hour, newer wins
                env_row(2, "2026-11-21T08:00:00", temperature=18.0),
                env_row(9, "2026-11-21T09:00:00", hood="ΚΟΥΚΑΚΙ"),     # no own dataset → neighbourhood centre
                env_row(1, "2026-11-20T09:00:00")]                     # 24 h old → outside the window
        d = self.build(rows)
        self.assertEqual(len(d["rows"]), 3)
        self.assertEqual([r["temperature"] for r in d["rows"] if r["station_id"] == 1], [25.0])
        self.assertEqual(d["locations"][9]["lat"], 37.964)

        h = env.heat(d)
        self.assertEqual(h["stations"][0]["station_id"], 1)  # hottest first
        self.assertEqual(h["city"]["peak_hour_24h"]["time"], "2026-11-21T09:00:00Z")
        self.assertEqual(h["city"]["peak_hour_24h"]["time_local"], "2026-11-21T11:00+02:00")
        self.assertEqual([x["time"] for x in h["hourly"]], ["2026-11-21T08:00:00Z", "2026-11-21T09:00:00Z"])

    def test_faulty_sensor_is_flagged_not_averaged(self):
        rows = [env_row(1, "2026-11-21T09:00:00", pm2_5=10.0, pm10=20.0),
                env_row(2, "2026-11-21T09:00:00", pm2_5=1800.0, pm10=1900.0, aqi=6)]
        a = env.air(self.build(rows))
        self.assertEqual(a["city"]["details"]["pm2_5_avg"], 10.0)
        self.assertEqual((a["city"]["pollution_pct_avg"], a["city"]["pollution_pct_max"]), (17, 17))
        self.assertIsNone(a["stations"][-1]["pollution_pct"])  # faulty: no false 100 %
        self.assertEqual(a["stations"][-1]["details"]["pm2_5"], 1800.0)  # raw value still there for the analytic view
        self.assertEqual(a["city"]["suspect"], [2])
        self.assertEqual(a["city"]["worst"], [1])
        self.assertTrue(a["stations"][-1]["suspect"])
        self.assertEqual((a["hourly"][0]["pollution_pct_avg"], a["hourly"][0]["details"]["pm2_5_avg"]), (17, 10.0))

    def test_string_numbers_and_bad_clock(self):
        rows = [env_row("1", "2026-11-21T09:00:00", pm2_5="12.5", temperature="21.5", humidity="40", aqi="2"),
                env_row(2, "2026-11-21T09:00:00", temperature="n/a"),
                env_row(7, "2099-01-01T00:00:00")]  # wrong clock: ignored, does not move the window
        d = self.build(rows)
        self.assertEqual(sorted(r["station_id"] for r in d["rows"]), [1, 2])
        a, h = env.air(d), env.heat(d)
        s1 = next(s for s in a["stations"] if s["station_id"] == 1)
        self.assertEqual((s1["details"]["pm2_5"], s1["details"]["aqi_label"], s1["lat"]), (12.5, "Fair", 38.0))
        self.assertEqual((s1["pollution_pct"], s1["pollution_level"]), (21, "Fair"))
        self.assertNotIn("pm2_5", s1)  # chemicals only inside details
        self.assertEqual(h["stations"][0]["temperature"], 21.5)
        self.assertIsNone(h["stations"][1]["temperature"])

    def test_zones_are_municipal_districts(self):
        rows = [env_row(1, "2026-11-21T09:00:00", pm2_5=40.0, temperature=20.0, municipal_district_id=6),
                env_row(2, "2026-11-21T09:00:00", pm2_5=5.0, temperature=22.0, municipal_district_id=6),
                env_row(3, "2026-11-21T09:00:00", pm2_5=60.0, temperature=18.0, municipal_district_id="4"),
                env_row(4, "2026-11-21T09:00:00", pm2_5=900.0, temperature=19.0, municipal_district_id=4),  # faulty PM
                env_row(9, "2026-11-21T09:00:00", hood="ΚΟΥΚΑΚΙ", temperature=17.0, municipal_district_id=None)]
        d = self.build(rows)
        z = env.zones(d)
        self.assertEqual(len(z["zones"]), 7)                                    # every district is a zone
        self.assertEqual(z["ranking"]["worst_air"][:2], [4, 6])
        self.assertEqual(z["ranking"]["hottest"][:2], [6, 4])
        z4, z6 = z["zones"][0], z["zones"][1]
        self.assertEqual((z4["name"], z4["stations_count"]), ("4ο Δημοτικό Διαμέρισμα Αθήνας", 3))
        self.assertEqual((z4["air"]["stations"], z4["air"]["suspect"], z4["air"]["details"]["pm2_5_avg"]), (2, [4], 35.0))
        self.assertEqual((z4["heat"]["stations"], z4["heat"]["temperature_avg"]), (3, 18.0))  # PM fault ≠ bad thermometer
        self.assertEqual((z6["air"]["details"]["pm2_5_avg"], z6["heat"]["temperature_avg"], z6["heat"]["hottest"]), (22.5, 21.0, [2, 1]))
        self.assertEqual(len(z6["heat"]["hourly"]), 1)
        self.assertEqual((z6["lat"], z6["neighbourhoods"]), (38.005, ["ΑΓΙΟΣ ΝΙΚΟΛΑΟΣ", "Κυψέλη"]))
        self.assertEqual((z["zones"][-1]["stations_count"], z["zones"][-1]["air"]), (0, None))
        one = env.zone(d, 6)["zone"]
        self.assertEqual([(s["station_id"], s["temperature"]) for s in sorted(one["stations"], key=lambda s: s["station_id"])],
                         [(1, 20.0), (2, 22.0)])
        self.assertIsNone(env.zone(d, 99))

    def test_here(self):
        d = self.build([env_row(1, "2026-11-21T09:00:00", municipal_district_id=6),
                        env_row(2, "2026-11-21T09:00:00", municipal_district_id=6, pm2_5=30.0),
                        env_row(5, "2026-11-21T09:00:00", municipal_district_id=6, pm2_5=1800.0),  # faulty: never "nearest"
                        env_row(3, "2026-11-21T09:00:00", municipal_district_id=4, hood="ΚΟΥΚΑΚΙ")])
        inside = env.locate(d, 38.001, 23.741)
        self.assertEqual((inside["match"], inside["neighbourhood"], inside["district_id"]), ("inside", "Κυψέλη", 6))
        edge = env.locate(d, 38.0060, 23.7400)  # just outside the polygon, 500 m from its centre
        self.assertEqual((edge["match"], edge["district_id"]), ("nearest", 6))
        self.assertEqual(env.locate(d, 40.64, 22.94)["match"], "outside")  # Thessaloniki

        h = env.here(d, 38.001, 23.741, 2)
        self.assertEqual(h["zone"]["district_id"], 6)
        self.assertEqual((h["zone"]["air"]["stations"], h["zone"]["air"]["suspect"]), (2, [5]))
        self.assertIsNotNone(h["zone"]["heat"]["temperature_avg"])
        self.assertEqual([s["station_id"] for s in h["nearest_stations"]], [1, 2])  # both at Kypseli's centre
        self.assertIn("temperature", h["nearest_stations"][0])
        self.assertIn("distance_m", h["nearest_stations"][0])
        self.assertIsNone(env.here(d, 40.64, 22.94, 2)["zone"])

    def test_track_is_light_and_recheck_is_safe(self):
        import random
        rows = [env_row(i, "2026-11-21T09:00:00", municipal_district_id=6, hood="ΚΟΥΚΑΚΙ" if i % 2 else "ΚΥΨΕΛΗ")
                for i in range(1, 7)]
        d = self.build(rows)
        rnd = random.Random(3)
        for i in range(10, 30):
            d["locations"][i] = {"lat": 37.99 + rnd.random() * 0.02, "lon": 23.73 + rnd.random() * 0.02}
            d["rows"].append({**d["rows"][0], "station_id": i})
        t = env.track(d, 38.001, 23.741, 3)
        self.assertEqual((t["location"]["match"], t["location"]["district_id"]), ("inside", 6))
        self.assertEqual(len(t["nearest_stations"]), 3)
        self.assertNotIn("hourly", json.dumps(t))
        self.assertTrue(1 <= t["recheck_after_m"] <= 500)
        # the promise: moving less than recheck_after_m never changes the answer
        for _ in range(200):
            lat, lon = 37.995 + rnd.random() * 0.01, 23.735 + rnd.random() * 0.01
            a = env.track(d, lat, lon, 3)
            r = a["recheck_after_m"] * 0.99
            ang = rnd.random() * 6.283
            lat2 = lat + r * __import__("math").sin(ang) / 110540
            lon2 = lon + r * __import__("math").cos(ang) / (111320 * __import__("math").cos(__import__("math").radians(lat)))
            b = env.track(d, lat2, lon2, 3)
            if a["recheck_after_m"] > 1:  # the 1 m floor is a rate limit, not a guarantee
                self.assertEqual([s["station_id"] for s in a["nearest_stations"]], [s["station_id"] for s in b["nearest_stations"]])
                self.assertEqual(a["location"]["neighbourhood"], b["location"]["neighbourhood"])

    def test_station(self):
        d = self.build([env_row(1, "2026-11-21T08:00:00"), env_row(1, "2026-11-21T09:00:00")])
        self.assertEqual(len(env.station(d, 1)["hourly"]), 2)
        self.assertIsNone(env.station(d, 404))


class Traffic(unittest.TestCase):
    def setUp(self):
        cache.clear()
        reg = [{"station_id": 1, "station_name": "Πλατεία Α_010", "station_address": "Οδός 1", "neighbourhood_name": "Α",
                "municipal_district_id": 1, "municipal_district_name": "1ο",
                "agg_cumulative_traffic_resource_id": "v", "agg_active_visitors_resource_id": "a",
                "agg_highest_visitors_resource_id": "p"},
               {"station_id": 2, "station_name": "Πλατεία Β", "neighbourhood_name": "Β",
                "agg_cumulative_traffic_resource_id": "v", "agg_active_visitors_resource_id": "a",
                "agg_highest_visitors_resource_id": "p"}]
        days = [f"2026-11-{d:02d}" for d in range(13, 21)]  # 13 … 20
        visits = [{"station_id": 1, "date": x, "cumulative_traffic": 1000} for x in days]
        visits[-1]["cumulative_traffic"] = 2000              # station 1 doubles on the 20th
        visits += [{"station_id": 2, "date": x, "cumulative_traffic": 500} for x in days[:-1]]  # not published yet for the 20th
        visits.reverse()                                      # API returns newest first
        self.get = fake_ckan(
            packages=[pkg("wifi-cumulative-traffic-001-a", "x", 37.99, 23.73, "Α")],
            datastore={"reg": reg, "v": visits,
                       "a": [{"station_id": 1, "date": "2026-11-20", "active_visitors": 50}],
                       "p": [{"station_id": 1, "date": "2026-11-20", "highest_visitors": 70}]},
            show={"wifi-stations-registry": pkg("wifi-stations-registry", "reg")})

    def test_overview(self):
        o = traffic.overview(traffic.load(self.get))
        s1, s2 = o["stations"]
        self.assertEqual((s1["station_id"], s1["visits"], s1["visitors"], s1["peak_visitors"]), (1, 2000, 50, 70))
        self.assertEqual((s1["visits_7d_avg"], s1["change_vs_7d_pct"], s1["busyness"]), (1000, 100.0, "busy"))
        self.assertEqual((s1["name"], s1["lat"]), ("Πλατεία Α", 37.99))
        self.assertEqual((s2["date"], s2["lat"]), ("2026-11-19", None))
        # only station 1 reported on the 20th → the 7-day average is over station 1 only (1000), not 1500
        self.assertEqual(o["city"]["date"], "2026-11-20")
        self.assertEqual((o["city"]["visits"], o["city"]["visits_7d_avg"], o["city"]["busyness"]), (2000, 1000, "busy"))

    def test_gaps_use_calendar_days(self):
        d = traffic.load(self.get)
        d["days"][1] = {"2026-11-01": {"visits": 9999}, "2026-11-18": {"visits": 1000}, "2026-11-20": {"visits": 1000}}
        s1 = next(s for s in traffic.overview(d)["stations"] if s["station_id"] == 1)
        self.assertIsNone(s1["visits_prev_day"])   # the 19th is missing; the 18th is not "yesterday"
        self.assertEqual(s1["visits_7d_avg"], 1000)  # the 1st is outside the 7 days

    def test_city_skips_barely_published_day(self):
        d = traffic.load(self.get)
        d["days"][3] = {f"2026-11-{x}": {"visits": 10} for x in range(13, 21)}
        d["stations"][3] = {"station_id": 3}
        d["days"][2]["2026-11-21"] = {"visits": 5}  # 1 of 3 stations so far on the 21st
        self.assertEqual(traffic.overview(d)["city"]["date"], "2026-11-20")

    def test_history(self):
        d = traffic.load(self.get)
        body, _ = traffic.history(d, 1, 3, self.get)
        self.assertEqual([x["date"] for x in body["daily"]], ["2026-11-18", "2026-11-19", "2026-11-20"])
        self.assertEqual(body["daily"][-1], {"date": "2026-11-20", "visits": 2000, "visitors": 50, "peak_visitors": 70})
        self.assertIsNone(traffic.history(d, 99, 3, self.get))
        n = len(self.get.calls)
        body, _ = traffic.history(d, 1, 7, self.get)  # other ?days= → same cache entry, no new calls
        self.assertEqual((len(body["daily"]), len(self.get.calls)), (7, n))


def tm_event(i, days_ahead, **kw):
    from datetime import timedelta
    from athens.times import iso_utc, now_utc
    start = now_utc() + timedelta(days=days_ahead)
    ev = {"id": f"e{i}", "name": f"Event {i}", "url": f"https://tm/e{i}",
          "images": [{"ratio": "4_3", "url": "small", "width": 300}, {"ratio": "16_9", "url": "wide", "width": 1024}],
          "dates": {"start": {"localDate": start.date().isoformat(), "localTime": "20:00:00", "dateTime": iso_utc(start)},
                    "status": {"code": kw.pop("status", "onsale")}},
          "classifications": [{"primary": True, "segment": {"name": kw.pop("segment", "Music")}, "genre": {"name": "Rock"}}],
          "priceRanges": [{"min": 25.0, "max": 60.0, "currency": "EUR"}],
          "_embedded": {"venues": [{"name": "Gazi Music Hall", "city": {"name": "Athens"}, "address": {"line1": "Iera Odos 1"},
                                    "location": {"latitude": str(kw.pop("lat", 37.978)), "longitude": "23.712"}}],
                        "attractions": [{"name": "Band"}]}}
    ev.update(kw)
    return ev


class Events(unittest.TestCase):
    def setUp(self):
        cache.clear()

    def fake_tm(self, pages):
        calls = []

        def get(url):
            q = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
            calls.append(q)
            n = int(q["page"])
            return json.dumps({"_embedded": {"events": pages[n]},
                               "page": {"totalElements": sum(map(len, pages)), "totalPages": len(pages), "number": n}}).encode()
        get.calls = calls
        return get

    def test_load_normalize_and_filter(self):
        pages = [[tm_event(1, 2), tm_event(2, 5, segment="Sports"), tm_event(3, 6, status="cancelled")],
                 [tm_event(1, 2), tm_event(4, 60, lat=38.05),  # page 2 repeats e1 (paging overlap)
                  tm_event(5, 3, name="TO BE DELETED_RED"), tm_event(6, 4, name="Event 1", segment="Undefined")]]
        get = self.fake_tm(pages)
        with mock.patch.dict(os.environ, {"TICKETMASTER_API_KEY": "k123"}):
            d = events.load(get)
        self.assertEqual(len(get.calls), 2)
        q = get.calls[0]
        self.assertEqual((q["apikey"], q["latlong"], q["sort"]), ("k123", "37.9838,23.7275", "date,asc"))
        self.assertEqual([e["id"] for e in d["events"]], ["e1", "e2", "e4", "e6"])  # duplicate, cancelled, test junk dropped
        self.assertIsNone(d["events"][-1]["category"])  # Ticketmaster's "Undefined"
        e1 = d["events"][0]
        self.assertEqual((e1["image"], e1["category"], e1["venue"]["lat"], e1["price"]["min"], e1["performers"]),
                         ("wide", "Music", 37.978, 25.0, ["Band"]))

        u = events.upcoming(d, days=30)
        self.assertEqual([e["id"] for e in u["events"]], ["e1", "e2", "e6"])   # e4 is 60 days away
        self.assertEqual(u["categories"], ["Music", "Sports"])
        self.assertEqual([e["id"] for e in events.upcoming(d, days=90, category="music")["events"]], ["e1", "e4"])

    def test_endpoint_without_key_and_key_never_leaks(self):
        spec = importlib.util.spec_from_file_location("t_events", os.path.join(ROOT, "api", "events.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with mock.patch.dict(os.environ, {"TICKETMASTER_API_KEY": ""}):
            status, body = run(mod.get, "/api/events")
        self.assertEqual(status, 503)
        self.assertIn("TICKETMASTER_API_KEY", body["error"])

        # e2 far outside Athens; e3 just outside the polygon (within the 1.5 km GPS tolerance) → still no zone
        get = self.fake_tm([[tm_event(1, 1), tm_event(2, 2, lat=38.2), tm_event(3, 3, lat=37.995)]])
        gazi = {"neighbourhood": "Γκάζι", "district_id": 3, "lat": 37.978, "lon": 23.712,
                "polygon": parse_wkt_polygon("POLYGON ((23.70 37.97, 23.72 37.97, 23.72 37.99, 23.70 37.99, 23.70 37.97))")}
        with mock.patch.dict(os.environ, {"TICKETMASTER_API_KEY": "secret-key-xyz"}), \
                mock.patch.object(events.load, "__defaults__", (get,)), \
                mock.patch.object(env, "data", return_value=({"neighbourhoods": [gazi]}, None)):
            status, body = run(mod.get, "/api/events")
        self.assertEqual(status, 200)
        self.assertNotIn("secret-key-xyz", json.dumps(body))
        self.assertEqual(body["meta"]["source"], "Ticketmaster Discovery API")
        self.assertEqual([(e["venue"]["neighbourhood"], e["venue"]["district_id"]) for e in body["events"]],
                         [("Γκάζι", 3), (None, None), (None, None)])
        self.assertTrue(ROUTES["/api/events"][1].startswith("public"))  # same for every user → CDN-cacheable

        def down(url):
            raise OSError("401 for https://app.ticketmaster.com/...apikey=secret-key-xyz")
        cache.clear()
        log = io.StringIO()
        with mock.patch.dict(os.environ, {"TICKETMASTER_API_KEY": "secret-key-xyz"}), \
                mock.patch.object(events.load, "__defaults__", (down,)), mock.patch("sys.stderr", log):
            status, body = run(mod.get, "/api/events")
        self.assertEqual(status, 502)
        self.assertNotIn("secret", json.dumps(body))
        self.assertIn("TicketmasterError", log.getvalue())
        self.assertNotIn("secret", log.getvalue())  # not in the server log either


class Http(unittest.TestCase):
    def test_int_param(self):
        self.assertEqual(int_param({"days": "7"}, "days", 30, 1, 90), 7)
        self.assertEqual(int_param({}, "days", 30), 30)
        for bad in ("x", "0", "91"):
            with self.assertRaises(HttpError):
                int_param({"days": bad}, "days", 30, 1, 90)

    def test_meta_clock_and_next_refresh(self):
        from athens.http import with_meta
        with mock.patch("athens.http.time.time", return_value=1_000_000.25):
            m = with_meta({"x": 1}, {"fetched_at": 999_900, "expires_at": 1_000_500, "stale": False})["meta"]
        self.assertEqual(m["server_time_ms"], 1_000_000_250)
        self.assertEqual(m["server_time"], "1970-01-12T13:46:40.250+00:00")
        self.assertEqual(m["next_refresh_s"], 500)  # ceil(1_000_500 − 1_000_000.25)
        with mock.patch("athens.http.time.time", return_value=2_000_000):
            m = with_meta({}, {"fetched_at": 0, "expires_at": 1_000_500, "stale": True})["meta"]
        self.assertEqual(m["next_refresh_s"], 1)  # already expired: never 0 or negative

    def test_cache_meta_has_expiry(self):
        cache.clear()
        with mock.patch("athens.cache.time.time", return_value=1000):
            _, meta = cache.cached("m", 600, lambda: 1)
        self.assertEqual(meta["expires_at"], 1600)

    def test_float_param(self):
        self.assertEqual(float_param({"lat": "37.9"}, "lat", -90, 90), 37.9)
        for bad in ({}, {"lat": "x"}, {"lat": "nan"}, {"lat": "91"}):
            with self.assertRaises(HttpError):
                float_param(bad, "lat", -90, 90)

    def test_run_maps_errors(self):
        self.assertEqual(run(lambda q: {"q": q}, "/api/x?a=1"), (200, {"q": {"a": "1"}}))
        self.assertEqual(run(lambda q: int_param(q, "n"), "/api/x?n=z")[0], 400)

        def down(q):
            raise OSError("secret internal detail")
        with mock.patch("sys.stderr"):
            status, body = run(down, "/api/x")
        self.assertEqual(status, 502)
        self.assertNotIn("secret", body["error"])

    def test_all_routes_register(self):
        for f in os.listdir(os.path.join(ROOT, "api")):
            spec = importlib.util.spec_from_file_location(f"t_{f[:-3]}", os.path.join(ROOT, "api", f))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.assertTrue(hasattr(mod, "handler"), f)
        self.assertEqual(ROUTES["/api/here"][1], "private, no-store")  # personal location: never cached
        self.assertEqual(ROUTES["/api/track"][1], "private, no-store")
        self.assertEqual(sorted(ROUTES), ["/api/air", "/api/config", "/api/events", "/api/health", "/api/heat", "/api/here", "/api/stations", "/api/track", "/api/traffic", "/api/zones"])


if __name__ == "__main__":
    unittest.main()
