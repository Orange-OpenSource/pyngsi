#!/usr/bin/env python3

import time
import signal

from paho.mqtt.client import MQTTMessage
from queue import SimpleQueue as Queue
from loguru import logger
from typing import Union, Sequence, Tuple, Literal

from pyngsi.sources.source import Source, Row, ROW_NOT_SET as QUEUE_EOT
from pyngsi.utils.mqttclient import MqttClient, MQTT_DEFAULT_PORT

OneOrManyStrings = Union[str, Sequence[str]]


class SourceMqtt(Source):
    """A SourceMqtt receives data from a MQTT broker on a given topic.

        Each time a message is received on the subscribed topic(s), the Source emits a Row composed of the message payload.
        The row provider is set to the topic.    
    """

    def __init__(self,
                 host: str = "localhost",
                 port: int = MQTT_DEFAULT_PORT,
                 credentials: Tuple[str, str] = (None, None),
                 topic: OneOrManyStrings = "#",  # all topics
                 qos: Literal[0, 1, 2] = 0  # no ack
                 ):
        """Returns a SourceMqtt instance.

        Args:
            host (str): Hostname or IP address of the remote broker. Defaults to "localhost".
            port (int): Network port of the server host to connect to. Defaults to 1883.
            credentials (str,str): Username and password used in broker authentication. Defaults to no auth.
            topic (OneOrManyStrings): Topic (or list of topics) to subscribe to. Defaults to "#" (all topics).
            qos (Literal[0, 1, 2]) : QoS : 0, 1 or 2 according to the MQTT protocol. Defaults to 0 (no ack).

        """
        self.topic = topic
        self.queue: "Queue[Row]" = Queue()
        user, passwd = credentials
        self.mcsub: MqttClient = MqttClient(host, port, user, passwd,
                                            qos, callback=self._callback)
        # install signal hooks
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGQUIT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except ValueError as e:
            logger.warning(e)

    def __iter__(self):
        self.mcsub.subscribe(self.topic)
        while True:
            row: Row = self.queue.get(True)
            if row == QUEUE_EOT:  # End Of Transmission
                logger.info("Received EOT")
                break
            yield row
        self.mcsub.stop()

    def _callback(self, msg: MQTTMessage):
        payload = str(msg.payload.decode("utf-8"))
        self.queue.put(Row(msg.topic, payload))

    def _handle_signal(self, signum, frame):
        """Properly clean resources when a signal is received"""
        logger.info("Received SIGNAL : ")
        logger.info("Stopping loop...")
        self.queue.put(QUEUE_EOT)
        time.sleep(1)

    def close(self):
        """Properly disconnect from MQTT broker and free resources
        """
        self.queue.put(QUEUE_EOT)
        self.mcsub.stop()
