#!/usr/bin/env python3

# v2.1.9 introduces SourceApi to facilitate the creation of an agent that retrieves its data from an API
# No need anymore to inherit from the Source class

import requests
from functools import partial

from pyngsi.agent import NgsiAgent
from pyngsi.sources.source import Row
from pyngsi.sources.more_sources import SourceApi
from pyngsi.sink import SinkStdout
from pyngsi.ngsi import DataModel


def request_api(ncommits: int = 5):
    url = "https://api.github.com/repos/numpy/numpy/commits"
    headers = {'Application': 'application/vnd.github.v3+json'}
    params = {'per_page': ncommits}
    response = requests.get(
        url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def build_entity(row: Row) -> DataModel:
    sha = row.record['sha']
    commit = row.record['commit']
    author = commit['author']
    m = DataModel(id=f"{sha}-GitCommit-Numpy-{row.provider}", type="GitCommit")
    m.add("author", author['name'])
    m.add("dateObserved", author['date'], isdate=True)
    m.add("message", commit['message'], urlencode=True)
    return m


def main():
    src = SourceApi(request_api, "github")
    # default is to retrieve 5 commits
    # in case you want to retrieve 3 commits, you could use either partial or lambda
    # src = SourceApi(partial(request_api, 3), "github")
    # src = SourceApi(lambda: request_api(3), "github")

    # if you have an Orion server available, just replace SinkStdout() with SinkOrion()
    sink = SinkStdout()
    agent = NgsiAgent.create_agent(src, sink, process=build_entity)
    agent.run()
    agent.close()


if __name__ == '__main__':
    main()
