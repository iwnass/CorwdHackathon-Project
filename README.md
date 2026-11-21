# Athens Pulse 🌬️

Tourism & events app for Athens: events (with prices and popularity), public transport
(closest stations + Metro / Tram / Suburban timetables) and EV charging, with a landing
page and 10 languages.
React (JavaScript) + Vite + Tailwind CSS + Chart.js. Layout inspired by
[kwd-dashboard](https://github.com/Kamona-WD/kwd-dashboard).

## Run it

```bash
npm install
cp .env.example .env      # optional, works with mock data out of the box
npm run dev               # http://localhost:5173
npm run build             # production build in /dist
```

## Project structure

```
src/
├── config.js                 # env settings (mocks on/off, API URL, donate link)
├── services/
│   ├── api.js                # ⭐ the only file the backend needs to touch
│   ├── http.js               # fetch wrapper
│   └── mockData.js           # fake data = the API contract
├── hooks/useApi.js           # loading / error / data (+ optional polling)
├── hooks/useMapFocus.js      # 📍 buttons → point the page's map at a place
├── context/ThemeContext.jsx  # dark mode + accent color (saved in localStorage)
├── i18n/                     # 10 languages: locales/*.js + translations.js + LanguageContext
├── components/
│   ├── landing/              # GradientWaves, DepthText, StickerBomb (landing page)
│   ├── chat/                 # ChatPanel (sidebar), MobileChat (phones)
│   ├── layout/               # Sidebar (nav + Buy me a coffee), BottomNav (phones), Header, SettingsPanel, Layout, navItems.js
│   ├── charts/               # BarChart (Chart.js), LineChart (ApexCharts, like the template), ChartCard
│   ├── transit/              # LineBadge, SaturdayReminder (24h Saturday metro)
│   ├── ui/                   # Skeleton loaders, Card, Icons, ScrollHint (arrow), LocateButton (📍)
│   ├── reactbits/            # GradientText, DotGrid, CrystalizedBall (reactbits.dev)
│   ├── MapPlaceholder.jsx    # Google Map placeholder + CircleLoader
└── pages/                    # Landing (/), Events, Transit, EvCharging (/ev-charging)
```

## Connecting the backend

1. In `.env` set `VITE_USE_MOCKS=false`.
2. Set `VITE_BACKEND_URL` to the backend (e.g. `http://localhost:8000`). In dev, Vite
   proxies `/api/*` there, so no CORS setup is needed.
3. In production set `VITE_API_BASE_URL` to the full API URL (and enable CORS on the backend),
   or serve the frontend and API from the same domain.

If your routes or JSON differ from below, change **only** `src/services/api.js`
(map your response to the shape below there).

### API contract

All responses are JSON. Every request also gets `?lang=<code>` (en, el, it, de, fr, es, ru, zh, ja, ar) (and
`lang` in the chat body) so names, event titles and agent replies can come back in
the user's language. 

| Method | Path | Response |
|---|---|---|
| GET | `/api/events` | `[{ id, title, date, venue, area, lat, lng, type, pricePerPerson, currency, popularity, interested }]` — `pricePerPerson` = average € per person (0 = free); `popularity` = 0–100; `interested` = people count; `lat/lng` used by the 📍 button |
| GET | `/api/transit/lines` | `[{ id, mode: 'metro'\|'tram'\|'suburban', label, color, route, first, last: { weekday, fri, sat }, freq, satNightFreq, allNightSat, approx }]` — times `HH:MM`, `'24h'` = runs all night. Default: `src/services/transitData.js` |
| GET | `/api/transit/stations` | `[{ id, name, lat, lng, lines: ['M2', 'T6', …] }]` |
| GET | `/api/ev/stations` | `[{ id, name, address, lat, lng, powerKw, connectors: [], total, available, pricePerKwh, status: 'available'\|'busy'\|'offline' }]` (polled every 2 min) |
| GET | `/api/ev/usage` | `[{ hour: 0-23, occupancy: 0-100, typical: 0-100 }]` |
| POST | `/api/agent/chat` | body `{ message, history: [{ role, content }], lang }` → `{ reply }` |

EV stations are polled every 2 minutes.

## Routes

| Path | Page |
|---|---|
| `/` | Landing page (first screen) |
| `/events` | Events |
| `/transit` | Closest stations + timetables |
| `/ev-charging` | EV charging stations |

## Languages

English, Ελληνικά, Italiano, Deutsch, Français, Español, Русский, 繁體中文, 日本語, العربية.
Picked from the globe menu (header, Settings, landing page) and remembered; the first
visit follows the browser language. Arabic switches the whole layout to right-to-left.
Universal terms (EV, kW, Pulse AI, athens pulse, "Buy me a coffee") stay English.
To add a language: copy `src/i18n/locales/en.js`, translate it, add it to `LANGUAGES` in
`src/i18n/translations.js`. The demo data (place names, event titles) only exists in English
and Greek; the real backend should return it in the requested `lang`.

## Transit

- **Closest stations**: the 5 nearest stations with walking time. Uses the phone's location
  after the user taps "Use my location" (or automatically if already allowed), otherwise
  measures from Syntagma Square.
- **Timetables** (Metro / Tram / Suburban): first train, today's last train and a live
  "Running now / Closed now" badge in Athens time (service day starts at 04:00, so
  Friday-night trains after midnight still count as Friday).
- **Saturday 24h reminder**: since 13 Sep 2025 Metro Lines 2 & 3 and Tram T6 & T7 run all
  night every Saturday (Line 1 and Airport trains excluded). A card on the Transit page,
  plus a dismissible banner on every page on Saturdays.
- Suburban railway times are approximate (only the general 04:30–00:00 window is in the
  data); the backend can supply exact Hellenic Train times through `/api/transit/lines`.

## Landing page

Your `Home.jsx` design converted to Tailwind: gradient waves, 3D "Athens Pulse" title with a
faint Parthenon behind it, sticker bomb, section buttons with icons, and the
"404 Brain Not Found" footer in Bungee (bundled with `@fontsource/bungee`, so it works
without Google Fonts).

## Landing page stickers

Drop transparent PNGs into `public/stickers/` (parthenon.png, owl.png, …, see the README
there). Missing files fall back to the drawn SVG stickers.

## Features

- **Skeleton loading** on every chart, list and page while data loads.
- **Map placeholder** (keyless Google Maps embed of Athens) with the requested
  `CircleLoader` from `react-spinners` until it loads; labels for nearby stations / chargers overlaid.
  To use a real map: `npm i @vis.gl/react-google-maps`, set `VITE_GOOGLE_MAPS_API_KEY`
  and replace the `<iframe>` in `MapPlaceholder.jsx` (stations are already passed in).
- **AI chat** in the sidebar's free space (phones: floating button → bottom sheet, same
  conversation). The React Bits Crystalized Ball sits right above the type bar,
  theme-colored, and spins faster while thinking.
- **Line chart** identical to the template's: ApexCharts area, 2 smooth lines, legend on top
  (click to hide/show a line), mouse-wheel / drag zoom with a reset button.
- **Dark mode + theme settings** (6 accent colors). The chosen color re-tints the
  whole page (background, dot grid, cards, sidebar, borders, skeletons, title,
  dial, charts) — all surfaces are mixed from `--primary` in `src/index.css`.

- **React Bits**: Gradient Text title, Dot Grid background, Crystalized Ball (AI chat)
- **Scroll arrow**: animated "more below" arrow that hides once you scroll.
- **Buy me a coffee** button – set `VITE_DONATE_URL`.
- **Settings**: theme-coloured header, light/dark preview tiles, gradient colour swatches,
  one-tap language buttons. Bottom sheet on phones, floating side panel on desktop.
- **Phone page turn**: switching tabs turns the new page in (3D) from the side of the tapped
  tab (`FROM_TAPPED_SIDE` in `Layout.jsx` flips it). Off when "reduce motion" is on.
- **Mobile**: no sidebar; a bottom tab bar for the sections, the AI chat as a floating
  button that opens a compact bottom sheet (same conversation as desktop), and
  "Buy me a coffee" inside Settings.
- **Location buttons (📍)** on every event and EV station: zoom the map there, with an
  "Open in Google Maps" link (handy for directions on phones).
- **EV charging** page (replaces Traffic): free chargers per station, occupancy today vs
  typical, and a station list with power, connectors and €/kWh. A good public data source
  for the backend is Open Charge Map (openchargemap.org).
- **Events** show the average price per person (or "Free").
