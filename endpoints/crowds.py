# GET /api/crowds → live crowd map from the app's own users: every ~220 m cell with at least 3 users in the last
#   15 min — centre, size, count (exact below 10, then "10+", "20+"…) and level (crowd_low / crowd_medium /
#   crowd_high, labels in /api/i18n). Same for everyone → cached 60 s. 503 until the store is configured.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from athens import presence  # noqa: E402
from athens.http import HttpError, make_handler  # noqa: E402


def get(q):
    try:
        return presence.crowds()
    except presence.NotConfigured as e:
        raise HttpError(503, f"crowds unavailable: {e}")


handler = make_handler("/api/crowds", get, cache="public, max-age=30, s-maxage=60")
