"""Heat index ("feels like"): the NWS formula (Rothfusz regression + adjustments)."""
import math


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
