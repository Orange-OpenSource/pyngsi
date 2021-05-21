#!/usr/bin/env python3

from collections import UserDict
from loguru import logger

from pyngsi.utils import eyaml

DEFAULT_CONFIG_FILE = "config.yml"
DEFAULT_ORION_CONFIG = { "host": "localhost", "port": 1026 }
KEY_ORION = "orion"

class ConfigError(Exception):
    pass


class Config(UserDict):

    @classmethod
    def load_from_yaml(cls, path: str = DEFAULT_CONFIG_FILE):
        logger.debug(f"Load config from yaml file {path}")
        config = {}
        try:
            with open(path) as file:
                config = eyaml.load(file)
        except Exception as e:
            raise ConfigError(
                f"Cannot read config from file {path}") from e
        logger.debug(f"{config=}")
        return cls(config)

    @property
    def orion(self):
        return self.data.get(KEY_ORION, DEFAULT_ORION_CONFIG)