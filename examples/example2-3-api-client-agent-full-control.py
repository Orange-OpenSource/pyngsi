#!/usr/bin/env python3

# Source subclass as an alternative to SourceApi
# when you need more control
# when you want a stateful source
# when tou want the ability to stream the incoming data thanks to the Python generator mechanism

import requests

from pyngsi.agent import NgsiAgent
from pyngsi.sources.source import Row, Source
from pyngsi.sink import SinkStdout
from pyngsi.ngsi import DataModel

GH_URL = "https://api.github.com"
GH_ENDPOINT = "/repos"


class SourceGitHubCommits(Source):

    def __init__(self, user: str, repo: str, ncommits: int = 5, provider: str = "github"):
        self.ncommits = ncommits
        self.provider = provider
        self.url = f"{GH_URL}{GH_ENDPOINT}/{user}/{repo}/commits"
        self.headers = {'Application': 'application/vnd.github.v3+json'}
        self.params = {'per_page': ncommits}

    def __iter__(self):
        response = requests.get(
            self.url, headers=self.headers, params=self.params)
        response.raise_for_status()
        for commit in response.json():
            yield Row(self.provider, commit)


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
    src = SourceGitHubCommits("numpy", "numpy")
    # if you have an Orion server available, just replace SinkStdout() with SinkOrion()
    sink = SinkStdout()
    agent = NgsiAgent.create_agent(src, sink, process=build_entity)
    agent.run()
    agent.close()


if __name__ == '__main__':
    main()
