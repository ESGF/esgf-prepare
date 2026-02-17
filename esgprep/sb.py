# -*- coding: utf-8 -*-

"""
Development sandbox script for esgprep.
This file contains utility functions for testing and development purposes.
"""

import re
from argparse import Namespace
from pathlib import Path

from esgprep.esgdrs import run


def go(dir_source, root_path_drs):
    """
    Run esgdrs make command with default test arguments.

    Args:
        dir_source: Source directory containing NetCDF files
        root_path_drs: Root path for DRS structure
    """
    arg = Namespace(
        cmd="make",
        log=None,
        debug=False,
        action="list",
        directory=[dir_source],
        project="cmip6",
        ignore_dir=re.compile("^.*/(files|\\.[\\w]*).*$"),
        include_file=["^.*\\.nc$"],
        exclude_file=["^\\..*$"],
        color=True,
        no_color=False,
        max_processes=1,
        root=root_path_drs,
        version="v19810101",
        set_value=None,
        set_key=None,
        rescan=True,
        commands_file=None,
        overwrite_commands_file=False,
        upgrade_from_latest=False,
        ignore_from_latest=None,
        ignore_from_incoming=None,
        copy=False,
        link=False,
        symlink=True,
        no_checksum=False,
        checksums_from=None,
        quiet=False,
        prog="esgdrs",
    )

    run(arg)


def go2():
    """
    Create test NetCDF files for testing various scenarios.

    This function generates test data for:
    - Different members
    - Different models
    - Different time periods
    - Different variables
    - Different versions
    """
    from tests.test_utils import (
        create_files_different_members,
        create_files_different_models,
        create_files_different_times,
        create_files_different_variables,
        create_files_different_versions,
    )

    base_dir = Path("tests/test_data/incoming")
    create_files_different_variables(base_dir / "incoming1")
    create_files_different_times(base_dir / "incoming2")
    create_files_different_members(base_dir / "incoming3")
    create_files_different_versions(base_dir / "incoming4")
    create_files_different_models(base_dir / "incoming5")


if __name__ == "__main__":
    go2()
    input_dir = Path("tests/test_data/incoming")
    output_root = Path("tests/test_data/root")
    go(input_dir, output_root)


__all__ = ["go", "go2"]
