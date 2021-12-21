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

import anyio
import time
import schedule
import _thread
import logging

from datetime import datetime
from typing import Callable
from dataclasses import dataclass
from enum import Enum

from .daemon import ManagedDaemon
from .agent import Agent

logger = logging.getLogger(__name__)

# TODO : run the whole thing backgroung using a thread !!

class UNIT(Enum):
    seconds = "s"
    minutes = "m"
    hours = "h"
    days = "d"


class Scheduler(ManagedDaemon):
    """Poll takes an agent and polls at periodic intervals.
    """

    def __init__(self, agent: Agent, func: Callable = None, interval: int = 1, unit: UNIT = UNIT.minutes):
        # take an already created agent and reschedule it
        # 1 - a func may be provided to create a new Source
        # 2 - or the source may have a reset() method        
        # 3 - or the Source __init__() is called to reinit the Source
        super().__init__(agent.sink, agent.process)
        self.src = agent.src
        self.func = func
        self.interval = interval
        self.unit = unit

    async def _ajob(self):
        logger.info(f"start new job at {datetime.now()}")
        self.status.lastcalltime = datetime.now()
        self.status.calls += 1

        # "reinit" the Source
        if self.func is not None:
            self.src = self.func() # get a new Source if such a method has been provided
        else:
            src = self.src                
            if hasattr(src, "reset"):
                src.reset()
            else:
                src.__init__()

        await self.trigger(src)    

    def job(self):
        anyio.run(self._ajob)

    def run(self):
        super().run()
        self.job()
        logger.info("schedule job")
        if self.unit == UNIT.seconds:
            schedule.every(self.interval).seconds.do(self.job)
            tick = 1
        elif self.unit == UNIT.minutes:
            schedule.every(self.interval).minutes.do(self.job)
            tick = 4
        elif self.unit == UNIT.hours:
            schedule.every(self.interval).hours.do(self.job)
            tick = 32
        elif self.unit == UNIT.days:
            schedule.every(self.interval).days.do(self.job)
            tick = 128

        while True:
            logger.debug("tick")
            schedule.run_pending()
            time.sleep(tick)
