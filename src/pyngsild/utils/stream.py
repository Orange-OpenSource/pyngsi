#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import logging

from typing import Any
from zipfile import ZipFile
from io import StringIO, TextIOWrapper
from pathlib import Path
from tempfile import SpooledTemporaryFile

logger = logging.getLogger(__name__)


def stream_from(
    filename: str, fp: SpooledTemporaryFile = None
) -> tuple[TextIOWrapper, list[str]]:

    # if fp is set then filename is only here for metadata
    # SpooledTemporaryFile used for interoperability with FastAPI
    if isinstance(fp, SpooledTemporaryFile):  # here fp is not None
        fp = fp._file

    logger.debug(f"{filename=} {fp=}")
    try:
        suffixes = [s[1:] for s in Path(filename).suffixes]  # suffixes w/o dot
        ext = suffixes[-1]  # last suffix
        if ext == "gz":
            stream = gzip.open(filename if fp is None else fp, "rt", encoding="utf-8")
            return stream, suffixes[:-1]
        elif ext == "zip":
            zf = ZipFile(filename if fp is None else fp, "r")
            f = zf.namelist()[0]
            stream = TextIOWrapper(zf.open(f, "r"), encoding="utf-8")
            return stream, suffixes
        else:
            if fp is None:
                return open(filename, "rt", encoding="utf-8"), suffixes
            else:
                return TextIOWrapper(fp, encoding="utf-8"), suffixes
    except Exception as e:
        logger.error(f"Cannot open file {filename} : {e}")
