#!/usr/bin/env python3

# This example requires a local MQTT broker
# docker run -d --net=host --name mqtt -p 1883:1883 eclipse-mosquitto

# Once the broker running : publish temp values that will be processed by the agent
# docker exec -it mqtt mosquitto_pub -h localhost -t sensor/temperature -m 22.5

from pyngsi.agent import NgsiAgent
from pyngsi.sources.source import Row
from pyngsi.sources.source_mqtt import SourceMqtt
from pyngsi.sink import SinkStdout
from pyngsi.ngsi import DataModel


def build_entity(row: Row) -> DataModel:
    temperature = row.record
    m = DataModel(id="Room1", type="Room")
    m.add("temperature", float(temperature))
    return m


def main():
    src = SourceMqtt(topic="sensor/temperature")
    # if you have an Orion server available, just replace SinkStdout() with SinkOrion()
    sink = SinkStdout()
    agent = NgsiAgent.create_agent(src, sink, process=build_entity)
    agent.run()
    agent.close()


if __name__ == '__main__':
    main()