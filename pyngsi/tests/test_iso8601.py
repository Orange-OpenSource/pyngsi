#!/usr/bin/env python3

from datetime import datetime, timezone

from pyngsi.utils.iso8601 import datetime_to_iso8601

def test_datetime_to_iso8601():
    dt = datetime(2021, 5, 18, 17, 45, 00, tzinfo=timezone.utc)
    assert datetime_to_iso8601(dt) == "2021-05-18T17:45:00Z"
