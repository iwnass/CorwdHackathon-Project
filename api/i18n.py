# GET /api/i18n?lang=de → labels for every code the API returns (place kinds, crowd/air/heat levels, event
#   categories…) in one of 9 languages: en el de fr es ru zh ja ar. `dir` is "rtl" for Arabic.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import i18n  # noqa: E402
from athens.http import make_handler  # noqa: E402

handler = make_handler("/api/i18n", lambda q: {**i18n.labels(q.get("lang", "en")), "languages": list(i18n.LANGS)},
                       cache="public, max-age=86400")
