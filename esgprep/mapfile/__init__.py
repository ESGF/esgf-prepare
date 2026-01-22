# -*- coding: utf-8 -*-

"""
.. module:: esgprep.mapfile
    :platform: Unix
    :synopsis: Manages mapfiles.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from pathlib import Path
import re
import sys

from esgprep import _STDOUT
from esgprep._contexts.multiprocessing import Runner
from esgprep._utils.print import Print, COLORS, TAGS
from esgprep.constants import FINAL_FRAME, FINAL_STATUS
from esgprep.mapfile.constants import WORKING_EXTENSION, MAPFILE_EXTENSION, SPINNER_DESC
from esgprep.mapfile.context import ProcessingContext
from lockfile import LockFile


def build_mapfile_name(name, dataset, version):
    """
    Injects token values and returns mapfile name.

    """
    # Inject dataset name.
    if re.compile(r"{dataset_id}").search(name):
        name = re.sub(r"{dataset_id}", dataset, name)

    # Inject dataset version.
    if re.compile(r"{version}").search(name):
        if version:
            name = re.sub(r"{version}", version, name)
        else:
            name = re.sub(r"\.{version}", "", name)

    # Inject date.
    if re.compile(r"{date}").search(name):
        name = re.sub(r"{date}", datetime.now().strftime("%Y%d%m"), name)

    # Inject job id.
    if re.compile(r"{job_id}").search(name):
        name = re.sub(r"{job_id}", str(os.getpid()), name)

    # Return path object with working extension.
    return Path(name).with_suffix(WORKING_EXTENSION)


def build_mapfile_entry(dataset_name, dataset_version, ffp, size, optional_attrs):
    """
    Generate mapfile line corresponding to the source.

    """
    line = [dataset_name]
    if dataset_version:
        line = ["{}.v{}".format(dataset_name, dataset_version)]
    line.append(ffp)
    line.append(str(size))
    for k, v in optional_attrs.items():
        if v:
            line.append("{}={}".format(k, v))
    return " | ".join(line) + "\n"


def write(outpath, line):
    """
    Append line to a mapfile.
    It generates a lockfile to avoid that several threads write on the same file at the same time.
    A LockFile is acquired and released after writing. Acquiring LockFile is timeouted if it's locked by other thread.
    Each process adds one line to the appropriate mapfile.

    """
    lock = LockFile(outpath)
    with lock:
        with outpath.open("a+") as mapfile:
            mapfile.write(line)


def run(args):
    """
    Main process.

    """
    # Deal with 'quiet' option separately.
    # Turn off all output before creating ProcessingContext.
    # Turn it on only when needed.
    quiet = args.quiet if hasattr(args, "quiet") else False
    if quiet:
        _STDOUT.stdout_off()

    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        # Instantiate the runner.
        r = Runner(ctx.processes)

        # Get results.
        results = r.run(ctx.sources, ctx)

        # Final print.
        msg = "\r{}".format(" " * ctx.msg_length.value)
        Print.progress(msg)
        msg = "\r{} {} {}\n".format(
            COLORS.OKBLUE(SPINNER_DESC), FINAL_FRAME, FINAL_STATUS
        )
        Print.progress(msg)

        # Flush buffer.
        Print.flush()

        # Get number of sources (without "Completed" step).
        ctx.nbsources = ctx.progress.value

        # Number of success (excluding errors/skipped files).
        ctx.success = len(list(filter(None, results)))

        # Number of generated mapfiles.
        ctx.nbmap = len(list(filter(None, set(results))))

        # Evaluate the list of results triggering action.
        if any(results):
            # Iterate over written mapfiles.
            for mapfile in filter(None, set(results)):
                # Set mapfile final extension.
                result = mapfile.with_suffix(MAPFILE_EXTENSION)

                # Print mapfiles to be generated.
                if ctx.cmd == "show":
                    # Disable quiet mode to print results.
                    if quiet:
                        _STDOUT.stdout_on()
                        print(str(result))
                        _STDOUT.stdout_off()
                    else:
                        Print.result(str(result))

                # Do mapfile renaming.
                elif ctx.cmd == "make":
                    # Count number of expected lines.
                    expected_lines = results.count(mapfile)

                    # Count number of lines in written mapfile.
                    with open(mapfile) as f:
                        lines = len(f.readlines())

                    # Sanity check that the mapfile has the appropriate lines number.
                    assert lines == expected_lines, (
                        "Wrong lines number : {}, {} expected - {}".format(
                            lines, expected_lines, mapfile
                        )
                    )

                    # A final mapfile is silently overwritten if already exists
                    mapfile.rename(result)

    # Evaluate errors & exit with corresponding return code.
    if ctx.final_error_count > 0:
        sys.exit(ctx.final_error_count)


__all__ = ["make", "show"]
