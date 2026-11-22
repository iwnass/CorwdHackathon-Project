"""Chat assistant: the City of Athens AthensGov Sandbox bot, plus answers from our own data.

Heat and "where can I cool down" questions are answered here (the city bot does not have that data);
everything else goes to the city bot (services, appointments, reports, fines…), which keeps the conversation and its
state on its side (conversation_id). Needs ATHENSGOV_SANDBOX_KEY. Its limits: 100 requests/min per key, 2000 chars
per message, "engine": "llm" 20/min and 1000 messages/day.
"""
import json
import math
import os
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter

from . import cooling, culture, env, events, metro
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


# "What events are on today in Athens?" (a suggested quick question): answered from the City of Athens' own
# events (culture.py), else Ticketmaster (events.py); never forwarded to the city bot, whose sandbox events are fictional.
_TODAY_WORDS = ("σημερα", "αποψε", "today", "tonight", "simera", "apopse")
_EVENT_WORDS = ("εκδηλωσ", "συναυλ", "γινεται", "event", "concert", "happening", "on in athens", "ekdilos")


def is_events_today_question(text):
    t = _fold(text)
    return any(w in t for w in _TODAY_WORDS) and any(w in t for w in _EVENT_WORDS)


def _city_events_today(limit):
    """The City of Athens' own events today (cultureisathens.gr), or None if its site can't be read."""
    try:
        d, _ = culture.data()
    except Exception:  # the portal is down or changed: fall back to Ticketmaster
        return None
    today = events.when_range("today")[0].isoformat()
    # a time only for what starts today: an exhibition running since October has no "today" time
    return [{"name": e["title"], "time": e["time"] if e["date"] == today else None, "venue": e["venue"],
             "free": e["free"], "lat": e["lat"], "lon": e["lon"], "url": e["url"]}
            for e in culture.on(d, today)[:limit]]


def _ticketmaster_today(limit):
    try:
        d, _ = events.data()
    except (events.NotConfigured, events.TicketmasterError):
        return None
    return [{"name": e["name"], "time": (e["time"] or "")[:5] or None, "venue": e["venue"]["name"], "free": None,
             "lat": e["venue"]["lat"], "lon": e["venue"]["lon"], "url": e["url"]}
            for e in events.upcoming(d, when="today", limit=limit)["events"]]


def events_today_answer(greek, limit=5):
    """The City of Athens' events first; Ticketmaster only when the city has none today (or can't be reached)."""
    city = _city_events_today(limit)
    today, by_city = (city, True) if city else (_ticketmaster_today(limit), False)
    if today is None and city is None:
        return _reply("events_today", "Οι εκδηλώσεις δεν είναι διαθέσιμες αυτή τη στιγμή." if greek
                      else "Events aren't available right now.")
    if not today:
        return _reply("events_today", "Δεν βρήκα εκδηλώσεις για σήμερα στην Αθήνα." if greek
                      else "I couldn't find any events in Athens today.")
    free = "δωρεάν" if greek else "free"
    lines = [f"- **{e['name']}**: " + " · ".join(x for x in (e["time"], e["venue"], free if e["free"] else None) if x)
             for e in today]
    cards = [{"type": "event", "title": e["name"], "data": {"lat": e["lat"], "lng": e["lon"], "url": e["url"]}}
             for e in today if e["lat"] is not None]
    head = (("Σήμερα από τον Δήμο Αθηναίων:" if greek else "On today from the City of Athens:") if by_city
            else ("Σήμερα στην Αθήνα:" if greek else "On today in Athens:"))
    return _reply("events_today", "\n".join([head, *lines]), cards)


# ---------- Metro & tram: from the STASY timetable (metro.py), never forwarded to the city bot ----------
# Buses and ticket prices aren't in our data: those questions still go to the city bot.
_TRANSIT_WORDS = ("μετρο", "τραμ", "τρενο", "σταθμο", "συρμο", "δρομολογ", "γραμμη", "γραμμες", "συγκοινων",
                  "metro", "subway", "tram", "train", "station", "transport")
_NIGHT_WORDS = ("ολη τη νυχτα", "ολονυχτ", "24ωρ", "24 ωρ", "all night", "24 hour", "24/7", "overnight")
_NEAR_WORDS = ("κοντινοτερ", "πλησιεστερ", "κοντα μου", "nearest", "closest", "near me", "nearby")
_SKIP_WORDS = ("εισιτηρ", "ticket", "fare", "λεωφορ", "bus", "τρολε", "trolley")
ALL_NIGHT = ("M2", "M3", "T6", "T7")  # every Saturday night, as the app's Saturday reminder says
LINE_NAME = {"el": {"M1": "Γραμμή 1 (πράσινη)", "M2": "Γραμμή 2 (κόκκινη)", "M3": "Γραμμή 3 (μπλε)", "T6": "Τραμ T6", "T7": "Τραμ T7"},
             "en": {"M1": "Line 1 (green)", "M2": "Line 2 (red)", "M3": "Line 3 (blue)", "T6": "Tram T6", "T7": "Tram T7"}}


def is_transit_question(text):
    t = _fold(text)
    return any(w in t for w in _TRANSIT_WORDS) and not any(w in t for w in _SKIP_WORDS)


def _stations_in(text):
    """Stations named in the text (Greek or Latin, any case ending): the longest match, every line's stop of that name."""
    t, best, found = _fold(text), 0, []
    for s in metro.data()["stations"]:
        for name in {_fold(s["name"]), _fold(metro.station(s)["name_en"] or "")}:
            stem = name[:-1] if len(name) >= 6 else name  # «Πειραιάς» → also «στον Πειραιά»
            if len(stem) < 4 or not re.search(r"(?<!\w)" + re.escape(stem), t):
                continue
            if len(stem) > best:
                best, found = len(stem), [s]
            elif len(stem) == best and s not in found:
                found.append(s)
    return found


def _timetable_note(greek):
    valid = metro.info()["timetable_valid"]
    return (f"Εκτίμηση από το ωράριο της ΣΤΑΣΥ (ισχύς {valid}) — όχι ζωντανά δεδομένα." if greek
            else f"Estimated from the STASY timetable (valid {valid}) — not live data.")


def _station_answer(stations, greek):
    lang = "el" if greek else "en"
    deps = [dep for s in stations for dep in metro.departures(s["id"])]
    # main directions only (short runs leaving hours from now are noise); late at night, whatever runs next
    shown = [d for d in deps if d["in_min"] and d["in_min"][0] <= 90] or [d for d in deps if d["in_min"]][:4]

    def when(m):
        if m == 0:
            return "τώρα" if greek else "now"
        return f"σε {m}′" if greek else f"in {m} min"

    rows = []
    for dep in shown:
        towards = dep["towards"] if greek else dep["towards_en"]
        soon = ", ".join(f"{t} ({when(m)})" for t, m in zip(dep["next"][:2], dep["in_min"][:2]))
        last = f"τελευταίο {dep['last']}" if greek else f"last {dep['last']}"
        rows.append(f"- **{LINE_NAME[lang].get(dep['line'], dep['line'])} → {towards}**: {soon} · {last}")
    if not rows:
        first = min((d["first"] for d in deps), default=None)
        if first:
            rows = [f"Δεν υπάρχουν άλλα δρομολόγια σήμερα. Το πρώτο αύριο: {first}." if greek
                    else f"No more trains today. The first one tomorrow: {first}."]
        else:
            rows = ["Δεν βρήκα δρομολόγια για σήμερα." if greek else "I couldn't find any trains for today."]

    name = stations[0]["name"] if greek else metro.station(stations[0])["name_en"]
    head = f"Επόμενα δρομολόγια στον σταθμό **{name}**:" if greek else f"Next trains at **{name}**:"
    cards = [{"type": "station", "title": s["name"], "data": {"lat": s["lat"], "lng": s["lon"], "station_id": s["id"]}}
             for s in stations]
    return _reply("metro_station", "\n".join([head, *rows, _timetable_note(greek)]), cards)


def _night_answer(greek):
    saturday = events.when_range("today")[0].weekday() == 5
    lines = ", ".join(LINE_NAME["el" if greek else "en"][x] for x in ALL_NIGHT)
    if greek:
        text = (f"Μόνο τα Σάββατα: όλη τη νύχτα λειτουργούν {lines}. Η Γραμμή 1 και τα τρένα για το αεροδρόμιο όχι.\n"
                + ("Σήμερα είναι Σάββατο — απόψε λειτουργούν όλη τη νύχτα!" if saturday
                   else "Σήμερα δεν είναι Σάββατο: απόψε το μετρό κλείνει μετά τα τελευταία δρομολόγια. "
                        "Ρώτα με για έναν σταθμό για να δεις το τελευταίο."))
    else:
        text = (f"Only on Saturdays: {lines} run all night. Line 1 and the airport trains don't.\n"
                + ("Today is Saturday — they run all night tonight!" if saturday
                   else "Today isn't Saturday: tonight the metro closes after its last trains. "
                        "Ask me about a station to see its last train."))
    return _reply("metro_night", text)


def _nearest_answer(lat, lon, greek):
    if lat is None:
        return {**_reply("metro_near", "Χρειάζομαι την τοποθεσία σου για να απαντήσω." if greek
                         else "I need your location to answer that."), "state": {"awaiting": "location"}}
    near = metro.near(lat, lon, radius_m=2000, k=2)
    if not near:
        return _reply("metro_near", "Δεν υπάρχει σταθμός μετρό ή τραμ σε απόσταση 2 χλμ." if greek
                      else "There's no metro or tram station within 2 km.")
    rows = [f"- **{s['name'] if greek else s['name_en']}**: {', '.join(s['lines'])} · {s['distance_m']} m"
            + (" · χωρίς σκάλες" if greek else " · step-free") * bool(s["step_free"]) for s in near]
    cards = [{"type": "station", "title": s["name"], "data": {"lat": s["lat"], "lng": s["lon"], "station_id": s["id"]}}
             for s in near]
    head = "Οι κοντινότεροι σταθμοί:" if greek else "Nearest stations:"
    return _reply("metro_near", "\n".join([head, *rows]), cards)


def _lines_answer(greek):
    """Each line with its two most frequent destinations (its ends), from the timetable itself."""
    counts = {}
    for by_station in metro.data()["departures"]["weekday"].values():
        for key, times in by_station.items():
            line, towards = key.split("|", 1)
            counts.setdefault(line, Counter())[towards] += len(times)
    lang = "el" if greek else "en"
    rows = []
    for line in sorted(counts):
        ends = [t if greek else metro.transliterate(t) for t, _ in counts[line].most_common(2)]
        rows.append(f"- **{LINE_NAME[lang].get(line, line)}**: {' ↔ '.join(ends)}")
    head = "Οι γραμμές μετρό και τραμ της Αθήνας:" if greek else "Athens metro and tram lines:"
    tip = ("Ρώτα με π.χ. «επόμενο μετρό στο Σύνταγμα» ή «κοντινότερος σταθμός»." if greek
           else "Ask me e.g. \"next metro at Syntagma\" or \"nearest station\".")
    return _reply("metro_lines", "\n".join([head, *rows, tip]))


def transit_answer(text, lat, lon, greek):
    stations = _stations_in(text)
    if stations:
        return _station_answer(stations, greek)
    t = _fold(text)
    if any(w in t for w in _NIGHT_WORDS):
        return _night_answer(greek)
    if any(w in t for w in _NEAR_WORDS):
        return _nearest_answer(lat, lon, greek)
    return _lines_answer(greek)


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
    if is_transit_question(text):
        return {**transit_answer(text, lat, lon, greek), "conversation_id": conversation_id, "truncated": truncated}

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
