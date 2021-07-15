#!/usr/bin/env python3

import pkg_resources
import json

from pyngsi.sources.more_sources import SourceFunc


def request_api():
    json_sample = pkg_resources.resource_string(
        __name__, "data/users_sample.json")
    json_obj = json.loads(json_sample)
    return json_obj["users"]


def test_source():
    src = SourceFunc(request_api)
    rows = [row for row in src]
    assert len(rows) == 5
    assert rows[0].provider == "api"
    assert rows[0].record["userId"] == 1
    assert rows[0].record["firstName"] == "Krish"
    assert rows[4].record["userId"] == 5
    assert rows[4].record["firstName"] == "jone"
