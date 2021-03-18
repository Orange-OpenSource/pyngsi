#!/usr/bin/env python3

# v2.1.9 introduces SourceApi to facilitate the creation of an agent that retrieves its data from an API
# No need anymore to inherit from the Source class
# Suitable for all APIs


import requests
from typing import List

from pyngsi.agent import NgsiAgent
from pyngsi.sources.source import Row
from pyngsi.sources.more_sources import SourceApi
from pyngsi.sink import SinkStdout
from pyngsi.ngsi import DataModel

GH_URL = "https://api.github.com"
GH_ENDPOINT = "/repos"


def retrieve_latest_commits(user: str = "numpy", repo: str = "numpy", ncommits: int = 5) -> List:
    url = f"{GH_URL}{GH_ENDPOINT}/{user}/{repo}/commits"
    headers = {'Application': 'application/vnd.github.v3+json'}
    params = {'per_page': ncommits}
    response = requests.get(
        url, headers=headers, params=params)
    response.raise_for_status()
    # returns the Python object parsed from the JSON string result (here an array)
    # it's ok here because the API returns a JSON array
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

    # just provide SourceApi with your own function (that returns an array)

    # default is to retrieve 5 commits
    # override the default provider "api" with "github"
    src = SourceApi(retrieve_latest_commits, "github")

    # in case you want to retrieve 3 commits, you could use lambda
    # src = SourceApi(lambda: retrieve_latest_commits(ncommits=3), "github")

    # one could prefer to use the partial function from functools
    # src = SourceApi(partial(retrieve_latest_commits, ncommits=3), "github")

    # if you have an Orion server available, just replace SinkStdout() with SinkOrion()
    sink = SinkStdout()
    agent = NgsiAgent.create_agent(src, sink, process=build_entity)
    agent.run()
    agent.close()


if __name__ == '__main__':
    main()
