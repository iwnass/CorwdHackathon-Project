# GET /api/config → the Google Maps JavaScript key for the browser.
# A Maps JS key is public by design (the browser loads it); protect it with an HTTP-referrer restriction
# in Google Cloud Console instead of keeping it secret. Set GOOGLE_MAPS_API_KEY in Vercel / .env.local.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens.http import make_handler  # noqa: E402

handler = make_handler("/api/config", lambda q: {"mapsKey": os.environ.get("GOOGLE_MAPS_API_KEY", "")})
