#!/usr/bin/env python3

import os
import pytest

from yaml.constructor import ConstructorError
from pyngsi.utils import eyaml


def test_raw_yaml():
    d = eyaml.load("""
    config:
    username: admin
    password: secret
    service: https://localhost/service
    """)
    assert d == {'config': None, 'password': 'secret',
                 'service': 'https://localhost/service', 'username': 'admin'}


def test_yaml_with_env(mocker):
    mocker.patch.dict(
        os.environ, {'SERVICE_PASSWORD': 'secret', 'SERVICE_HOST': 'localhost'})
    d = eyaml.load("""
    config:
    username: admin
    password: ${SERVICE_PASSWORD}
    service: https://${SERVICE_HOST}/service
    """)
    assert d == {'config': None, 'password': 'secret',
                 'service': 'https://localhost/service', 'username': 'admin'}


def test_yaml_with_env_and_tags(mocker):
    mocker.patch.dict(
        os.environ, {'SERVICE_PASSWORD': 'secret', 'SERVICE_HOST': 'localhost'})
    d = eyaml.load("""
    config:
    username: admin
    password: !ENV ${SERVICE_PASSWORD}
    service: !ENV https://${SERVICE_HOST}/service
    """)
    assert d == {'config': None, 'password': 'secret',
                 'service': 'https://localhost/service', 'username': 'admin'}


def test_yaml_with_env_and_bad_tags(mocker):
    d = None
    mocker.patch.dict(
        os.environ, {'SERVICE_PASSWORD': 'secret', 'SERVICE_HOST': 'localhost'})
    with pytest.raises(ConstructorError):
        d = eyaml.load("""
        config:
        username: admin
        password: !ENW ${SERVICE_PASSWORD}
        service: !ENW https://${SERVICE_HOST}/service
        """)
    assert d is None
