#!/usr/bin/env python3

import pytest
import os
import gzip
import pkg_resources

from os.path import join
from loguru import logger

from pyngsi.sink import SinkNull, SinkStdout, SinkFile, SinkFileGzipped,\
    SinkHttp, SinkOrion, SinkException


def test_sink_null(mocker):
    sink = SinkNull()
    mocker.spy(sink, "write")
    sink.write(msg="dummy")
    assert sink.write.call_count == 1  # pylint: disable=no-member


def test_sink_stdout(capsys):
    sink = SinkStdout()
    sink.write(msg="dummy")
    captured = capsys.readouterr()
    assert captured.out == f"dummy{os.linesep}"


def test_sink_file(tmp_path):
    filename = join(tmp_path, "dummy.txt")
    sink = SinkFile(filename)
    sink.write(msg="dummy")
    sink.close()
    with open(filename, "r", encoding="utf-8") as f:
        read_data = f.read()
    assert read_data == f"dummy{os.linesep}"


def test_sink_file_append(tmp_path):
    test_sink_file(tmp_path)
    filename = join(tmp_path, "dummy.txt")
    sink = SinkFile(filename, append=True)
    sink.write(msg="dummy")
    sink.close()
    with open(filename, "r", encoding="utf-8") as f:
        read_data = f.read()
    assert read_data == f"dummy{os.linesep}dummy{os.linesep}"


def test_sink_file_gz(tmp_path):
    filename = join(tmp_path, "dummy.txt.gz")
    logger.info("filename" + filename)
    sink = SinkFileGzipped(filename)
    sink.write(msg="dummy")
    sink.close()
    with gzip.open(filename, "rt", encoding="utf8") as f:
        read_data = f.read()
    assert read_data == f"dummy{os.linesep}"


def test_sink_http(requests_mock):
    sink = SinkHttp()
    requests_mock.post("http://127.0.0.1:8080/",
                       request_headers={'Content-Type': 'application/json'},
                       additional_matcher=lambda request: "dummy" in request.text)
    sink.write(msg="dummy")


def test_sink_http_error(requests_mock):
    with pytest.raises(SinkException):
        sink = SinkHttp()
        requests_mock.post("http://127.0.0.1:8080/", request_headers={
            'Content-Type': 'application/json'}, status_code=500)
        sink.write(msg="dummy")


def test_sink_http_server_status(requests_mock):
    sink = SinkHttp()
    requests_mock.get("http://127.0.0.1:8080/status",
                      json={'version': '1.0.0'})
    resp = sink.status()
    assert resp["version"] == "1.0.0"


def test_sink_http_server_status_error(requests_mock):
    sink = SinkHttp()
    requests_mock.get("http://127.0.0.1:8080/status", status_code=400)
    resp = sink.status()
    assert resp["state"] == "Down or Unreachable"


def test_sink_orion_no_baseurl():
    sink = SinkOrion()
    assert sink.post_url == "http://127.0.0.1:1026/v2/entities?options=upsert"
    assert sink.status_url == "http://127.0.0.1:1026/version"


def test_sink_orion_baseurl():
    sink = SinkOrion(baseurl="/hopu/orion")
    assert sink.post_url == "http://127.0.0.1:1026/hopu/orion/v2/entities?options=upsert"
    assert sink.status_url == "http://127.0.0.1:1026/hopu/orion/version"


def test_sink_orion_write(requests_mock):
    sink = SinkOrion()
    requests_mock.post("http://127.0.0.1:1026/v2/entities?options=upsert",
                       request_headers={'Content-Type': 'application/json'})
    sink.write(msg=r'{"id": "Room1", "type": "Room")')


def test_sink_orion_write_with_auth(requests_mock):
    sink = SinkOrion(token="00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff")
    requests_mock.post("http://127.0.0.1:1026/v2/entities?options=upsert",
                       request_headers={'Content-Type': 'application/json',
                                        'X-Auth-Token': '00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff'})
    sink.write(msg=r'{"id": "Room1", "type": "Room")')


def test_sink_orion_write_with_auth_env(mocker, requests_mock):
    mocker.patch.dict(
        os.environ, {'ORION_TOKEN': '00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff'})
    sink = SinkOrion()
    requests_mock.post("http://127.0.0.1:1026/v2/entities?options=upsert",
                       request_headers={'Content-Type': 'application/json',
                                        'X-Auth-Token': '00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff'})
    sink.write(msg=r'{"id": "Room1", "type": "Room")')


def test_sink_orion_status(requests_mock):
    sink = SinkOrion()
    requests_mock.get("http://127.0.0.1:1026/version",
                      json={'orion': {'version': '2.2.0-next'}})
    status = sink.status()
    assert status["orion"]["version"] == "2.2.0-next"


def test_sink_orion_status_with_auth(requests_mock):
    sink = SinkOrion(token="00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff")
    requests_mock.get("http://127.0.0.1:1026/version",
                      request_headers={
                          'X-Auth-Token': '00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff'},
                      json={'orion': {'version': '2.2.0-next'}})
    status = sink.status()
    assert status["orion"]["version"] == "2.2.0-next"


def test_sink_orion_status_with_auth_env(mocker, requests_mock):
    mocker.patch.dict(
        os.environ, {'ORION_TOKEN': '00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff'})
    sink = SinkOrion()
    requests_mock.get("http://127.0.0.1:1026/version",
                      request_headers={
                          'X-Auth-Token': '00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff'},
                      json={'orion': {'version': '2.2.0-next'}})
    status = sink.status()
    assert status["orion"]["version"] == "2.2.0-next"


def test_sink_orion_load_config_basic():
    config = {"host": "128.0.0.2", "port": 1127, "secure": True}
    kwargs = SinkOrion._load_config_from_dict(config)
    assert kwargs["hostname"] == "128.0.0.2"
    assert kwargs["port"] == 1127
    assert kwargs["secure"] == True
    assert "service" not in kwargs
    assert "servicepath" not in kwargs
    assert "token" not in kwargs
    assert "user" not in kwargs
    assert "passwd" not in kwargs


def test_sink_orion_load_config_complete():
    config = {"host": "128.0.0.2", "port": 1127, "secure": True, "tenant": {
        "service": "Fiware-Service-1", "service-path": "Fiware-ServicePath-2"},
        "auth": {"user": "foo", "passwd": "bar"}
    }
    kwargs = SinkOrion._load_config_from_dict(config)
    assert kwargs["hostname"] == "128.0.0.2"
    assert kwargs["port"] == 1127
    assert kwargs["secure"] == True
    assert kwargs["service"] == "Fiware-Service-1"
    assert kwargs["servicepath"] == "Fiware-ServicePath-2"
    assert kwargs["user"] == "foo"
    assert kwargs["passwd"] == "bar"


def test_sink_orion_load_config_from_yaml():
    filename = pkg_resources.resource_filename(__name__, "data/orion.yml")
    kwargs = SinkOrion._load_config_from_yaml(filename)
    assert kwargs["hostname"] == "orion.fiware.org"
    assert kwargs["port"] == 1027
    assert kwargs["secure"] == True
    assert kwargs["servicepath"] == "Service-Path-1"
    assert kwargs["user"] == "foo"
    assert kwargs["passwd"] == "bar"


def test_sink_orion_create_from_yaml_config():
    filename = pkg_resources.resource_filename(__name__, "data/orion.yml")
    sink = SinkOrion.from_config(filename)
    assert sink.hostname == "orion.fiware.org"
    assert sink.port == 1027
    assert sink.protocol == "https"
    assert sink.headers['Fiware-ServicePath'] == "Service-Path-1"
    assert sink.user == "foo"
    assert sink.passwd == "bar"


def test_sink_orion_create_from_yaml_config_file_not_found():
    filename = pkg_resources.resource_filename(
        __name__, "data/orion-not-found.yml")
    with pytest.raises(SinkException, match=r".*Cannot read config.*"):
        sink = SinkOrion.from_config(filename)
