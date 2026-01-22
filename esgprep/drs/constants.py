# -*- coding: utf-8 -*-

"""
:platform: Unix
:synopsis: Constants used in this module.

"""

import tempfile
from os import link, symlink, environ, remove
from shutil import copy2 as copy
from shutil import move
from pathlib import Path

# Spinner description.
SPINNER_DESC = "DRS tree generation"

# Command-line parameter to ignore
CONTROLLED_ARGS = [
    "directory",
    "set_values",
    "set_keys",
    "mode",
    "version",
    "root",
    "no_checksum",
    "checksums_from",
    "upgrade_from_latest",
    "ignore_from_latest",
    "ignore_from_incoming",
]

# Tree context file
TREE_FILE = str(Path(tempfile.gettempdir()) / f"DRSTree_{environ['USER']}.pkl")

# PID prefixes
PID_PREFIXES = {
    "cmip6": "hdl:21.14100",
    "cordex": "hdl:21.14103",
    "obs4mips": "hdl:21.14102",
}
