# Every /api/* endpoint in one Vercel Function: the Hobby plan allows at most 12 Functions per deployment.
# The endpoints live in endpoints/*.py (one per route); vercel.json rewrites /api/* here.
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from athens.http import Dispatch, load_endpoints  # noqa: E402

load_endpoints(os.path.join(ROOT, "endpoints"))


class handler(Dispatch):
    pass
