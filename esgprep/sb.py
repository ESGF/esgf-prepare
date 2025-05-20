import re
from argparse import Namespace
from pathlib import Path

from esgprep.esgdrs import run


def go(dir_source, root_path_drs):
    arg = Namespace(
        cmd="make",
        i="/esg/config/esgcet",
        log=None,
        debug=False,
        action="upgrade",
        directory=[dir_source],
        project="cmip6",
        ignore_dir=re.compile("^.*/(files|\\.[\\w]*).*$"),
        include_file=["^.*\\.nc$"],
        exclude_file=["^\\..*$"],
        color=False,
        no_color=False,
        max_processes=1,
        root=root_path_drs,
        version="v19810101",
        set_value=None,
        set_key=None,
        rescan=False,
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


if __name__ == "__main__":
    input_dir = Path("tests/test_data/incoming")
    output_root = Path("tests/test_data/root")
    go(input_dir, output_root)
