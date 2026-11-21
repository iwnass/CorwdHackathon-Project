# Athens Monitor — backend

JSON API for air quality, heat and footfall in the Municipality of Athens, built only on the city's open-data
portal ([opendata.cityofathens.gr](https://opendata.cityofathens.gr), CKAN). Python standard library only — no
`pip install`. Runs as Vercel serverless functions or locally with one command.

```bash
python3 scripts/serve.py              # http://localhost:8000/api/... (reads .env.local)
python3 -m unittest discover -s tests # offline tests (fake city API)
vercel --prod                         # deploy (api/*.py → /api/*)
```

## Endpoints

All responses are JSON, UTF-8, `Access-Control-Allow-Origin: *`, and end with
`"meta": {"source", "fetched_at", "stale", "server_time", "server_time_ms", "next_refresh_s"}`.
Times are given twice: `time` (UTC, `Z`) and `time_local` (Athens).

- **`server_time_ms`** — for the live clock, with no extra request: measure the round trip `Δt` of any call and set
  `T_realtime = server_time_ms + Δt / 2`, then tick locally; re-sync on every data refresh.
- **`next_refresh_s`** — seconds until this data can change (`wait = e_k − now`, `e_k` = cache expiry). Schedule the
  next call with it instead of polling; calling earlier returns the same data.

| Endpoint | What you get |
|---|---|
| `GET /api/air` | `city` now (`pollution_pct_avg`, `pollution_level`, `pollution_pct_max`, `worst` 5 station ids, `suspect` ids), every station's `pollution_pct` / `pollution_level` / `main_pollutant`, `hourly` city curve for the last 24 h. Individual pollutants only inside `details` |
| `GET /api/heat` | `city` now (temperature, humidity, `feels_like`, `heat_level`, `hottest`/`coolest`, `peak_hour_24h`, `low_hour_24h`), every station with `min_24h`/`max_24h`, `hourly` city curve (avg/min/max) |
| `GET /api/air?station_id=102` (same on `/api/heat`) | one station, hourly air **and** heat for the last 24 h |
| **`GET /api/here?lat=&lon=[&k=3]`** | **for the live map, one call per position:** `location` (`neighbourhood`, `district_id`, `match`: `inside` / `nearest` within 1.5 km of a border / `outside` Athens), the user's `zone` (air + heat with 24 h curves), `nearest_stations` (air + heat, `distance_m`, faulty sensors skipped), `nearest_wifi` (footfall), `city` context. `Cache-Control: private, no-store` |
| `GET /api/zones` | every **zone = municipal district** (the city's 7 Δημοτικά Διαμερίσματα): name, centre point, neighbourhoods, and an `air` block (`pollution_pct_avg`, `pollution_level`, `pollution_pct_max`, `worst`, `hourly`; pollutants in `details`) and a `heat` block (`temperature_avg/min/max`, `feels_like_avg`, `heat_level`, `hottest`/`coolest`, peak/low hour, `hourly`). Sorted worst air first; `ranking.worst_air` and `ranking.hottest` give both orders |
| `GET /api/zones?district_id=6` | one zone with all its stations, each with both air and heat |
| `GET /api/traffic` | footfall per WiFi station for the latest day, vs. its own previous-7-day average (`busyness`: `quiet` / `usual` / `busy`), `daily` city totals for 14 days |
| `GET /api/traffic?station_id=113&days=30` | one WiFi station, daily series (`days` 1–90, default 30) |
| `GET /api/events[?days=30][&category=Music][&limit=50]` | upcoming concerts and events in Athens from **Ticketmaster**, soonest first: name, date/time, `category` (Music, Sports, Arts & Theatre), `genre`, `status` (`onsale`/`offsale`), venue with coordinates **and its `neighbourhood` + `district_id`**, image, ticket `url`. Same answer for every user (no position in the URL) → served from the CDN cache. `503` until `TICKETMASTER_API_KEY` is set |
| `GET /api/stations` | every environmental and WiFi station with coordinates — for the map |
| `GET /api/health` | liveness + what this instance has cached; never calls the city API |

Errors: `400` bad parameter, `404` unknown station, `502` city API unreachable **and** nothing cached yet.

## Data sources (all from the city's CKAN API)

| Topic | Dataset | Granularity | Requests per refresh |
|---|---|---|---|
| Air + heat | `env-all-stations` (Smart Sense, ~93 stations): AQI, PM1/2.5/10, NO₂, O₃, CO, SO₂, temperature, humidity, pressure | hourly, ~1 h delay | 1 (+ dataset list + neighbourhoods) |
| Footfall | `wifi-{cumulative-traffic,active-visitors,highest-visitors}-all-stations` + `wifi-stations-registry` (81 squares/parks) | **daily** | 4 (+ dataset list) |
| Coordinates | `spatial_coverage` of each per-station dataset; `neighbourhoods-athens` as fallback | — | — |
| Zones | `municipal-districts-athens` (names) + `neighbourhoods-athens` (which neighbourhood is in which district; zone centre = mean of its neighbourhood centres). The city publishes no district boundaries. | — | 1 |

Cached in memory per instance: air/heat 10 min, footfall 30 min. If a refresh fails, the last good data is served with
`"stale": true` instead of an error. The CDN may also keep a response for 5 min (`s-maxage=300`).

## Things a frontend should know

- **Live tracking flow.** Tracking runs on the device; the server is stateless and never stores positions or trails.
  1. On start: `/api/zones` (zone layer), `/api/stations` (markers), `/api/here` (full panel with 24 h curves).
  2. `navigator.geolocation.watchPosition(…, {enableHighAccuracy: true})`. On each fix, call **`/api/track`** only
     if you moved at least the last `recheck_after_m` from where you last called (or `next_refresh_s` has passed).
     `recheck_after_m` is the distance within which the answer provably cannot change (half the gap to the next
     station swap, or the distance to the neighbourhood border); near a border it drops to 1 m, i.e. every fix.
  3. When `location.district_id` changes, show that zone from the `/api/zones` data you already have.
  4. **Events by location, with no extra calls:** fetch `/api/events` once and again after `meta.next_refresh_s`.
     Group them with the location `/api/track` already returns: venue `neighbourhood` == the user's → "In your
     neighbourhood"; venue `district_id` == the user's → "In your zone"; else → "Elsewhere in Athens" (`district_id`
     `null` = venue outside the municipality). Distance to a venue, if wanted, is local math on its `lat`/`lon`.

  Measured on live data, walking with a fix every 5 m: 16–43 % of fixes cause a call, ~1 KB per response,
  ~1.5 ms server time, and the shown answer was never stale between calls.

| Endpoint | When |
|---|---|
| `GET /api/track?lat=&lon=[&k=3]` | **every significant move**: `location` (`match`, `neighbourhood`, `district_id`), `nearest_stations` (compact: air + heat + `distance_m`), `nearest_wifi` (1 spot), `recheck_after_m`. `Cache-Control: private, no-store` |
- **The user's zone comes from the neighbourhood outlines** the city publishes (point-in-polygon), so it is exact
  inside the municipality. Outside it (`match: "outside"`, e.g. Piraeus) `zone` is `null` and the nearest stations
  are still returned with their distance.

- **"Traffic" is people, not cars.** The city publishes no vehicle-traffic data. `visits` = WiFi connections that day,
  `visitors` = distinct people, `peak_visitors` = highest simultaneous count. Updated once a day (yesterday's numbers).
- **Coordinates are neighbourhood centres**, not exact sensor positions — several stations share a point.
- **Air pollution is one percentage per sensor: `pollution_pct` (0–100).** It follows the European Air Quality
  Index, the same scale as the city's own rating: each pollutant (PM2.5, PM10, NO₂, O₃, SO₂) is placed on the
  6 EAQI bands — every band is one sixth of the scale, linear inside it — and the worst pollutant decides
  (`main_pollutant`). `pollution_level` is the band name: Good (0–17 %), Fair, Moderate, Poor, Very poor,
  Extremely poor (84–100 %). On live data the level matches the city's own `aqi` for 89 of 93 sensors.
- **Analytic view = `details`.** Every station, summary and hourly point has a `details` object with the individual
  pollutants (µg/m³), the city's `aqi` 1–6 and an approximate `us_aqi` (EPA breakpoints on hourly PM). The default
  view needs none of it; show it behind the "analytic" checkbox. `/api/track` leaves it out to stay ~1 KB —
  fetch `/api/air?station_id=` when the checkbox is on.
- **`suspect: true`** marks a station with impossible PM values (above the top of the EPA scale — a faulty sensor);
  its `pollution_pct` is `null` (show "sensor fault"), its raw values stay in `details`.
  It is listed but left out of city averages, `worst` and the hourly curve.
- **`fresh: false`** marks a station whose last reading is more than 3 h older than the newest one; it is left out
  of the city's "now" numbers.
- **`feels_like`** is the NWS heat index; below ~27 °C it equals the temperature. `heat_level`: `none`, `caution`,
  `extreme_caution`, `danger`, `extreme_danger`.

## Configuration (optional environment variables)

| Variable | Default | |
|---|---|---|
| `CKAN_BASE` | `https://opendata.cityofathens.gr/api/3/action` | CKAN action API |
| `ATHENS_ENV_TTL_S` | `600` | air/heat cache |
| `ATHENS_WIFI_TTL_S` | `1800` | footfall cache |
| `ATHENS_ENV_ROWS` | `4000` | newest rows read (≈ 24 h × ~100 stations) |
| `ATHENS_HTTP_TIMEOUT_S` | `15` | per request to the city |

| `TICKETMASTER_API_KEY` | — | **needed for `/api/events` only**: free Consumer Key from developer.ticketmaster.com. Set it in Vercel → Settings → Environment Variables (locally: `export` it, see `.env.example`). Server-side only |
| `TICKETMASTER_RADIUS_KM` | `25` | events within this radius of central Athens |
| `TICKETMASTER_TTL_S` | `1800` | events cache |

The Ticketmaster key is the only secret. It never reaches the browser, responses or logs, and the user's position is
never sent to Ticketmaster: the backend fetches all Athens events once per 30 min and computes distances itself.

## Layout

```
api/            one file per endpoint (Vercel maps api/x.py → /api/x)
athens/ckan.py      CKAN client, dataset discovery, coordinates
athens/env.py       air + heat: 24 h window, per-hour folding, city aggregates
athens/traffic.py   WiFi footfall: latest day, 7-day comparison, history
athens/indices.py   European/US AQI, heat index
athens/cache.py     TTL cache with single-flight refresh and stale-on-error
athens/http.py      handler plumbing, parameter validation, error mapping
scripts/serve.py    local server with the same routes
tests/              offline tests
```
