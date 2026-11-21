"""Chat assistant: the City of Athens AthensGov Sandbox bot, plus answers from our own data.

Air quality, heat and "where can I cool down" questions are answered here (the city bot does not have that data);
everything else goes to the city bot (services, appointments, reports, fines…), which keeps the conversation and its
state on its side (conversation_id). Needs ATHENSGOV_SANDBOX_KEY. Its limits: 100 requests/min per key, 2000 chars
per message, "engine": "llm" 20/min and 1000 messages/day.
"""
import json
import math
import os
import threading
import time
import unicodedata
import urllib.error
import urllib.request

from . import cooling, env

BASE = os.environ.get("ATHENSGOV_SANDBOX_URL", "https://athensgov.cityofathens.gr/sandbox")
MAX_TEXT = 2000  # the city bot rejects longer messages (422)
TIMEOUT = 20
RATE_PER_MIN = int(os.environ.get("ATHENSGOV_REQUESTS_PER_MIN", 100))


class NotConfigured(Exception):
    pass


class AthensGovError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


# ---------- Rate limit: all users share one key ----------
# shortcut: per instance; with several Vercel instances running at once, lower ATHENSGOV_REQUESTS_PER_MIN
# or move the bucket to a shared store (e.g. Redis) if the city starts answering 429.
_bucket = {"tokens": float(RATE_PER_MIN), "at": time.monotonic()}
_bucket_lock = threading.Lock()


def _take():
    """Token bucket: RATE_PER_MIN tokens, refilled continuously. No token → 429 with the wait in seconds."""
    with _bucket_lock:
        now = time.monotonic()
        _bucket["tokens"] = min(RATE_PER_MIN, _bucket["tokens"] + (now - _bucket["at"]) * RATE_PER_MIN / 60)
        _bucket["at"] = now
        if _bucket["tokens"] < 1:
            wait = math.ceil((1 - _bucket["tokens"]) * 60 / RATE_PER_MIN)
            raise AthensGovError(429, f"assistant busy, retry in {wait} s")
        _bucket["tokens"] -= 1


def http(method, url, headers, body=None):
    """The only function that touches the network; tests replace it. → parsed JSON"""
    req = urllib.request.Request(url, data=body, headers={"User-Agent": "athens-monitor/1.0", **headers}, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read(1024 * 1024).decode("utf-8"))


def _call(method, path, body=None, request=None):
    key = os.environ.get("ATHENSGOV_SANDBOX_KEY", "").strip()
    if not key:
        raise NotConfigured("ATHENSGOV_SANDBOX_KEY is not set")
    _take()
    headers = {"X-API-Key": key, "Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        return (request or http)(method, f"{BASE}{path}", headers, data)
    except urllib.error.HTTPError as e:  # `from None`: the request carries the key
        raise AthensGovError(e.code, f"AthensGov HTTP {e.code}") from None
    except Exception as e:
        raise AthensGovError(502, f"AthensGov request failed: {type(e).__name__}") from None


# ---------- What we answer ourselves ----------
def _fold(s):
    """Lowercase, no accents: «Ζέστη» → «ζεστη», so Greek, greeklish and English all match."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


# shortcut: keyword routing; swap for the sandbox NLU (/v1/nlu/parse) if it misroutes real questions
TOPICS = [  # first match wins: "it's hot, where can I cool down?" is a cooling question
    ("cooling", ("δροσ", "βρυσ", "πιδακ", "κολυμβητ", "πισιν", "fountain", "cool down", "pool", "drosi", "vrysi", "pidak")),
    ("heat", ("ζεστ", "θερμοκρασ", "καυσων", "heat", "hot", "temperature", "zest", "kafson", "kaysw", "thermokras")),
    ("air", ("αερα", "ατμοσφαιρ", "ρυπαν", "μολυνσ", "aqi", "air quality", "pollution", "aeras", "rypans", "atmosfair")),
]
AIR_EL = {"Good": "Καλή", "Fair": "Ικανοποιητική", "Moderate": "Μέτρια", "Poor": "Κακή", "Very poor": "Πολύ κακή",
          "Extremely poor": "Εξαιρετικά κακή"}
HEAT_EL = {"none": "κανονική", "caution": "προσοχή", "extreme_caution": "αυξημένη προσοχή", "danger": "κίνδυνος",
           "extreme_danger": "μεγάλος κίνδυνος"}
KIND_EL = {"fountain": "Βρύση", "pocket_park": "Πάρκο τσέπης", "pool": "Κολυμβητήριο"}


def topic(text):
    t = _fold(text)
    return next((name for name, words in TOPICS if any(w in t for w in words)), None)


def _reply(name, text, cards=()):
    return {"source": "athens-pulse", "text": text, "speech": text.replace("**", ""),
            "intent": {"name": name, "confidence": 1.0}, "cards": list(cards), "suggestions": []}


def local_answer(name, lat, lon, greek):
    if lat is None:
        return {**_reply(name, "Χρειάζομαι την τοποθεσία σου για να απαντήσω." if greek
                         else "I need your location to answer that."), "state": {"awaiting": "location"}}
    if name == "cooling":
        near = cooling.nearest(cooling.data()[0], lat, lon)
        lines = [f"{KIND_EL[k] if greek else k.replace('_', ' ').title()}: **{s['name']}** ({s['distance_m']} m)"
                 for k, s in sorted(near.items(), key=lambda x: x[1]["distance_m"])]
        cards = [{"type": "cooling", "title": s["name"], "data": {"lat": s["lat"], "lng": s["lon"], "kind": k}}
                 for k, s in near.items()]
        return _reply(name, "\n".join(lines) or ("Δεν βρέθηκε κοντινό σημείο." if greek else "Nothing found nearby."), cards)
    d, _ = env.data()
    h = env.here(d, lat, lon, 1)
    s = (h["nearest_stations"] or [None])[0]
    if s is None:
        return _reply(name, "Δεν υπάρχουν πρόσφατες μετρήσεις." if greek else "No recent readings.")
    card = {"type": "station", "title": s["name"], "data": {"lat": s["lat"], "lng": s["lon"], "station_id": s["station_id"]}}
    zone = h["zone"] or {}
    if name == "air":
        lvl = s["pollution_level"]
        text = (f"Αέρας στο **{s['name']}** ({s['distance_m']} m): **{s['pollution_pct']}%**, {AIR_EL.get(lvl, lvl)}."
                if greek else f"Air at **{s['name']}** ({s['distance_m']} m): **{s['pollution_pct']}%**, {lvl}.")
        za = zone.get("air") or {}
        if za.get("pollution_pct_avg") is not None:
            text += (f" Στη ζώνη σου: {za['pollution_pct_avg']}%." if greek else f" Your zone: {za['pollution_pct_avg']}%.")
        return _reply(name, text, [card])
    lvl = s["heat_level"]
    text = (f"Θερμοκρασία στο **{s['name']}** ({s['distance_m']} m): **{s['temperature']} °C**, αίσθηση {s['feels_like']} °C"
            f" ({HEAT_EL.get(lvl, lvl)})." if greek else
            f"Temperature at **{s['name']}** ({s['distance_m']} m): **{s['temperature']} °C**, feels like {s['feels_like']} °C ({lvl}).")
    return _reply(name, text, [card])


# ---------- Entry point ----------
def ask(text, conversation_id=None, lat=None, lon=None, engine=None, request=None):
    text = " ".join(str(text or "").split())
    if not text:
        raise ValueError("text is empty")
    truncated = len(text) > MAX_TEXT
    text = text[:MAX_TEXT]
    if lat is not None:  # the data is neighbourhood-level; no need to send an exact position anywhere
        lat, lon = round(lat, 3), round(lon, 3)

    name = topic(text)
    if name:
        greek = any("Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿" for c in text)
        return {**local_answer(name, lat, lon, greek), "conversation_id": conversation_id, "truncated": truncated}

    msg = {"text": text}
    if lat is not None:
        msg["location"] = {"lat": lat, "lng": lon}
    if engine in ("rules", "llm"):
        msg["engine"] = engine
    for attempt in (1, 2):
        if not conversation_id:
            conversation_id = _call("POST", "/v1/conversations", {}, request)["id"]
        try:
            reply = _call("POST", f"/v1/conversations/{conversation_id}/messages", msg, request)
            break
        except AthensGovError as e:
            if e.status != 404 or attempt == 2:  # 404: the conversation expired or was reset → start a new one
                raise
            conversation_id = None
    return {**reply, "source": "athensgov", "conversation_id": conversation_id, "truncated": truncated}
