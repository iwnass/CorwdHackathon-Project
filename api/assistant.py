# POST /api/assistant  {"text": "...", "conversation_id"?: "...", "lat"?: 37.98, "lon"?: 23.73, "engine"?: "llm"}
#   → the City of Athens assistant (AthensGov Sandbox) for city services; heat/cooling questions answered from
#     our own data. Send back the returned conversation_id with the next message to keep the dialogue going.
#   503 if ATHENSGOV_SANDBOX_KEY is not set, 429 when the shared key's per-minute limit is reached.
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import assistant  # noqa: E402
from athens.http import HttpError, float_param, make_handler  # noqa: E402

CONV_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")  # it goes into the city API's URL path


def get(q, body, ip=None):
    text = body.get("text")
    if not isinstance(text, str) or not text.strip():
        raise HttpError(400, "text is required")
    conv = body.get("conversation_id")
    if conv is not None and not (isinstance(conv, str) and CONV_ID.match(conv)):
        raise HttpError(400, "bad conversation_id")
    lat = lon = None
    if body.get("lat") is not None or body.get("lon") is not None:
        lat = float_param({"lat": body.get("lat")}, "lat", -90, 90)
        lon = float_param({"lon": body.get("lon")}, "lon", -180, 180)
    try:
        return assistant.ask(text, conv, lat, lon, body.get("engine"))
    except assistant.NotConfigured as e:
        raise HttpError(503, f"assistant unavailable: {e}")
    except assistant.AthensGovError as e:
        raise HttpError(429 if e.status == 429 else 502, str(e))


# no-store: messages and positions are personal
handler = make_handler("/api/assistant", get, cache="private, no-store", method="POST")
