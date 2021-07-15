#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import urllib.parse

from datetime import datetime, timedelta
from geojson import Point
from typing import Any
from collections.abc import Sequence, Callable

ONE_WEEK = 7*86400

# https://fiware-orion.readthedocs.io/en/master/user/forbidden_characters/index.html
FORBIDDEN_CHARACTERS = "<>\"'=;()"

# https://jsapi.apiary.io/previews/null/introduction/specification/field-syntax-restrictions
ID_FIELDS_FORBIDDEN_CHARACTERS = "&?/#"
RESERVED_KEYWORDS = ("id", "type", "geo:distance",
                     "dateCreated", "dateModified", "dateExpires", "*")


class NgsiError(Exception):
    pass


class NgsiRestrictionViolationError(NgsiError):
    pass


def escape(value: str) -> str:
    return urllib.parse.quote(value)


def unescape(value: str) -> str:
    return urllib.parse.unquote(value)


class DataModel(dict):

    transient_timeout = None

    def __init__(self, id: str, type: str, strict: bool = False, serializer: Callable = str):
        self.strict = strict
        self.serializer = serializer
        self["id"] = id
        self["type"] = type
        if self.transient_timeout:
            self.add_transient(self.transient_timeout)

    @classmethod
    def set_transient(cls, timeout: int = ONE_WEEK):
        cls.transient_timeout = timeout

    @classmethod
    def unset_transient(cls):
        cls.transient_timeout = None

    @staticmethod
    def enforce_general_restrictions(name: str, value: str):
        if 1 in [c in value for c in FORBIDDEN_CHARACTERS]:
            raise NgsiRestrictionViolationError(
                f"Forbidden character found in field {name}")

    @staticmethod
    def enforce_id_restrictions(name: str):
        if 1 in [c in name for c in ID_FIELDS_FORBIDDEN_CHARACTERS]:
            raise NgsiRestrictionViolationError(
                f"Forbidden character found in field {name}")
        l = len(name)
        if l < 1:
            raise NgsiRestrictionViolationError(
                f"{name} length must be at least 1")
        elif l > 256:
            raise NgsiRestrictionViolationError(
                f"{name} length must not exceed 256")
        if name in RESERVED_KEYWORDS:
            raise NgsiRestrictionViolationError(
                f"{name} uses a reserved keyword")

    def add(self, name: str, value: Any,
            isdate: bool = False, isurl: bool = False, urlencode=False, metadata: dict = {}):
        if self.strict:
            self.enforce_id_restrictions(name)
            self.enforce_general_restrictions(name, value)
        if isinstance(value, str):
            if isdate:
                t = "DateTime"
            elif isurl:
                t = "URL"
            elif urlencode:
                t = "STRING_URL_ENCODED"
            else:
                t = "Text"
            v = escape(value) if urlencode else value
        elif isinstance(value, bool):
            t, v = "Boolean", value
        elif isinstance(value, int):
            t, v = "Number", value
        elif isinstance(value, float):
            t, v = "Number", value
        elif isinstance(value, datetime):
            # the value datetime MUST be UTC
            t, v = "DateTime", value.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif isinstance(value, Point):
            t, v = "geo:json", value
        elif isinstance(value, tuple) and len(value) == 2:
            lat, lon = value
            try:
                location = Point((lon, lat))
            except Exception as e:
                raise NgsiError(f"Cannot create geojson field : {e}")
            t, v = "geo:json", location
        elif isinstance(value, Sequence):
            t, v = "Array", value
        elif isinstance(value, dict):
            t, v = "Property", value
        else:
            raise NgsiError(
                f"Cannot map {type(value)} to NGSI type. {name=} {value=}")
        self[name] = {"value": v, "type": t}
        if metadata:
            self[name]["metadata"] = metadata

    def add_date(self, *args, **kwargs):
        self.add(isdate=True, *args, **kwargs)

    def add_now(self, *args, **kwargs):
        self.add(value=datetime.utcnow(), *args, **kwargs)

    def add_url(self, *args, **kwargs):
        self.add(isurl=True, *args, **kwargs)

    def add_relationship(self, rel_name: str, fq_ref_type: str, ref_id: str):
        """Add Entity relationship

        Args:
            rel_name (str): the relation name (should start with "ref:")
            fq_ref_type (str): the fully qualified type (including namespace), i.e. urn:ngsi-ld:Shelf
            ref_id (str): the datamodel identifier

        Raises:
            NgsiException
        """
        if self.strict and not rel_name.startswith("ref"):
            raise NgsiError(
                f"Bad relationship name : {rel_name}. Relationship attributes must use prefix 'ref'")
        t, v = "Relationship", f"{fq_ref_type}:{ref_id}"
        self[rel_name] = {"value": v, "type": t}

    def add_address(self, value: dict):
        t, v = "PostalAddress", value
        self["address"] = {"value": v, "type": t}

    def add_transient(self, timeout: int = ONE_WEEK, expire: datetime = None):
        if not expire:
            expire = datetime.utcnow() + timedelta(seconds=timeout)
        self.add("dateExpires", expire)

    def json(self):
        """Returns the datamodel in json format"""
        return json.dumps(self, default=self.serializer, ensure_ascii=False)

    def pprint(self):
        """Returns the datamodel pretty-json-formatted"""
        print(json.dumps(self, default=self.serializer, indent=2))
