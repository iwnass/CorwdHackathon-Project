"""Places for visitors from the City of Athens GIS: cultural venues, named places, metro/tram/rail stations,
free WiFi4EU spots and accessible parking — plus the cool-down spots from cooling.py.

Every place: {kind, name (Greek), name_en (English from the city, else a Latin transliteration), address, lat, lon}.
"""
import re
import unicodedata

from . import cache, ckan, cooling
from .geo import haversine

TTL_S = 24 * 3600  # these layers change a few times a year
VENUE_KIND = {"ΜΟΥΣΕΙΟ": "museum", "ΠΙΝΑΚΟΘΗΚΗ": "gallery", "ΒΙΒΛΙΟΘΗΚΗ": "library", "ΘΕΑΤΡΟ": "theatre",
              "ΠΟΛΙΤΙΣΤΙΚΟ ΚΕΝΤΡΟ": "cultural_centre", "ΤΕΧΝΟΠΟΛΙΣ": "cultural_centre", "ΚΙΝΗΜΑΤΟΓΡΑΦΟΣ": "cinema"}
STATION_KIND = {"ΜΕΤΡΟ": "metro_station", "ΤΡΑΜ": "tram_stop", "ΟΣΕ": "rail_station"}

# ---------- Greek → Latin (ELOT 743, simplified) for names the city publishes only in Greek ----------
# shortcut: no ΑΥ/ΕΥ voicing rule or ΓΓ/ΓΚ nuances; good enough to read and recognise a name, not official spelling
_DIGRAPHS = [("ΟΥ", "OU"), ("ΑΥ", "AV"), ("ΕΥ", "EV")]
_LETTERS = dict(zip("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ",
                    ["A", "V", "G", "D", "E", "Z", "I", "TH", "I", "K", "L", "M", "N", "X", "O", "P", "R", "S", "T", "Y",
                     "F", "CH", "PS", "O"]))


def transliterate(text):
    if not text:
        return None
    t = "".join(c for c in unicodedata.normalize("NFD", text.upper()) if unicodedata.category(c) != "Mn")
    t = re.sub(r"\bΜΠ", "B", re.sub(r"\bΝΤ", "D", t))
    for g, l in _DIGRAPHS:
        t = t.replace(g, l)
    return _title("".join(_LETTERS.get(c, c) for c in t))


def _title(s):
    """"43.PL.SYNTAGMATOS(KENTRIKO)" → "43.Pl.Syntagmatos(Kentriko)": capitalise each run of letters, not each word."""
    return re.sub(r"[^\W\d_]+", lambda m: m.group(0).capitalize(), " ".join(s.split())) if s else None


# ---------- Layers ----------
def _point(f):
    g = f.get("geometry") or {}
    pt = g.get("coordinates")
    pt = pt[0] if g.get("type") == "MultiPoint" and pt else pt
    if not pt or len(pt) < 2:
        return None, None
    return ckan.num(pt[1]), ckan.num(pt[0])


def _clean(s):
    return re.sub(r"\s+", " ", (s or "").replace(" - ", " ").strip(" -")) or None


def load(get=ckan.http_get):
    out = []
    got = cooling.layers(["geonode:politismos24_f", "geonode:toponymia", "geonode:stasy2024", "geonode:wifi4eu",
                          "geonode:parking_amea"], get)

    def add(kind, f, name, name_en=None, address=None, **extra):
        lat, lon = _point(f)
        name = _clean(name)
        if lat is not None and lon is not None and name:
            out.append({"kind": kind, "name": name, "name_en": _title(_clean(name_en)) or transliterate(name),
                        "address": _clean(address), "lat": lat, "lon": lon, **extra})

    for f in got["geonode:politismos24_f"]:
        p = f.get("properties") or {}
        add(VENUE_KIND.get(p.get("type"), "cultural_centre"), f, p.get("name"), address=p.get("tax_diefth"),
            link=p.get("link_") or None)
    for f in got["geonode:toponymia"]:
        p = f.get("properties") or {}
        add("place", f, p.get("names_labe") or p.get("names"), p.get("names_eng"), neighbourhood=p.get("synoikia") or None)
    for f in got["geonode:stasy2024"]:
        p = f.get("properties") or {}
        lines = []  # "Γραμμή 1&2-ΜΕΤΡΟ" → ["M1", "M2"]; "Γραμμή 5-ΤΡΑΜ" → ["T5"]
        m = re.match(r"Γραμμή ([\d&]+)-(ΜΕΤΡΟ|ΤΡΑΜ)", p.get("lines") or "")
        if m:
            lines = [("M" if m.group(2) == "ΜΕΤΡΟ" else "T") + n for n in m.group(1).split("&")]
        add(STATION_KIND.get(p.get("eidos"), "metro_station"), f, p.get("name"), p.get("name_en"), lines=lines)
    for f in got["geonode:wifi4eu"]:
        p = f.get("properties") or {}
        add("free_wifi", f, p.get("descr"))
    for f in got["geonode:parking_amea"]:
        p = f.get("properties") or {}
        street = " ".join(x for x in (p.get("street"), p.get("number")) if x)
        add("accessible_parking", f, street, address=street)
    return out


def data():
    return cache.cached("places", TTL_S, load)


def all_places():
    """Places + cool-down spots (fountains, pocket parks, pools) in one list."""
    spots, _ = cooling.data()
    pl, meta = data()
    spots = [{**s, "name": re.sub(r"^\d+\.\s*", "", s["name"] or "")} for s in spots]  # "43.Πλ.Συντάγματος": the city's fountain number
    return pl + [{**s, "name_en": transliterate(s["name"])} for s in spots], meta


def near(items, lat, lon, radius_m=1000, k=10, kinds=None):
    """Items within radius_m (optionally only some kinds), nearest first, with distance_m."""
    out = []
    for p in items:
        if kinds and p["kind"] not in kinds:
            continue
        d = haversine(lat, lon, p["lat"], p["lon"])
        if d <= radius_m:
            out.append({**p, "distance_m": round(d)})
    return sorted(out, key=lambda p: p["distance_m"])[:k]
