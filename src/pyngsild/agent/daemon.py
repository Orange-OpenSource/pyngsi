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

import asyncio
import anyio
import uvicorn
import logging
import time

from fastapi import FastAPI, File, UploadFile
from typing import Callable
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from anyio import Lock
from uvicorn import server

from pyngsild import __version__
from .agent import BaseAgent, Agent
from ..source.source import Source
from ..sink import Sink, SinkStdout

logger = logging.getLogger(__name__)


class State(Enum):
    PENDING = 0
    RUNNING = 1
    CLOSED = 2
    ERROR = 3


@dataclass
class Status:
    state: State = State.PENDING
    starttime: datetime = None
    lastcalltime: datetime = None
    calls: int = 0
    success: int = 0
    errors: int = 0


class Daemon(BaseAgent):
    def __init__(
        self,
        sink: Sink = SinkStdout(),
        process: Callable = lambda row: row.record, 
    ):
        super().__init__(sink, process)
        self._status = Status()

    async def trigger(
        self, src: Source
    ):  # a Daemon server will have to create a source then call this method
        logger.info(f"{src=}")
        try:
            agent = Agent(src, self.sink, self.process)
            agent.run()
            agent.close()
        except Exception as e:
            logger.error("Error while running agent", e)
            lock = Lock()
            async with lock:
                self._status.errors += 1
            return None
        lock = Lock()
        async with lock:
            self._status.success +=1
            self.stats += agent.stats
        return agent.stats


class HttpAgent(Daemon):
    def __init__(
        self,
        sink: Sink = SinkStdout(),
        process: Callable = lambda row: row.record
    ):
        super().__init__(sink, process)

        self.app = FastAPI()

        endpoint = "/myendpoint"

        @self.app.on_event("startup")
        async def startup_event():
            logger.info("Start FastAPI HTTP server")

        @self.app.on_event("shutdown")
        def shutdown_event():
            logger.info("Shutdown FastAPI HTTP server")
            self.close()

        @self.app.get("/")
        async def root():
            return {"message": "Hello World"}

        @self.app.get("/status")
        async def status():
            return {"status": asdict(self._status), "sink": self.sink.status}

        @self.app.get("/version")
        async def version():
            return {"version": f"pyngsild-{__version__}"}

        @self.app.get(endpoint)
        async def upload():
            return {"upload": "success"}            

        @self.app.post("/files/")
        async def create_file(file: bytes = File(...)):
            logger.info("HERE !!!!")
            return {"file_size": len(file)}
        
        @self.app.post("/uploadfile/", status_code=201)
        async def create_upload_file(file: UploadFile = File(...)):
            logger.info(file.filename)
            lock = Lock()
            async with lock:
                self._status.lastcalltime = datetime.now()
                self._status.calls += 1
            src = Source.from_file(file.filename, fp=file.file)
            await self.trigger(src)
            return {"filename": file.filename}

    def run(self):
        self._status.starttime = datetime.now()
        self._status.state = State.RUNNING
        uvicorn.run(
            self.app, host="localhost", port=8000, log_level="debug", debug="true"
        )

    def close(self):
        self._status.state = State.CLOSED

