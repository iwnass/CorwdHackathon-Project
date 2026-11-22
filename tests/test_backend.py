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
from athens.indices import heat_index, heat_level  # noqa: E402


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

    def test_string_numbers_and_bad_clock(self):
        rows = [env_row("1", "2026-11-21T09:00:00", temperature="21.5", humidity="40"),
                env_row(2, "2026-11-21T09:00:00", temperature="n/a"),
                env_row(7, "2099-01-01T00:00:00")]  # wrong clock: ignored, does not move the window
        d = self.build(rows)
        self.assertEqual(sorted(r["station_id"] for r in d["rows"]), [1, 2])
        h = env.heat(d)
        self.assertEqual((h["stations"][0]["temperature"], h["stations"][0]["humidity"], h["stations"][0]["lat"]), (21.5, 40.0, 38.0))
        self.assertIsNone(h["stations"][1]["temperature"])

    def test_zones_are_municipal_districts(self):
        rows = [env_row(1, "2026-11-21T09:00:00", temperature=20.0, municipal_district_id=6),
                env_row(2, "2026-11-21T09:00:00", temperature=22.0, municipal_district_id=6),
                env_row(3, "2026-11-21T09:00:00", temperature=18.0, municipal_district_id="4"),
                env_row(4, "2026-11-21T09:00:00", temperature=19.0, municipal_district_id=4),
                env_row(9, "2026-11-21T09:00:00", hood="ΚΟΥΚΑΚΙ", temperature=17.0, municipal_district_id=None)]
        d = self.build(rows)
        z = env.zones(d)
        self.assertEqual(len(z["zones"]), 7)                                    # every district is a zone
        self.assertEqual(z["ranking"]["hottest"][:2], [6, 4])
        z6, z4 = z["zones"][0], z["zones"][1]                                   # hottest first
        self.assertEqual((z4["name"], z4["stations_count"]), ("4ο Δημοτικό Διαμέρισμα Αθήνας", 3))
        self.assertEqual((z4["heat"]["stations"], z4["heat"]["temperature_avg"]), (3, 18.0))  # station 9 via its neighbourhood
        self.assertEqual((z6["heat"]["temperature_avg"], z6["heat"]["hottest"]), (21.0, [2, 1]))
        self.assertNotIn("air", z6)
        self.assertEqual(len(z6["heat"]["hourly"]), 1)
        self.assertEqual((z6["lat"], z6["neighbourhoods"]), (38.005, ["ΑΓΙΟΣ ΝΙΚΟΛΑΟΣ", "Κυψέλη"]))
        self.assertEqual((z["zones"][-1]["stations_count"], z["zones"][-1]["heat"]), (0, None))
        one = env.zone(d, 6)["zone"]
        self.assertEqual([(s["station_id"], s["temperature"]) for s in sorted(one["stations"], key=lambda s: s["station_id"])],
                         [(1, 20.0), (2, 22.0)])
        self.assertIsNone(env.zone(d, 99))

    def test_here(self):
        d = self.build([env_row(1, "2026-11-21T09:00:00", municipal_district_id=6),
                        env_row(2, "2026-11-21T09:00:00", municipal_district_id=6),
                        env_row(3, "2026-11-21T09:00:00", municipal_district_id=4, hood="ΚΟΥΚΑΚΙ")])
        inside = env.locate(d, 38.001, 23.741)
        self.assertEqual((inside["match"], inside["neighbourhood"], inside["district_id"]), ("inside", "Κυψέλη", 6))
        edge = env.locate(d, 38.0060, 23.7400)  # just outside the polygon, 500 m from its centre
        self.assertEqual((edge["match"], edge["district_id"]), ("nearest", 6))
        self.assertEqual(env.locate(d, 40.64, 22.94)["match"], "outside")  # Thessaloniki

        h = env.here(d, 38.001, 23.741, 2)
        self.assertEqual(h["zone"]["district_id"], 6)
        self.assertEqual((h["zone"]["heat"]["stations"], list(h["city"])), (2, ["heat"]))
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

    def test_outage_days_are_not_quiet_days(self):
        rows = [{"station_id": 1, "date": "2026-11-21", "cumulative_traffic": 0}]
        self.assertEqual(traffic._merge({"visits": rows}), {})  # a 0 is dropped, not stored as "0 visits"

    def test_patterns(self):
        from datetime import date as D, timedelta as T
        last = D(2026, 11, 20)  # a Friday
        days = {}
        for i in range(56):
            x = last - T(days=i)
            days[x.isoformat()] = {"visits": 3000 if x.weekday() == 5 else (500 if i < 7 else 1000)}  # Saturdays busiest
        p = traffic._patterns(days, last.isoformat())
        self.assertEqual(p["busiest_weekday"], "Sat")
        self.assertEqual(p["usual_for_weekday"], 1000)            # previous Fridays
        self.assertLess(p["trend_7d_vs_28d_pct"], 0)              # the last week was quieter

    def test_at_point_and_by_district(self):
        d = traffic.load(self.get)
        d["stations"][2].update(lat=37.99, lon=23.73)              # both spots at the same place now
        near = traffic.at_point(d, 37.991, 23.731)                 # ~140 m away
        self.assertEqual([s["station_id"] for s in near["spots"]], [1, 2])
        # station 1 at 2× its usual, station 2 at 1×, same distance → 1.5× → busy (+50 %)
        self.assertEqual((near["busyness"], near["change_vs_usual_pct"], near["based_on"]), ("busy", 50.0, 2))
        far = traffic.at_point(d, 38.10, 23.90)
        self.assertEqual((far["spots"], far["busyness"]), ([], None))
        self.assertGreater(far["nearest_m"], 1000)
        z = traffic.by_district(d)
        self.assertEqual((z[1]["spots"], z[1]["visits"], z[1]["busyness"], z[1]["busiest_spot"]), (1, 2000, "busy", 1))

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
        spec = importlib.util.spec_from_file_location("t_events", os.path.join(ROOT, "endpoints", "events.py"))
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


class Cooling(unittest.TestCase):
    def test_load_and_nearest(self):
        from athens import cooling
        layers = {
            "geonode:pidakes": [{"geometry": {"type": "MultiPoint", "coordinates": [[23.7408, 37.9770]]},
                                 "properties": {"name": "Πλ.Κολωνακίου", "address": "Κολωνάκι", "status": "ΕΝΕΡΓΟ"}},
                                {"geometry": {"type": "MultiPoint", "coordinates": [[23.7350, 37.9755]]},
                                 "properties": {"name": "closed", "status": "ΑΝΕΝΕΡΓΟ"}},
                                {"geometry": None, "properties": {"name": "no location"}}],
            "geonode:PocketParks2": [{"geometry": {"type": "Point", "coordinates": [23.7353, 37.9603]},
                                      "properties": {"descr": "ΠΑΡΚΟ ΤΣΕΠΗΣ", "streetname": "ΑΕΤΙΩΝΟΣ"}}],
            "geonode:kolimbitiria": []}

        def get(url):
            self.assertIn("srsName=EPSG:4326", url)
            return json.dumps({"features": layers[parse_qs(urlparse(url).query)["typename"][0]]}).encode()
        spots = cooling.load(get)
        self.assertEqual([(s["kind"], s["name"]) for s in spots], [("fountain", "Πλ.Κολωνακίου"), ("pocket_park", "ΠΑΡΚΟ ΤΣΕΠΗΣ")])
        near = cooling.nearest(spots, 37.9755, 23.7348)  # Syntagma: the closed fountain right there is skipped
        self.assertEqual(sorted(near), ["fountain", "pocket_park"])
        self.assertAlmostEqual(near["fountain"]["distance_m"], 550, delta=50)


class Assistant(unittest.TestCase):
    KEY = {"ATHENSGOV_SANDBOX_KEY": "sbx-secret-1"}

    def setUp(self):
        from athens import assistant
        self.a = assistant
        assistant._bucket.update(tokens=float(assistant.RATE_PER_MIN))

    def fake_city(self, expired=()):
        calls = []

        def request(method, url, headers, body=None):
            calls.append((method, url, headers, json.loads(body) if body else None))
            self.assertEqual(headers["X-API-Key"], "sbx-secret-1")
            if url.endswith("/v1/conversations"):
                return {"id": f"c{len(calls)}"}
            conv = url.split("/v1/conversations/")[1].split("/")[0]
            if conv in expired:
                import urllib.error
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            return {"text": "Βρήκα 3 ΚΕΠ", "speech": "Βρήκα 3 ΚΕΠ", "intent": {"name": "find_kep", "confidence": 1.0},
                    "cards": [], "suggestions": [], "state": {"flow": None}}
        request.calls = calls
        return request

    def test_topics(self):
        t = self.a.topic
        self.assertEqual([t("ΖΈΣΤΗ σήμερα!"), t("kanei zesti?"), t("what's the temperature?")], ["heat", "heat", "heat"])
        self.assertIsNone(t("Πώς είναι ο αέρας;"))  # air quality is not answered here → city bot
        self.assertEqual(t("κάνει ζέστη, πού να δροσιστώ;"), "cooling")  # cooling wins
        self.assertIsNone(t("Θέλω ραντεβού για πιστοποιητικό γέννησης"))  # → city bot

    def test_forward_cap_and_reuse(self):
        req = self.fake_city()
        with mock.patch.dict(os.environ, self.KEY):
            r = self.a.ask("  pou einai   to kontinotero KEP? " + "x" * 3000, lat=37.97551234, lon=23.73481234,
                           engine="llm", request=req)
            self.assertEqual((r["source"], r["conversation_id"], r["truncated"]), ("athensgov", "c1", True))
            _, url, _, body = req.calls[1]
            self.assertTrue(url.endswith("/v1/conversations/c1/messages"))
            self.assertEqual(len(body["text"]), 2000)                 # never more than the city bot accepts
            self.assertTrue(body["text"].startswith("pou einai to kontinotero KEP?"))  # whitespace collapsed
            self.assertEqual((body["location"], body["engine"]), ({"lat": 37.976, "lng": 23.735}, "llm"))
            r2 = self.a.ask("και αύριο;", conversation_id="c1", request=req)  # same conversation, no new one
            self.assertEqual((r2["conversation_id"], len(req.calls)), ("c1", 3))

    def test_expired_conversation_restarts(self):
        req = self.fake_city(expired=("old",))
        with mock.patch.dict(os.environ, self.KEY):
            r = self.a.ask("ΚΕΠ", conversation_id="old", request=req)
        self.assertEqual(r["conversation_id"], "c2")

    def test_rate_limit(self):
        req = self.fake_city()
        self.a._bucket.update(tokens=2.0, at=__import__("time").monotonic())
        with mock.patch.dict(os.environ, self.KEY):
            self.a.ask("ΚΕΠ", request=req)                             # 2 calls: new conversation + message
            with self.assertRaises(self.a.AthensGovError) as e:
                self.a.ask("ΚΕΠ", conversation_id="c1", request=req)
        self.assertEqual(e.exception.status, 429)
        self.assertIn("retry in", str(e.exception))

    def test_local_answers(self):
        r = self.a.ask("κάνει ζέστη;")                               # no location, no key needed
        self.assertEqual((r["source"], r["state"]["awaiting"]), ("athens-pulse", "location"))
        here = {"zone": {}, "nearest_stations": [{"name": "Πλ. Συντάγματος", "distance_m": 6, "temperature": 22.1,
                                                  "feels_like": 22.1, "heat_level": "none", "lat": 37.975, "lon": 23.735,
                                                  "station_id": 161}]}
        with mock.patch.object(env, "data", return_value=({}, None)), mock.patch.object(env, "here", return_value=here):
            el = self.a.ask("κάνει ζέστη;", lat=37.975, lon=23.735)
            en = self.a.ask("is it hot?", lat=37.975, lon=23.735)
        self.assertIn("22.1 °C", el["text"]); self.assertIn("κανονική", el["text"])
        self.assertEqual(en["intent"]["name"], "heat"); self.assertIn("feels like", en["text"])
        self.assertNotIn("**", el["speech"])                          # speech is plain text for TTS

    def test_endpoint_validation_and_key_safety(self):
        spec = importlib.util.spec_from_file_location("t_assistant", os.path.join(ROOT, "endpoints", "assistant.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        call = lambda body: run(lambda q: mod.get(q, body, "1.1.1.1"), "/api/assistant")  # noqa: E731
        self.assertEqual(call({})[0], 400)
        self.assertEqual(call({"text": "ΚΕΠ", "conversation_id": "../../admin"})[0], 400)
        self.assertEqual(call({"text": "ΚΕΠ", "lat": 999, "lon": 1})[0], 400)
        with mock.patch.dict(os.environ, {"ATHENSGOV_SANDBOX_KEY": ""}):
            status, body = call({"text": "ΚΕΠ"})
        self.assertEqual(status, 503)
        self.assertIn("ATHENSGOV_SANDBOX_KEY", body["error"])

        def down(method, url, headers, body=None):
            raise OSError(f"failed {url} {headers}")  # would leak the key if it reached the log
        log = io.StringIO()
        with mock.patch.dict(os.environ, self.KEY), mock.patch.object(self.a, "http", down), mock.patch("sys.stderr", log):
            status, body = call({"text": "ΚΕΠ"})
        self.assertEqual(status, 502)
        self.assertNotIn("sbx-secret-1", log.getvalue() + json.dumps(body))
        self.assertEqual(ROUTES["/api/assistant"][1:], ("private, no-store", "POST"))


class Tourism(unittest.TestCase):
    def test_i18n_all_languages(self):
        from athens import i18n
        self.assertEqual(len(i18n.LANGS), 9)
        for code, row in i18n.LABELS.items():
            self.assertTrue(all(row[l].strip() for l in i18n.LANGS), code)
        de, ar, xx = i18n.labels("de"), i18n.labels("ar"), i18n.labels("klingon")
        self.assertEqual((de["labels"]["museum"], de["dir"]), ("Museum", "ltr"))
        self.assertEqual((ar["labels"]["metro_station"], ar["dir"]), ("محطة مترو", "rtl"))
        self.assertEqual(xx["lang"], "en")  # unknown language → English

    def test_transliterate(self):
        from athens.places import transliterate
        self.assertEqual(transliterate("Μουσείο Λαϊκής Τέχνης"), "Mouseio Laikis Technis")
        self.assertEqual(transliterate("Ντόρα Στράτου"), "Dora Stratou")
        self.assertIsNone(transliterate(""))
        self.assertEqual(transliterate("Πλ.Συντάγματος(κεντρικό)"), "Pl.Syntagmatos(Kentriko)")

    def test_places_load(self):
        from athens import places
        pt = lambda lon, lat, multi=False: {"type": "MultiPoint" if multi else "Point",  # noqa: E731
                                            "coordinates": [[lon, lat]] if multi else [lon, lat]}
        layers = {
            "geonode:politismos24_f": [{"geometry": pt(23.72, 37.97, True), "properties": {"type": "ΜΟΥΣΕΙΟ",
                                        "name": "Μουσείο, Λαϊκής Τέχνης - και Παράδοσης", "tax_diefth": "Αγγ. Χατζημιχάλη 6",
                                        "link_": "http://x"}}],
            "geonode:toponymia": [{"geometry": pt(23.71, 37.99), "properties": {"names_labe": "ΠΛΑΤΕΙΑ ΑΓ.ΤΡΥΦΩΝΟΣ",
                                   "names_eng": "AGIOU TRYFONOS SQ.", "synoikia": "ΑΚΑΔΗΜΙΑ ΠΛΑΤΩΝΟΣ"}}],
            "geonode:stasy2024": [{"geometry": pt(23.73, 37.98, True), "properties": {"name": "ΟΜΟΝΟΙΑ", "name_en": "Omonia",
                                   "lines": "Γραμμή 1&2-ΜΕΤΡΟ", "eidos": "ΜΕΤΡΟ"}},
                                  {"geometry": pt(23.73, 37.97, True), "properties": {"name": "ΣΥΝΤΑΓΜΑ", "name_en": "Syntagma",
                                   "lines": "Γραμμή 5-ΤΡΑΜ", "eidos": "ΤΡΑΜ"}}],
            "geonode:wifi4eu": [{"geometry": pt(23.735, 37.9755), "properties": {"descr": "Πλατεία Συντάγματος"}}],
            "geonode:parking_amea": [{"geometry": None, "properties": {"street": "ΜΟΥΡΟΥΖΗ", "number": "1"}}]}  # no point → skipped
        with mock.patch("athens.cooling.layer", lambda name, get: layers[name]):
            ps = places.load(None)
        by = {p["kind"]: p for p in ps}
        self.assertEqual(sorted(by), ["free_wifi", "metro_station", "museum", "place", "tram_stop"])
        self.assertEqual(by["museum"]["name"], "Μουσείο, Λαϊκής Τέχνης και Παράδοσης")  # the city's " - " line breaks removed
        self.assertTrue(by["museum"]["name_en"].startswith("Mouseio"))                # no English name → transliterated
        self.assertEqual((by["place"]["name_en"], by["metro_station"]["lines"], by["tram_stop"]["lines"]),
                         ("Agiou Tryfonos Sq.", ["M1", "M2"], ["T5"]))
        near = places.near(ps, 37.9755, 23.735, 500)
        self.assertEqual(near[0]["kind"], "free_wifi")
        self.assertEqual(near[0]["distance_m"], 0)

    def test_when_range(self):
        from datetime import date as D
        fri, sat, sun = D(2026, 11, 20), D(2026, 11, 21), D(2026, 11, 22)
        self.assertEqual(events.when_range("today", fri), (fri, fri))
        self.assertEqual(events.when_range("weekend", fri), (sat, sun))
        self.assertEqual(events.when_range("weekend", sat), (sat, sun))
        self.assertEqual(events.when_range("weekend", sun), (sun, sun))
        self.assertEqual(events.when_range("week", fri), (fri, D(2026, 11, 26)))

    def test_events_nearby_one_entry_per_show(self):
        d = {"events": [events._normalize(tm_event(1, 1)), events._normalize(tm_event(2, 2, name="Event 1")),  # same show
                        events._normalize(tm_event(3, 3, lat=38.2))]}                                         # 25 km away
        near = events.nearby(d, 37.978, 23.712)
        self.assertEqual([(e["id"], e["distance_m"]) for e in near], [("e1", 0)])


class Presence(unittest.TestCase):
    def setUp(self):
        from athens import presence
        self.p, self.store = presence, presence.MemoryStore()
        self.calls = []

        def request(url, headers, body):  # an Upstash pipeline backed by the in-memory store
            self.calls.append((url, headers, json.loads(body)))
            return [{"result": self.store.run(c)} for c in json.loads(body)]
        self.req = request
        self.env = mock.patch.dict(os.environ, {"KV_REST_API_URL": "https://kv.example", "KV_REST_API_TOKEN": "tok",
                                                "PRESENCE_STORE": ""})
        self.env.start()
        self.addCleanup(self.env.stop)

    def ping(self, session, lat, lon, ip="1.2.3.4", now=None):
        return self.p.ping(session, lat, lon, ip, now=now, request=self.req)

    def test_counts_threshold_and_privacy(self):
        now = 1_800_000_000
        for i in range(2):
            self.ping(f"session-{i:010d}", 37.97551, 23.73481, now=now)
        self.assertEqual(self.p.crowds(now=now, request=self.req)["cells"], [])  # 2 people: never shown
        self.ping("session-0000000002", 37.97559, 23.73489, now=now)             # same ~220 m cell
        cells = self.p.crowds(now=now, request=self.req)["cells"]
        self.assertEqual([(c["count"], c["level"]) for c in cells], [(3, "crowd_low")])
        stored = json.dumps(self.store.kv) + json.dumps(self.store.z)
        for leak in ("session-0000000002", "37.975", "1.2.3.4"):                 # no raw id, position or IP stored
            self.assertNotIn(leak, stored)
        self.assertEqual(self.calls[0][0], "https://kv.example/pipeline")
        self.assertEqual(self.calls[0][1]["Authorization"], "Bearer tok")

    def test_moving_counts_once_and_expiry(self):
        now = 1_800_000_000
        for i in range(3):
            self.ping(f"walker-{i:010d}", 37.9755, 23.7348, now=now)
        self.ping("walker-0000000000", 37.9900, 23.7400, now=now + 60)           # walked to another cell
        self.assertEqual(self.p.crowds(now=now + 60, request=self.req)["cells"], [])  # 2 left in the first cell
        self.assertEqual(self.p.crowds(now=now + 16 * 60, request=self.req)["cells"], [])  # all expired

    def test_big_crowds_are_rounded_and_abuse_is_limited(self):
        now = 1_800_000_000
        for i in range(23):
            self.ping(f"crowd-{i:011d}", 37.9755, 23.7348, ip=f"10.0.0.{i}", now=now)
        cell = self.p.crowds(now=now, request=self.req)["cells"][0]
        self.assertEqual((cell["count"], cell["level"]), (20, "crowd_medium"))   # 23 → "20+"
        with mock.patch.object(self.p, "PINGS_PER_IP", 2):
            self.ping("spam-00000000000001", 37.9755, 23.7348, ip="6.6.6.6", now=now)
            self.ping("spam-00000000000002", 37.9755, 23.7348, ip="6.6.6.6", now=now)
            with self.assertRaises(self.p.RateLimited):
                self.ping("spam-00000000000003", 37.9755, 23.7348, ip="6.6.6.6", now=now)

    def test_endpoint(self):
        spec = importlib.util.spec_from_file_location("t_presence", os.path.join(ROOT, "endpoints", "presence.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        bad = run(lambda q: mod.get(q, {"session": "x", "lat": 37.9, "lon": 23.7}, "1.1.1.1"), "/api/presence")
        self.assertEqual(bad[0], 400)
        with mock.patch.dict(os.environ, {"KV_REST_API_URL": "", "PRESENCE_STORE": ""}):
            off = run(lambda q: mod.get(q, {"session": "s" * 20, "lat": 37.9, "lon": 23.7}, "1.1.1.1"), "/api/presence")
        self.assertEqual(off[0], 503)
        self.assertEqual(ROUTES["/api/presence"][1:], ("private, no-store", "POST"))


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
        for f in os.listdir(os.path.join(ROOT, "endpoints")):
            spec = importlib.util.spec_from_file_location(f"t_{f[:-3]}", os.path.join(ROOT, "endpoints", f))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.assertTrue(hasattr(mod, "handler"), f)
        self.assertEqual(ROUTES["/api/here"][1], "private, no-store")  # personal location: never cached
        self.assertEqual(ROUTES["/api/track"][1], "private, no-store")
        self.assertEqual(sorted(ROUTES), ["/api/assistant", "/api/config", "/api/crowds", "/api/culture", "/api/ev", "/api/events", "/api/health", "/api/heat", "/api/here", "/api/i18n", "/api/metro", "/api/parking", "/api/places", "/api/presence", "/api/stations", "/api/track", "/api/traffic", "/api/zones"])


class Culture(unittest.TestCase):
    PAGE = """<title>Treat Yourself &#8211; A Sunday Market￼ - Culture is Athens - Πολιτισμός είναι η Αθήνα</title>
    <li class="gt-start-date"><div class="gt-icon"><svg></svg></div><div class="gt-content"><div class="gt-title">Ημερομηνία</div><div class="gt-inner">22 Νοεμβρίου 2026 10:00</div></div></li>
    <li class="gt-status"><div class="gt-content"><div class="gt-title">Κατάσταση</div><div class="gt-inner">Τρέχουσα</div></div></li>
    <li class="gt-venue"><div class="gt-content"><div class="gt-title">Χώρος</div><div class="gt-inner"><ul><li><a href="/venue/x/">Δημοτική Αγορά Κυψέλης</a></li></ul></div></div></li>
    <div class="gt-price">Free</div><ul data-zoom="16" data-lat="38.0008" data-lng="23.7379" data-type="true"></ul>"""

    def test_parse_date(self):
        from athens import culture
        self.assertEqual(culture.parse_date("22 Νοεμβρίου 2026 10:00"), ("2026-11-22", "10:00"))
        self.assertEqual(culture.parse_date("3 Μαΐου 2027"), ("2027-05-03", None))
        self.assertEqual(culture.parse_date("31 Φεβρουαρίου 2026"), (None, None))
        self.assertEqual(culture.parse_date("soon"), (None, None))

    def test_parse_event_and_selection(self):
        from athens import culture
        e = culture.parse_event(self.PAGE, "https://cultureisathens.gr/event/x/")
        self.assertEqual((e["title"], e["date"], e["time"], e["status"], e["venue"], e["free"], e["lat"], e["lon"]),
                         ("Treat Yourself – A Sunday Market", "2026-11-22", "10:00", "current", "Δημοτική Αγορά Κυψέλης",
                          True, 38.0008, 23.7379))
        self.assertIsNone(culture.parse_event("<title>No date</title>", "u"))
        old = {**e, "date": "2026-10-01", "status": "current", "url": "old"}
        past = {**e, "date": "2026-10-02", "status": "past", "url": "past"}
        later = {**e, "date": "2026-12-01", "status": "upcoming", "url": "later"}
        d = {"events": [old, past, e, later]}
        self.assertEqual([x["url"] for x in culture.on(d, "2026-11-22")], [e["url"], "old"])
        self.assertEqual([x["url"] for x in culture.upcoming(d, "2026-11-22")], ["old", e["url"], "later"])
        self.assertEqual(culture.nearby([e, {**e, "lat": None}], 38.0008, 23.7379)[0]["distance_m"], 0)


class EvHistory(unittest.TestCase):
    def test_one_sample_per_slot_and_24h_window(self):
        from athens import ev, presence
        store = presence.MemoryStore()
        redis = lambda *cs: [store.run([str(x) for x in c]) for c in cs]  # noqa: E731
        c = lambda free, pts, lat=37.9838, down=0: {"lat": lat, "lon": 23.7275, "points": pts, "available": free,  # noqa: E731
                                                    "status": {"ev_out_of_order": down}}
        items = [c(1, 4), c(0, 2, down=2), c(0, 4, lat=38.2)]  # all-down station and one 24 km away are left out
        self.assertEqual(ev.occupancy(items), 75)
        t0 = 1_800_000_000 - 1_800_000_000 % 600
        self.assertTrue(ev.record_occupancy(items, t0, redis))
        self.assertFalse(ev.record_occupancy(items, t0 + 60, redis))  # same 10-minute slot
        self.assertTrue(ev.record_occupancy([c(4, 4)], t0 + 600, redis))
        self.assertEqual(ev.occupancy_history(t0 + 601, redis), [{"time": t0, "occupancy": 75}, {"time": t0 + 600, "occupancy": 0}])
        self.assertEqual(ev.occupancy_history(t0 + 25 * 3600, redis), [])


class Parking(unittest.TestCase):
    def test_keeps_garages_and_named_lots_and_falls_back_to_snapshot(self):
        from athens import parking
        osm = {"elements": [
            {"type": "way", "id": 1, "center": {"lat": 37.98, "lon": 23.73},
             "tags": {"parking": "underground", "capacity": "642", "fee": "yes", "capacity:charging": "2"}},
            {"type": "node", "id": 2, "lat": 37.97, "lon": 23.72, "tags": {"parking": "surface"}},  # unnamed lot: dropped
            {"type": "node", "id": 3, "lat": 37.96, "lon": 23.71, "tags": {"name": "Lot", "wheelchair": "yes"}}]}
        got = parking.normalize(osm)
        self.assertEqual([(p["id"], p["type"], p["capacity"], p["ev_points"], p["fee"]) for p in got],
                         [("way/1", "underground", 642, 2, True), ("node/3", "surface", None, None, None)])
        self.assertTrue(got[1]["wheelchair"])

        def down():
            raise OSError("overpass down")
        self.assertGreater(len(parking.load(down)), 50)  # data/parking.json


if __name__ == "__main__":
    unittest.main()
