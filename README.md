# Athens Monitor — backend

JSON API for tourism, events, heat, crowds and footfall in the Municipality of Athens, built only on the city's open-data
portal ([opendata.cityofathens.gr](https://opendata.cityofathens.gr), CKAN). Python standard library only — no
`pip install`. Runs as Vercel serverless functions or locally with one command.

```bash
python3 scripts/serve.py              # http://localhost:8000 = test UI (devtools/test-ui.html), /api/... (reads .env.local)
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
| `GET /api/heat` | `city` now (temperature, humidity, `feels_like`, `heat_level`, `hottest`/`coolest`, `peak_hour_24h`, `low_hour_24h`), every station with `min_24h`/`max_24h`, `hourly` city curve (avg/min/max) |
| `GET /api/heat?station_id=102` | one station, hourly heat for the last 24 h |
| **`GET /api/here?lat=&lon=[&k=3]`** | **for the live map, one call per position:** `location` (`neighbourhood`, `district_id`, `match`: `inside` / `nearest` within 1.5 km of a border / `outside` Athens), the user's `zone` (heat with 24 h curves), `nearest_stations` (heat, `distance_m`), `footfall` (WiFi spots within 1 km + one `busyness` index for the area vs usual, see below), `cooling` (nearest fountain, pocket park, pool), `places_nearby` (within 1 km), `accessible_parking` (nearest within 2 km), `events_nearby` (next show of each event within 2 km this week), `metro_nearby` (next trains), `ev_nearby` (chargers with live availability), `city` context. `Cache-Control: private, no-store` |
| `GET /api/zones` | every **zone = municipal district** (the city's 7 Δημοτικά Διαμερίσματα): name, centre point, neighbourhoods, and a `heat` block (`temperature_avg/min/max`, `feels_like_avg`, `heat_level`, `hottest`/`coolest`, peak/low hour, `hourly`). Sorted hottest first (`ranking.hottest`). Each zone also has `footfall`: visits/visitors of its WiFi spots on the latest day, `busyness` vs their 7-day average, `busiest_spot` |
| `GET /api/zones?district_id=6` | one zone with all its stations |
| `GET /api/traffic` | footfall per WiFi station for the latest day, vs. its own previous-7-day average (`busyness`: `quiet` / `usual` / `busy`), plus from its last 8 weeks: `usual_for_weekday` (a normal day like this one), `busiest_weekday`, `trend_7d_vs_28d_pct`; `daily` city totals for 14 days |
| `GET /api/traffic?station_id=113&days=30` | one WiFi station, daily series (`days` 1–90, default 30) |
| `GET /api/events[?days=30 or when=today/weekend/week][&category=Music][&limit=50]` | upcoming concerts and events in Athens from **Ticketmaster**, soonest first: name, date/time, `category` (Music, Sports, Arts & Theatre), `genre`, `status` (`onsale`/`offsale`), venue with coordinates **and its `neighbourhood` + `district_id`**, image, ticket `url`. Same answer for every user (no position in the URL) → served from the CDN cache. `503` until `TICKETMASTER_API_KEY` is set |
| **`POST /api/assistant`** `{"text", "conversation_id"?, "lat"?, "lon"?, "engine"?: "llm"}` | **chat assistant.** City-service questions (appointments, KEP, reports, fines, the 570 municipal services…) go to the City of Athens **AthensGov Sandbox** bot; heat and "where can I cool down" are answered from our data. Reply: `text` (markdown), `speech` (for TTS), `suggestions` (quick replies), `cards` (with `lat`/`lng` for the map), `source` (`athensgov` / `athens-pulse`), `conversation_id` (send it back with the next message), `truncated` (message was cut to the bot's 2000-char limit). `503` until `ATHENSGOV_SANDBOX_KEY` is set, `429` when the shared key's per-minute limit is reached. Note: the sandbox's events/POIs are fictional; only its services registry is real |
| **`GET /api/places[?kind=museum,metro_station]`** | **places for visitors** (city GIS, ~450): museums, galleries, theatres, libraries, cultural centres, cinema (`kind` per venue type), 302 named places/squares, metro/tram/rail stations (`lines`: `M1`…`T5`), free WiFi4EU spots, accessible parking, drinking fountains, pocket parks, pools. Each: `name` (Greek), `name_en` (the city's English name, else a Latin transliteration), `address`, `lat`/`lon`. CDN-cached |
| **`GET /api/i18n?lang=de`** | labels for every code the API returns (place kinds, crowd/heat levels, event categories, `onsale`/`offsale`, `today`/`weekend`/`week`) in **en, el, de, fr, es, ru, zh, ja, ar**; `dir` = `rtl` for Arabic. Load once, translate in the app |
| **`POST /api/presence`** `{"session", "lat", "lon"}` | **live crowds, opt-in:** the app pings every ~2 min while open; the user is counted in their ~220 m cell for 15 min. `session` = a random id the app creates (16–64 chars) |
| **`GET /api/crowds`** | **traffic-style crowd map from the app's own users:** every cell with ≥ 3 users in the last 15 min — `lat`/`lon` (centre), `size_m`, `count` (exact below 10, then 10+, 20+…), `level` (`crowd_low`/`crowd_medium`/`crowd_high`). Cached 60 s |
| **`GET /api/ev[?available=1][&fast=1]`** | **EV chargers** in the Athens area from the national registry (ΜΥΦΑΗ, public files, no key): name, operator, address, `lat`/`lon`, charging `points`, `plugs` (Type 2, CCS, CHAdeMO…), `max_kw`, `fast` (DC), live `available` count and per-status counts (`ev_available` / `ev_in_use` / `ev_out_of_order` / `ev_unknown`), refreshed every 10 min. CDN-cached; nearest ones in `/api/here` → `ev_nearby` |
| **`GET /api/metro[?station=233]`** | **metro (M1–M3) and tram (T6/T7):** all 132 stations with `lines` and `step_free`; with `station`, the next departures per line and direction (`next`, `in_min`), first and last train. **Timetable estimates** (`estimated: true`, `timetable_valid`): STASY publishes no live data, and its latest official timetable is July–August 2026 — rebuild `data/metro.json` with `python3 scripts/build_metro.py` when a new one appears. Nearest stations in `/api/here` → `metro_nearby` |
| `GET /api/stations` | every environmental and WiFi station with coordinates, plus `cooling`: active drinking fountains, pocket parks and public pools (city GIS) — for the map |
| `GET /api/health` | liveness + what this instance has cached; never calls the city API |

Errors: `400` bad parameter, `404` unknown station, `502` city API unreachable **and** nothing cached yet.

## Data sources (all from the city's CKAN API)

| Topic | Dataset | Granularity | Requests per refresh |
|---|---|---|---|
| Heat | `env-all-stations` (Smart Sense, ~93 stations): temperature, humidity, pressure | hourly, ~1 h delay | 1 (+ dataset list + neighbourhoods) |
| Footfall | `wifi-{cumulative-traffic,active-visitors,highest-visitors}-all-stations` + `wifi-stations-registry` (81 squares/parks) | **daily** | 4 (+ dataset list) |
| Coordinates | `spatial_coverage` of each per-station dataset; `neighbourhoods-athens` as fallback | — | — |
| Zones | `municipal-districts-athens` (names) + `neighbourhoods-athens` (which neighbourhood is in which district; zone centre = mean of its neighbourhood centres). The city publishes no district boundaries. | — | 1 |

Cached in memory per instance: heat 10 min, footfall 30 min. If a refresh fails, the last good data is served with
`"stale": true` instead of an error. The CDN may also keep a response for 5 min (`s-maxage=300`).

## Things a frontend should know

- **Live crowds are privacy-first** — ask for consent before the first `/api/presence` ping. Stored: only the ~220 m
  cell, a hash of the session id that changes every day, and a hashed per-IP ping counter; everything expires within
  30 min; no coordinates, raw ids or IPs. A cell appears only with ≥ 3 users. Counts are app users, not all people.
  Needs Upstash Redis on Vercel (shared by all instances); the per-IP limit stops one phone faking a crowd.

- **For visitors, in any of 9 languages:** the API returns stable codes; translate them with `/api/i18n?lang=…`.
  Place names come in Greek (`name`) and English (`name_en`); show `name_en` for every language except Greek.
  Event titles are shown as Ticketmaster publishes them (no machine translation). Arabic: render right-to-left.
- **The city GIS (places, cool-down spots) is slow at times** (5–15 s per layer). Layers load in parallel and are
  cached for 24 h; if a refresh fails the last good copy is served, and `/api/here` still answers without them.

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
| `GET /api/track?lat=&lon=[&k=3]` | **every significant move**: `location` (`match`, `neighbourhood`, `district_id`), `nearest_stations` (compact: heat + `distance_m`), `nearest_wifi` (1 spot), `recheck_after_m`. `Cache-Control: private, no-store` |
- **The user's zone comes from the neighbourhood outlines** the city publishes (point-in-polygon), so it is exact
  inside the municipality. Outside it (`match: "outside"`, e.g. Piraeus) `zone` is `null` and the nearest stations
  are still returned with their distance.

- **"Traffic" is people, not cars.** The city publishes no vehicle-traffic data. `visits` = WiFi connections that day,
  `visitors` = distinct people, `peak_visitors` = highest simultaneous count. Updated once a day (yesterday's numbers);
  there is no hourly data, so "how busy is it right now" is not possible. A day with 0 visits is a WiFi outage
  (~5 % of days) and is treated as missing, not as an empty square.
- **Footfall at a point** (`/api/here` → `footfall`): each spot within 1 km is compared with its own 7-day average,
  and those ratios are averaged with weight 1/d² (closer spots count more; raw counts are not averaged, or one big
  square would swamp the rest). `based_on` says how many spots; with 0 the area has no WiFi spot nearby
  (`nearest_m` says how far the closest is) — show "no data" rather than "quiet".
- **Coordinates are neighbourhood centres**, not exact sensor positions — several stations share a point.
- **`fresh: false`** marks a station whose last reading is more than 3 h older than the newest one; it is left out
  of the city's "now" numbers.
- **`feels_like`** is the NWS heat index; below ~27 °C it equals the temperature. `heat_level`: `none`, `caution`,
  `extreme_caution`, `danger`, `extreme_danger`.

## Configuration (optional environment variables)

| Variable | Default | |
|---|---|---|
| `CKAN_BASE` | `https://opendata.cityofathens.gr/api/3/action` | CKAN action API |
| `ATHENS_ENV_TTL_S` | `600` | heat cache |
| `ATHENS_WIFI_TTL_S` | `1800` | footfall cache |
| `ATHENS_ENV_ROWS` | `4000` | newest rows read (≈ 24 h × ~100 stations) |
| `ATHENS_HTTP_TIMEOUT_S` | `15` | per request to the city |

| `TICKETMASTER_API_KEY` | — | **needed for `/api/events` only**: free Consumer Key from developer.ticketmaster.com. Set it in Vercel → Settings → Environment Variables (locally: `export` it, see `.env.example`). Server-side only |
| `ATHENSGOV_SANDBOX_KEY` | — | **needed for `/api/assistant` (city services) only**: the sandbox API key. Server-side only |
| `ATHENSGOV_REQUESTS_PER_MIN` | `100` | the key's limit, shared by all users; the backend answers `429` instead of exceeding it (per instance) |
| `TICKETMASTER_RADIUS_KM` | `25` | events within this radius of central Athens |
| `TICKETMASTER_TTL_S` | `1800` | events cache |

The Ticketmaster key is the only secret. It never reaches the browser, responses or logs, and the user's position is
never sent to Ticketmaster: the backend fetches all Athens events once per 30 min and computes distances itself.

## Layout

```
api/            one file per endpoint (Vercel maps api/x.py → /api/x)
athens/ckan.py      CKAN client, dataset discovery, coordinates
athens/env.py       heat: 24 h window, per-hour folding, zones, location, tracking
athens/traffic.py   WiFi footfall: latest day, 7-day comparison, history
athens/indices.py   heat index (feels like)
athens/cache.py     TTL cache with single-flight refresh and stale-on-error
athens/http.py      handler plumbing, parameter validation, error mapping
scripts/serve.py    local server with the same routes
tests/              offline tests
```
