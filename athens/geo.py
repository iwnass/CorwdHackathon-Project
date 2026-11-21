"""Distances and point-in-polygon for locating the user."""
import re
from math import asin, cos, radians, sin, sqrt

R = 6371008.8  # mean Earth radius, m


def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres."""
    dphi, dlam = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlam / 2) ** 2
    return 2 * R * asin(min(1.0, sqrt(a)))


def parse_wkt_polygon(wkt):
    """'POLYGON ((lon lat, …), (hole…))' → [[(lon, lat), …], …] (outer ring first), or None."""
    if not wkt or not str(wkt).lstrip().upper().startswith("POLYGON"):
        return None
    rings = []
    for body in re.findall(r"\(([^()]+)\)", str(wkt)):
        try:
            ring = [tuple(float(c) for c in pt.split()[:2]) for pt in body.split(",")]
        except ValueError:
            return None
        if len(ring) >= 3:
            rings.append(ring)
    return rings or None


def _in_ring(lon, lat, ring):
    inside, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def distance_to_boundary_m(lat, lon, rings):
    """Shortest distance from the point to any edge of the polygon, in metres (local flat approximation)."""
    kx, ky = 111320 * cos(radians(lat)), 110540  # metres per degree at this latitude
    best = float("inf")
    for ring in rings or []:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            ax, ay = (x1 - lon) * kx, (y1 - lat) * ky
            bx, by = (x2 - lon) * kx, (y2 - lat) * ky
            dx, dy = bx - ax, by - ay
            seg = dx * dx + dy * dy
            t = 0.0 if seg == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / seg))
            best = min(best, sqrt((ax + t * dx) ** 2 + (ay + t * dy) ** 2))
    return best


def in_polygon(lat, lon, rings):
    return bool(rings) and _in_ring(lon, lat, rings[0]) and not any(_in_ring(lon, lat, h) for h in rings[1:])
