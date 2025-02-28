#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

from datetime import datetime, timedelta, timezone
from geojson import Point

from pyngsi.ngsi import DataModel, NgsiError, NgsiRestrictionViolationError, unescape, ONE_WEEK


def test_create():
    m = DataModel("id", "type")
    assert m["id"] == "id"
    assert m["type"] == "type"


def test_add_field_str():
    m = DataModel("id", "type")
    m.add("projectName", "Pixel")
    assert m.json(
    ) == r'{"id": "id", "type": "type", "projectName": {"value": "Pixel", "type": "Text"}}'


def test_add_field_str_escaped():
    m = DataModel("id", "type")
    m.add("forbiddenCharacters", r"""BEGIN<>"'=;()END""", urlencode=True)
    assert m.json(
    ) == r'{"id": "id", "type": "type", "forbiddenCharacters": {"value": "BEGIN%3C%3E%22%27%3D%3B%28%29END", "type": "STRING_URL_ENCODED"}}'
    assert unescape(m["forbiddenCharacters"]["value"]
                    ) == r"""BEGIN<>"'=;()END"""


def test_add_field_int():
    m = DataModel("id", "type")
    m.add("temperature", 37)
    assert m.json(
    ) == r'{"id": "id", "type": "type", "temperature": {"value": 37, "type": "Number"}}'


def test_add_field_float():
    m = DataModel("id", "type")
    m.add("temperature", 37.2)
    assert m.json(
    ) == r'{"id": "id", "type": "type", "temperature": {"value": 37.2, "type": "Number"}}'


def test_add_field_bool():
    m = DataModel("id", "type")
    m.add("loading", True)
    assert m.json(
    ) == r'{"id": "id", "type": "type", "loading": {"value": true, "type": "Boolean"}}'


def test_add_field_date_from_str_old_way():
    m = DataModel("id", "type")
    m.add("dateObserved", "2018-01-01T15:00:00", isdate=True)
    assert m.json(
    ) == r'{"id": "id", "type": "type", "dateObserved": {"value": "2018-01-01T15:00:00", "type": "DateTime"}}'


def test_add_field_date_from_str():
    m = DataModel("id", "type")
    m.add_date("dateObserved", "2018-01-01T15:00:00")
    assert m.json(
    ) == r'{"id": "id", "type": "type", "dateObserved": {"value": "2018-01-01T15:00:00", "type": "DateTime"}}'


def test_add_field_url_from_str_old_way():
    m = DataModel("id", "type")
    m.add("dataProvider", "https://www.fiware.org", isurl=True)
    assert m.json(
    ) == r'{"id": "id", "type": "type", "dataProvider": {"value": "https://www.fiware.org", "type": "URL"}}'


def test_add_field_url_from_str():
    m = DataModel("id", "type")
    m.add_url("dataProvider", "https://www.fiware.org")
    assert m.json(
    ) == r'{"id": "id", "type": "type", "dataProvider": {"value": "https://www.fiware.org", "type": "URL"}}'


def test_add_field_date_from_datetime():
    m = DataModel("id", "type")
    d = datetime(2019, 6, 1, 18, 30, 0)
    m.add("dateObserved", d)
    assert m.json(
    ) == r'{"id": "id", "type": "type", "dateObserved": {"value": "2019-06-01T18:30:00Z", "type": "DateTime"}}'


def test_add_location_from_tuple():
    m = DataModel("id", "type")
    m.add("location", (44.8333, -0.5667))
    assert m.json(
    ) == r'{"id": "id", "type": "type", "location": {"value": {"type": "Point", "coordinates": [-0.5667, 44.8333]}, "type": "geo:json"}}'


def test_add_location_from_geojson():
    m = DataModel("id", "type")
    location = Point((-0.5667, 44.8333))
    m.add("location", location)
    assert m.json(
    ) == r'{"id": "id", "type": "type", "location": {"value": {"type": "Point", "coordinates": [-0.5667, 44.8333]}, "type": "geo:json"}}'


def test_add_location_invalid():
    m = DataModel("id", "type")
    with pytest.raises(NgsiError, match=r".*JSON compliant.*"):
        m.add("location", ('A', -0.5667))


def test_cannot_map_ngsi_type():
    m = DataModel("id", "type")
    with pytest.raises(NgsiError, match=r".*Cannot map.*"):
        m.add("unknown", None)


def test_add_field_sequence():
    m = DataModel("id", "type")
    d1 = {}
    d1["major"] = "standard"
    d1["minor"] = "surface"
    d1["dateObserved"] = datetime(2019, 6, 1, 18, 30, 0)
    seq = [{"major": "standard", "minor": "surface", "elapsed": 3600},
           {"major": "standard", "minor": "tropopause", "elapsed": 1800},
           d1]
    m.add("collection", seq)
    assert m.json() == r'{"id": "id", "type": "type", ' \
        r'"collection": {"value": [{"major": "standard", "minor": "surface", "elapsed": 3600}, ' \
        r'{"major": "standard", "minor": "tropopause", "elapsed": 1800}, ' \
        r'{"major": "standard", "minor": "surface", "dateObserved": "2019-06-01 18:30:00"}], ' \
        r'"type": "Array"}}'


# https://fiware-datamodels.readthedocs.io/en/latest/Environment/AirQualityObserved/doc/spec/index.html#representing-air-pollutants
def test_metadata():
    m = DataModel("AirQualityObserved", "AirQualityObserved")
    unitsGP = {"unitCode": {"value": "GP"}}
    unitsGQ = {"unitCode": {"value": "GQ"}}
    m.add("CO", 500, metadata=unitsGP)
    m.add("NO", 45, metadata=unitsGQ)
    assert m.json() == r'{"id": "AirQualityObserved", "type": "AirQualityObserved", ' \
        r'"CO": {"value": 500, "type": "Number", "metadata": {"unitCode": {"value": "GP"}}}, ' \
        r'"NO": {"value": 45, "type": "Number", "metadata": {"unitCode": {"value": "GQ"}}}}'


def test_add_relationship():
    # https://github.com/Fiware/tutorials.Entity-Relationships
    m = DataModel("id", "type")
    m.add_relationship("refStore", "urn:ngsi-ld:Shelf", "001")
    assert m.json() == r'{"id": "id", "type": "type", ' \
        r'"refStore": {"value": "urn:ngsi-ld:Shelf:001", "type": "Relationship"}}'


def test_add_relationship_bad_ref():
    m = DataModel("id", "type", strict=True)
    with pytest.raises(NgsiError, match=r".*Bad relationship.*"):
        m.add_relationship("store", "Shelf", "001")


def test_add_dict():
    m = DataModel("id", "type")
    m.add("property", {"a": 1, "b": 2})
    assert m.json() == r'{"id": "id", "type": "type", ' \
        r'"property": {"value": {"a": 1, "b": 2}, "type": "Property"}}'


def test_add_address():
    m = DataModel("id", "type")
    addr = {"addressLocality": "London",
            "postalCode": "EC4N 8AF",
            "streetAddress": "25 Walbrook"}
    m.add_address(addr)
    assert m.json() == r'{"id": "id", "type": "type", ' \
        r'"address": {"value": {"addressLocality": "London", ' \
        r'"postalCode": "EC4N 8AF", "streetAddress": "25 Walbrook"}, ' \
        r'"type": "PostalAddress"}}'


def test_add_transient_expire_date():
    christmas_under_lockdown = datetime(
        2020, 12, 25, 12, 00, tzinfo=timezone.utc)
    m = DataModel("id", "type")
    m.add_transient(expire=christmas_under_lockdown)
    assert m.json() == r'{"id": "id", "type": "type", ' \
        r'"dateExpires": {"value": "2020-12-25T12:00:00Z", "type": "DateTime"}}'


def test_add_transient_timeout_1d():
    now = datetime.utcnow()
    m = DataModel("id", "type")
    m.add_transient(timeout=86400)
    tomorrow = now + timedelta(days=1)
    assert m['dateExpires']['value'][:10] == tomorrow.strftime("%Y-%m-%d")


def test_set_implicit_transient():
    now = datetime.utcnow()
    DataModel.set_transient(timeout=ONE_WEEK)
    m = DataModel("id", "type")
    a_week_later = now + timedelta(weeks=1)
    assert m['dateExpires']['value'][:10] == a_week_later.strftime("%Y-%m-%d")


def test_unset_implicit_transient():
    DataModel.set_transient()
    DataModel.unset_transient()
    assert DataModel.transient_timeout is None
    m = DataModel("id", "type")
    assert m.json() == r'{"id": "id", "type": "type"}'


def test_enforce_general_restrictions():
    m = DataModel("id", "type", strict=True)
    with pytest.raises(NgsiRestrictionViolationError):
        m.add("projectName", "P<ixel")


def test_enforce_id_restrictions_forbidden_char():
    m = DataModel("id", "type", strict=True)
    with pytest.raises(NgsiRestrictionViolationError):
        m.add("project&Name", "Pixel")


def test_enforce_id_restrictions_max_length_exceeded():
    m = DataModel("id", "type", strict=True)
    with pytest.raises(NgsiRestrictionViolationError):
        m.add("projectName"+'-'*256, "Pixel")


def test_enforce_id_restrictions_length_too_short():
    m = DataModel("id", "type", strict=True)
    with pytest.raises(NgsiRestrictionViolationError):
        m.add("", "Pixel")


def test_enforce_id_restrictions_reserved_keyword():
    m = DataModel("id", "type", strict=True)
    with pytest.raises(NgsiRestrictionViolationError):
        m.add("id", "Pixel")


def test_strict_mode():
    m = DataModel("id", "type", strict=True)
    with pytest.raises(NgsiRestrictionViolationError):
        m.add("id", "Pixel")
