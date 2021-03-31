#!/usr/bin/env python3

from paho.mqtt import client as mqtt_client
from shortuuid import uuid
from loguru import logger

from pyngsi.__init__ import __version__


class MqttError(Exception):
    pass


class MqttConnectError(MqttError):
    pass


CLIENT_ID = f"pyngsi-{__version__}-{uuid()}"


MQTT_CONNECT_RC = ["Connection accepted",  # 0x0
                   "The Server does not support the level of the MQTT protocol requested by the Client",  # 0x1
                   "The Client identifier is correct UTF-8 but not allowed by the Server",  # 0x2
                   "The Network Connection has been made but the MQTT service is unavailable",  # 0x3
                   "The data in the user name or password is malformed",  # 0x4
                   "The Client is not authorized to connect",  # 0x5
                   "Reserved for future use"  # 0x6-0xff
                   ]


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        return client
    elif rc < 6:
        raise MqttConnectError(MQTT_CONNECT_RC)
    else:
        raise MqttConnectError(6)


def mqtt_connect(host: str = "localhost", port: int = 1883, username: str = None, password: str = None) -> mqtt_client:
    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.connect(host, port)
    return client


def mqtt_disconnect():
    pass
