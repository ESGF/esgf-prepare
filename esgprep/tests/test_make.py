import re
from argparse import Namespace
from pathlib import Path

from esgprep.esgdrs import run
from esgprep.tests.post_test_folder import Post_Test_Folder
from esgprep.tests.test_utils import clean_directory


def make_input_files():
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


def get_default_arg() -> Namespace:
    arg = Namespace(
        cmd="make",
        log=None,
        debug=False,
        action="upgrade",
        directory=[""],
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


def test_diff_variable():
    # test basic structure from a model simulation output with multiple variable, one in each file
    dir_source = Path("tests/test_data/incoming/incoming1")
    root_path_drs = Path("tests/test_data/root")
    clean_directory(root_path_drs)

    arg = get_default_arg()
    arg.directory = [dir_source]
    arg.root = root_path_drs
    run(arg)
    Post_Test_Folder(
        Path(
            "tests/test_data/root/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/day/hur/gn"
        )
    ).test()


def test_new_version_diff_file():
    # test to add a new version for a specific var "tas" with multiple new file
    dir_source = Path("tests/test_data/incoming/incoming2")
    root_path_drs = Path("tests/test_data/root")
    arg = get_default_arg()
    arg.directory = [dir_source]
    arg.root = root_path_drs
    arg.version = "v19810102"

    run(arg)
    Post_Test_Folder(
        Path(
            "tests/test_data/root/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/day/tas/gn"
        )
    ).test()


def test_diff_member_id():
    # test to add a new version with more member_id
    dir_source = Path("tests/test_data/incoming/incoming3")
    root_path_drs = Path("tests/test_data/root")
    arg = get_default_arg()
    arg.directory = [dir_source]
    arg.root = root_path_drs
    arg.version = "v19810102"

    run(arg)
    Post_Test_Folder(
        Path(
            "tests/test_data/root/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r2i1p1f1/day/tas/gn"
        )
    ).test()


def test_diff_source():
    # test to add a new version with more model
    dir_source = Path("tests/test_data/incoming/incoming5")
    root_path_drs = Path("tests/test_data/root")
    arg = get_default_arg()
    arg.directory = [dir_source]
    arg.root = root_path_drs
    arg.version = "v19810103"

    run(arg)
    # doesnt really make sense scientificly cause the institute never run this model but whatever we only test the output structure
    Post_Test_Folder(
        Path(
            "tests/test_data/root/CMIP6/CMIP/IPSL/NESM3/historical/r1i1p1f1/day/tas/gn"
        )
    ).test()
