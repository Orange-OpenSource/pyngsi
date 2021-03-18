#!/usr/bin/env python3

# This agent takes data from a sample source, builds NGSI entities, eventually writes to a given Sink.
# https://fiware-orion.readthedocs.io/en/2.0.0/user/walkthrough_apiv2/index.html#entity-creation

import json

from pyngsi.agent import NgsiAgent
from pyngsi.sources.source import Row
from pyngsi.sources.source_json import SourceJson
from pyngsi.sink import SinkStdout
from pyngsi.ngsi import DataModel

json_obj = json.loads(r'''[ {"fruit": "Apple", "size": "Large", "color": "Red"},
    {"fruit": "Lime", "size": "Medium", "color": "Yellow"} ]''')


def build_entity(row: Row) -> DataModel:
    fruit = row.record
    m = DataModel(id=f"Fruit-{fruit['fruit']}", type="Fruit")
    m.add("size", fruit['size'])
    m.add("color", fruit['color'])
    return m


def main():
    src = SourceJson(json_obj)

    # in this example data are embedded in the source
    # you can get json data from any file or stream
    # example : Source.from_file("/tmp/test.json")
    # have a look at the factory methods available in the Source class

    # if you have an Orion server available, just replace SinkStdout() with SinkOrion()
    sink = SinkStdout()
    agent = NgsiAgent.create_agent(src, sink, process=build_entity)
    agent.run()
    agent.close()


if __name__ == '__main__':
    main()
