#!/usr/bin/env python3

from datetime import datetime, timezone


def datetime_to_iso8601(date: datetime) -> str:
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")


def now_to_iso8601(date: datetime) -> str:
    now = datetime.now(timezone.utc)
    return datetime_to_iso8601(now)
