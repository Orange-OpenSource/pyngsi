#!/usr/bin/env python3

# Software Name: python-orion-client
# SPDX-FileCopyrightText: Copyright (c) 2021 Orange
# SPDX-License-Identifier: Apache 2.0
#
# This software is distributed under the Apache 2.0;
# see the NOTICE file for more details.
#
# Author: Fabien BATTELLO <fabien.battello@orange.com> et al.
# SPDX-License-Identifier: Apache-2.0

from concurrent.futures import ThreadPoolExecutor
from orionldclient.api.client import Client
from orionldclient.api.constants import NGSILD_DEFAULT_PORT
from orionldclient.model.entity import Entity
from . import Sink, SinkException


class SinkNgsi(Sink):
    def __init__(self, hostname: str = "localhost", port: int = NGSILD_DEFAULT_PORT):
        try:
            self.client = Client(hostname, port)
        except Exception as e:
            raise SinkException(e)

    def write(self, entity: Entity):
        try:
            self.client.upsert(entity)
        except Exception as e:
            raise SinkException(e)

    def close(self):
        self.client.close()


class SinkNgsiAsync(Sink):
    def __init__(self, hostname: str = "localhost", port: int = NGSILD_DEFAULT_PORT):
        try:
            self.client = Client(hostname, port)
            self.executor = ThreadPoolExecutor()
        except Exception as e:
            raise SinkException(e)

    def write(self, entity: Entity):
        self.executor.submit(self.client.upsert, entity)

    def close(self):
        self.client.close()
