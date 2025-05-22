import re
from argparse import Namespace
from pathlib import Path

from esgprep.esgdrs import run


def go(dir_source, root_path_drs):
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


"""

import re
from argparse import Namespace
from pathlib import Path

from esgprep.esgdrs import run
from esgprep.tests.post_test_folder import Post_Test_Folder


def get_default_arg() -> Namespace:
    arg = Namespace(
        cmd="make",
        log=None,
        debug=False,
        action="upgrade",
        directory="",
        project="cmip6",
        ignore_dir=re.compile("^.*/(files|\\.[\\w]*).*$"),
        include_file=["^.*\\.nc$"],
        exclude_file=["^\\..*$"],
        color=False,
        no_color=False,
        max_processes=1,
        root="",
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
    return arg


def test_incoming1():
    dir_source = Path("tests/test_data/incoming/incoming1")
    root_path_drs = Path("tests/test_data/root")

    arg = get_default_arg()
    arg.dir_source = dir_source
    arg.root = root_path_drs
    
    print(arg)
    run(arg)
    Post_Test_Folder(
        Path(
            "tests/test_data/root/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/day/hur/gn"
        )
    ).test()


def test_incoming2():
    pass
"""
