"""City of Athens cultural events from cultureisathens.gr, the municipality's culture portal.

It has no events API with dates: its WordPress REST API lists events (title, link), but each event's date,
status, venue, price and map position exist only on the event's page. So the candidates are the most recently
edited events (REST, orderby=modified) plus the ones featured on the homepage, and each page is read for those
fields. One city-wide refresh every few hours, the same for every user. Pages are parsed by the theme's labels
(gt-start-date, gt-venue, data-lat…): if the site's template changes, events simply stop appearing.
"""
import html
import json
import re
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from . import cache
from .geo import haversine

BASE = "https://cultureisathens.gr"
TTL_S = 3 * 3600
CANDIDATES = 40  # most recently edited events; with the homepage's featured ones that covers what's on now
TIMEOUT = 8  # per page: a slow moment on the site drops a few events instead of stalling the answer
MAX_BYTES = 2 * 1024 * 1024
MONTHS = {m: i for i, m in enumerate(("ιανουαριου", "φεβρουαριου", "μαρτιου", "απριλιου", "μαιου", "ιουνιου", "ιουλιου",
                                      "αυγουστου", "σεπτεμβριου", "οκτωβριου", "νοεμβριου", "δεκεμβριου"), 1)}
STATUS = {"τρεχουσα": "current", "προσεχεις": "upcoming"}


def http_get(url):
    """The only function that touches the network; tests replace it."""
    req = urllib.request.Request(url, headers={"User-Agent": "athens-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(MAX_BYTES).decode("utf-8", "replace")


def _fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def _text(fragment):
    text = html.unescape(re.sub(r"<[^>]+>", " ", fragment or "")).replace("￼", "")  # ￼: leftover embed marks in titles
    return re.sub(r"\s+", " ", text).strip() or None


def _field(page, cls):
    m = re.search(rf'<li class="{cls}">.*?<div class="gt-inner">(.*?)</div>', page, re.S)
    return _text(m.group(1)) if m else None


def parse_date(text):
    """"22 Νοεμβρίου 2026 10:00" → ("2026-11-22", "10:00"); the time is optional."""
    m = re.match(r"(\d{1,2})\s+(\S+)\s+(\d{4})(?:\s+(\d{1,2}):(\d{2}))?", text or "")
    month = MONTHS.get(_fold(m.group(2))) if m else None
    if not month:
        return None, None
    try:
        day = date(int(m.group(3)), month, int(m.group(1))).isoformat()
    except ValueError:
        return None, None
    return day, f"{int(m.group(4)):02d}:{m.group(5)}" if m.group(4) else None


def parse_event(page, url):
    """An event page → its details, or None if it has no readable date."""
    day, time = parse_date(_field(page, "gt-start-date"))
    if not day:
        return None
    title = re.search(r"<title>(.*?)</title>", page, re.S)
    title = _text(title.group(1)) if title else None
    title = title.split(" - Culture is Athens")[0].strip() if title else None
    pos = re.search(r'data-lat="(-?\d+\.\d+)" data-lng="(-?\d+\.\d+)"', page)
    price = re.search(r'<div class="gt-price">(.*?)</div>', page, re.S)
    price = _text(price.group(1)) if price else None
    status = _field(page, "gt-status")
    return {"title": title or url, "url": url, "date": day, "time": time,
            "status": STATUS.get(_fold(status or ""), "past" if status else None),
            "venue": _field(page, "gt-venue") or _field(page, "gt-locations"),
            "category": _field(page, "gt-categories"),
            "free": _fold(price) in ("free", "δωρεαν") if price else None, "price": price,
            "lat": float(pos.group(1)) if pos else None, "lon": float(pos.group(2)) if pos else None}


def candidates(get=http_get):
    rest = json.loads(get(f"{BASE}/wp-json/wp/v2/event?per_page={CANDIDATES}&orderby=modified&order=desc&_fields=link"))
    home = re.findall(rf'href="({re.escape(BASE)}/event/[^"/]+/)"', get(f"{BASE}/"))
    return list(dict.fromkeys([e["link"] for e in rest] + home))


def load(get=http_get):
    def one(url):
        try:
            return parse_event(get(url), url)
        except Exception:  # one broken page must not hide the others
            return None
    with ThreadPoolExecutor(8) as pool:
        found = [e for e in pool.map(one, candidates(get)) if e]
    return {"events": sorted(found, key=lambda e: (e["date"], e["time"] or ""))}


def data():
    return cache.cached("culture", TTL_S, load)


def on(d, day):
    """Events on `day` (an ISO date): the ones starting that day, then the ones running (status "current")."""
    starting = [e for e in d["events"] if e["date"] == day]
    running = [e for e in d["events"] if e["status"] == "current" and e["date"] < day]
    return starting + running


def upcoming(d, day):
    """From `day` on, plus whatever is running now; past events left out."""
    return [e for e in d["events"] if e["date"] >= day or e["status"] == "current"]


def nearby(items, lat, lon, k=5):
    """The k events with a map position nearest to (lat, lon), with distance_m."""
    near = [{**e, "distance_m": round(haversine(lat, lon, e["lat"], e["lon"]))} for e in items if e["lat"] is not None]
    return sorted(near, key=lambda e: e["distance_m"])[:k]
