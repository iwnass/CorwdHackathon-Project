"""UTC parsing and Athens local time. The city's datasets are all in UTC."""
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    ATHENS = ZoneInfo("Europe/Athens")
except Exception:  # host without a tz database: apply the EU rule ourselves
    ATHENS = None


def _last_sunday_1utc(year, month):
    d = datetime(year, month + 1, 1, 1, tzinfo=timezone.utc) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() + 1) % 7)


def _athens_offset(dt):
    """EU summer time: last Sunday of March 01:00 UTC → last Sunday of October 01:00 UTC."""
    u = dt.astimezone(timezone.utc)
    summer = _last_sunday_1utc(u.year, 3) <= u < _last_sunday_1utc(u.year, 10)
    return timezone(timedelta(hours=3 if summer else 2))


def parse_utc(s):
    dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def iso_utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_local(dt):
    return dt.astimezone(ATHENS or _athens_offset(dt)).isoformat(timespec="minutes")


def now_utc():
    return datetime.now(timezone.utc)
