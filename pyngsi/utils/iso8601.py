#!/usr/bin/env python3

from datetime import datetime


def datetime_to_iso8601(date: datetime) -> str:
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")


def now_iso8601() -> str:
    now = datetime.utcnow()
    return datetime_to_iso8601(now)
