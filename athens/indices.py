"""Air-quality and heat indices.

- `aqi` in the city data is the European AQI band 1–6.
- US AQI is computed from hourly PM2.5/PM10 with the EPA breakpoints (PM2.5 as revised in 2024).
  EPA defines it on 24 h / NowCast averages, so from one hourly value it is an approximation.
- Heat index ("feels like") is the NWS formula (Rothfusz regression + adjustments).
"""
import math

EAQI = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very poor", 6: "Extremely poor"}

PM25 = [(0.0, 9.0, 0, 50), (9.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
        (55.5, 125.4, 151, 200), (125.5, 225.4, 201, 300), (225.5, 325.4, 301, 500)]
PM10 = [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
        (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500)]
US_CATEGORIES = [(50, "Good"), (100, "Moderate"), (150, "Unhealthy for sensitive groups"),
                 (200, "Unhealthy"), (300, "Very unhealthy"), (math.inf, "Hazardous")]


# ---------- General pollution percentage ----------
# European AQI bands (EEA, the version the city's own `aqi` follows: it reproduces it for 90 % of live readings).
# Upper limits of bands 1–5 in µg/m³; band 6 runs up to twice the band-5 limit, where the scale reads 100 %.
EAQI_BANDS = {"pm2_5": (10, 20, 25, 50, 75), "pm10": (20, 40, 50, 100, 150), "no2": (40, 90, 120, 230, 340),
              "o3": (50, 100, 130, 240, 380), "so2": (100, 200, 350, 500, 750)}


def _pct(v, limits):
    """Place a concentration on 0–100: each of the 6 bands is one sixth, linear inside the band. → (pct, band 1–6)"""
    edges = (0, *limits, limits[-1] * 2)
    for b in range(6):
        lo, hi = edges[b], edges[b + 1]
        if v <= hi:  # a band includes its upper limit, as in the EAQI tables
            return (b + (v - lo) / (hi - lo)) * 100 / 6, b + 1
    return 100.0, 6


def pollution(r):
    """→ (pollution_pct 0–100, level label, main pollutant) from a row's concentrations; the worst pollutant decides,
    as in the EAQI. (None, None, None) if the row has none of them."""
    scores = {p: _pct(r[p], lim) for p, lim in EAQI_BANDS.items() if isinstance(r.get(p), (int, float)) and r[p] >= 0}
    if not scores:
        return None, None, None
    main = max(scores, key=lambda p: scores[p][0])
    pct, band = scores[main]
    return round(min(100.0, pct)), EAQI[band], main


def pollution_level(pct):
    """Level for an averaged percentage (sixths of the scale)."""
    return None if pct is None else EAQI[min(6, max(1, math.ceil(round(pct * 6 / 100, 6))))]


def eaqi_label(v):
    return EAQI.get(int(v)) if isinstance(v, (int, float)) and float(v).is_integer() else None


def _sub_index(c, table, decimals):
    if c is None or c < 0:
        return None
    c = math.floor(c * 10 ** decimals) / 10 ** decimals  # EPA truncates, it does not round
    for lo, hi, ilo, ihi in table:
        if c <= hi:
            return round((ihi - ilo) / (hi - lo) * (c - lo) + ilo)
    return 500


def us_aqi(pm2_5, pm10):
    subs = [i for i in (_sub_index(pm2_5, PM25, 1), _sub_index(pm10, PM10, 0)) if i is not None]
    return max(subs) if subs else None


def us_aqi_category(v):
    return None if v is None else next(label for top, label in US_CATEGORIES if v <= top)


def heat_index(t_c, rh):
    """°C, °C/% → apparent temperature °C (NWS)."""
    if t_c is None or rh is None:
        return None
    t = t_c * 9 / 5 + 32
    hi = 0.5 * (t + 61 + (t - 68) * 1.2 + rh * 0.094)
    if (hi + t) / 2 >= 80:
        hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh - 0.22475541 * t * rh - 6.83783e-3 * t * t
              - 5.481717e-2 * rh * rh + 1.22874e-3 * t * t * rh + 8.5282e-4 * t * rh * rh - 1.99e-6 * t * t * rh * rh)
        if rh < 13 and 80 <= t <= 112:
            hi -= (13 - rh) / 4 * math.sqrt((17 - abs(t - 95)) / 17)
        elif rh > 85 and 80 <= t <= 87:
            hi += (rh - 85) / 10 * (87 - t) / 5
    else:
        hi = (hi + t) / 2 if t >= 80 else t  # below 80 °F the "feels like" is just the temperature
    return round((hi - 32) * 5 / 9, 1)


def heat_level(feels_c):
    """NWS heat-index categories."""
    if feels_c is None:
        return None
    f = feels_c * 9 / 5 + 32
    return ("none" if f < 80 else "caution" if f < 90 else "extreme_caution" if f < 103
            else "danger" if f < 125 else "extreme_danger")
