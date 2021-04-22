#!/usr/bin/env python3

import yaml
import re
import os


# pattern for global vars: look for ${word}
_pattern = re.compile('.*?\${(\w+)}.*?')
_loader = yaml.SafeLoader


def _constructor_env_variables(loader, node):
    value = loader.construct_scalar(node)
    match = _pattern.findall(value)  # to find all env variables in line
    if match:
        full_value = value
        for g in match:
            full_value = full_value.replace(
                f"${{{g}}}", os.environ.get(g, g)
            )
        return full_value
    return value


_loader.add_implicit_resolver("!ENV", _pattern, None)
_loader.add_constructor("!ENV", _constructor_env_variables)


def load(config):
    return yaml.load(config, Loader=_loader)
