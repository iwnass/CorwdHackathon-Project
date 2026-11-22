"""Chat assistant: the City of Athens AthensGov Sandbox bot, plus answers from our own data.

Heat and "where can I cool down" questions are answered here (the city bot does not have that data);
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

from . import cooling, env, events
from .geo import haversine

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
    ("heat", ("θερμοκρασ", "καυσων", "heat", "hot", "temperature", "kafson", "kaysw", "thermokras")),
]
HEAT_EL = {"none": "κανονική", "caution": "προσοχή", "extreme_caution": "αυξημένη προσοχή", "danger": "κίνδυνος",
           "extreme_danger": "μεγάλος κίνδυνος"}
KIND_EL = {"fountain": "Βρύση", "pocket_park": "Πάρκο τσέπης", "pool": "Κολυμβητήριο"}


def topic(text):
    t = _fold(text)
    return next((name for name, words in TOPICS if any(w in t for w in words)), None)


# Obvious off-app chit-chat, blocked before it ever reaches the city bot (real city-service questions —
# fines, appointments, KEP, the 570 municipal services — still go through as before).
OFF_TOPIC_WORDS = (
    "write me a poem", "write a poem", "write me a song", "write a story", "write me code", "write some code",
    "ποιημα", "τραγουδι", "γραψε μου μια ιστορια", "κωδικα για",
    "python", "javascript", "typescript", "c++", " html", " css", " sql",
    "translate this", "μεταφρασε",
    "tell me a joke", "ένα αστειο", "ενα αστειο",
    "capital of", "πρωτευουσα του",
    "who won the world cup", "who is the president of", "ποιος ειναι ο προεδρος",
    "ignore previous instructions", "ignore all instructions", "system prompt", "pretend you are", "act as a",
    "solve this equation", "λυσε την εξισωση",
    "recipe for", "συνταγη για",
)


def is_off_topic(text):
    t = _fold(text)
    return any(w in t for w in OFF_TOPIC_WORDS)


def off_topic_answer(greek):
    text = ("Μπορώ να βοηθήσω μόνο με θέματα της εφαρμογής — εκδηλώσεις, μέσα μαζικής μεταφοράς, φόρτιση EV & "
            "πάρκινγκ, σημεία δροσιάς, αξιοθέατα, και υπηρεσίες του Δήμου Αθηναίων. Δοκίμασε κάτι από αυτά!"
            if greek else
            "I can only help with things in this app — events, public transit, EV charging & parking, "
            "cool-down spots, places to visit, and City of Athens services. Try asking about one of those!")
    return _reply("off_topic", text)


def _is_search_dump(text):
    """The sandbox's generic "found these documents on the website" fallback (a raw markdown link list)
    when its rules engine has no real scripted answer — not an actual reply, so don't show it as one.
    Seen in both Greek ("...βρήκα:") and English ("...I found:") phrasings."""
    t = _fold(text or "")
    return ("i found:" in t or "βρηκα:" in t) and "](http" in (text or "")


def no_answer_reply(greek):
    text = ("Δεν βρήκα συγκεκριμένη απάντηση για αυτό. Μπορώ να βοηθήσω με εκδηλώσεις, μέσα μαζικής μεταφοράς, "
            "φόρτιση EV & πάρκινγκ, σημεία δροσιάς, αξιοθέατα, και υπηρεσίες του Δήμου Αθηναίων."
            if greek else
            "I don't have a direct answer for that. I can help with events, public transit, EV charging & "
            "parking, cool-down spots, places to visit, and City of Athens services.")
    return _reply("no_answer", text)


# "How do I get to the Acropolis by metro?" is one of the three suggested quick questions (agent.s2 in every
# locale) — answered here with the real nearby station (see transitData.js) instead of forwarding it to the
# city bot, which has no fixed answer for it and was returning generic web-search-style links.
AKROPOLI_STATION = {"lat": 37.9688, "lon": 23.7295}  # Akropoli station, Metro Line 2 (red)
ACROPOLIS_ENTRANCE = {"lat": 37.9715, "lon": 23.7257}  # main archaeological site entrance
_ACROPOLIS_WORDS = ("ακροπολ", "acropoli", "akropoli")
_METRO_WORDS = ("μετρο", "metro", "υπογειο", "subway")


def is_acropolis_metro_question(text):
    t = _fold(text)
    return any(w in t for w in _ACROPOLIS_WORDS) and any(w in t for w in _METRO_WORDS)


def acropolis_metro_answer(greek):
    walk_m = round(haversine(AKROPOLI_STATION["lat"], AKROPOLI_STATION["lon"],
                              ACROPOLIS_ENTRANCE["lat"], ACROPOLIS_ENTRANCE["lon"]) / 10) * 10
    card = {"type": "station", "title": "Akropoli",
            "data": {"lat": AKROPOLI_STATION["lat"], "lng": AKROPOLI_STATION["lon"], "station_id": "akropoli"}}
    text = (f"Πάρε τη **Γραμμή 2** (κόκκινη) του μετρό μέχρι τον σταθμό **Ακρόπολη** — η κύρια είσοδος του "
            f"αρχαιολογικού χώρου είναι περίπου {walk_m} μ. με τα πόδια από εκεί."
            if greek else
            f"Take **Metro Line 2** (the red line) to **Akropoli** station — the main entrance to the "
            f"archaeological site is about {walk_m} m on foot from there.")
    return _reply("acropolis_metro", text, [card])


# "What events are on today in Athens?" (a suggested quick question): answered from our own events data
# (Ticketmaster via events.py), never forwarded to the city bot, whose sandbox events are fictional.
_TODAY_WORDS = ("σημερα", "αποψε", "today", "tonight", "simera", "apopse")
_EVENT_WORDS = ("εκδηλωσ", "συναυλ", "γινεται", "event", "concert", "happening", "on in athens", "ekdilos")


def is_events_today_question(text):
    t = _fold(text)
    return any(w in t for w in _TODAY_WORDS) and any(w in t for w in _EVENT_WORDS)


def events_today_answer(greek, limit=5):
    try:
        d, _ = events.data()
    except (events.NotConfigured, events.TicketmasterError):
        return _reply("events_today", "Οι εκδηλώσεις δεν είναι διαθέσιμες αυτή τη στιγμή." if greek
                      else "Events aren't available right now.")
    today = events.upcoming(d, when="today", limit=limit)["events"]
    if not today:
        return _reply("events_today", "Δεν βρήκα εκδηλώσεις για σήμερα στην Αθήνα." if greek
                      else "I couldn't find any events in Athens today.")
    lines = [f"- **{e['name']}**: " + " · ".join(x for x in ((e["time"] or "")[:5], e["venue"]["name"]) if x)
             for e in today]
    cards = [{"type": "event", "title": e["name"], "data": {"lat": e["venue"]["lat"], "lng": e["venue"]["lon"], "url": e["url"]}}
             for e in today if e["venue"]["lat"] is not None]
    head = "Σήμερα στην Αθήνα:" if greek else "On today in Athens:"
    return _reply("events_today", "\n".join([head, *lines]), cards)


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
    lvl = s["heat_level"]
    text = (f"Θερμοκρασία στο **{s['name']}** ({s['distance_m']} m): **{s['temperature']} °C**, αίσθηση {s['feels_like']} °C"
            f" ({HEAT_EL.get(lvl, lvl)})." if greek else
            f"Temperature at **{s['name']}** ({s['distance_m']} m): **{s['temperature']} °C**, feels like {s['feels_like']} °C ({lvl}).")
    return _reply(name, text, [card])


# ---------- Entry point ----------
def ask(text, conversation_id=None, lat=None, lon=None, request=None):
    text = " ".join(str(text or "").split())
    if not text:
        raise ValueError("text is empty")
    truncated = len(text) > MAX_TEXT
    text = text[:MAX_TEXT]
    if lat is not None:  # the data is neighbourhood-level; no need to send an exact position anywhere
        lat, lon = round(lat, 3), round(lon, 3)

    greek = any("Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿" for c in text)
    if is_off_topic(text):
        return {**off_topic_answer(greek), "conversation_id": conversation_id, "truncated": truncated}
    if is_acropolis_metro_question(text):
        return {**acropolis_metro_answer(greek), "conversation_id": conversation_id, "truncated": truncated}
    if is_events_today_question(text):
        return {**events_today_answer(greek), "conversation_id": conversation_id, "truncated": truncated}

    name = topic(text)
    if name:
        return {**local_answer(name, lat, lon, greek), "conversation_id": conversation_id, "truncated": truncated}

    msg = {"text": text}
    if lat is not None:
        msg["location"] = {"lat": lat, "lng": lon}
    # always the rules engine (the registered municipal services), never the free-form "llm" engine:
    # that one isn't scoped to the app's own services and shouldn't be reachable by a client-supplied field
    msg["engine"] = "rules"
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
    if _is_search_dump(reply.get("text", "")):
        return {**no_answer_reply(greek), "conversation_id": conversation_id, "truncated": truncated}
    return {**reply, "source": "athensgov", "conversation_id": conversation_id, "truncated": truncated}
