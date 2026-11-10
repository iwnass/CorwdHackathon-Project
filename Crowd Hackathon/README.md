# Athens Pulse

Live traffic + air quality for the Municipality of Athens (apps4athens hackathon).
React 19 · Vite · Tailwind CSS v4 · Leaflet.

## Run

```bash
npm install
npm run dev
```

Optional: copy `.env.example` to `.env` and add a free TomTom key for real live-traffic tiles.
Without it, the map shows a clearly-labelled demo traffic estimate.

## Where to edit

| What | File |
| --- | --- |
| Brand colour / fonts / dark surfaces | `src/index.css` (`@theme`) |
| AQI threshold (103), map bounds, districts, avenues | `src/config.js` |
| Reusable UI pieces (Card, Button, Badge, StatCard) | `src/components/ui/` |
| Sidebar links, header | `src/components/layout/` |
| Home page layout | `src/pages/Home.jsx` |
| Alert logic (toast + browser notification) | `src/hooks/useAqiAlerts.js` |
| Air-quality data source | `src/hooks/useAirQuality.js` (Open-Meteo, no key needed) |

Use "Simulate a pollution spike" on the dashboard to demo the alert.
