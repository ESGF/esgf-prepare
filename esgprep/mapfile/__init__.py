"""""
ESGF mapfile generation module.

This module provides utilities to generate ESGF mapfiles required for data publication.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from esgprep import _STDOUT
from esgprep._contexts.multiprocessing import Runner
from esgprep._utils.print import Print, COLORS
from esgprep.constants import FINAL_FRAME, FINAL_STATUS
from esgprep.mapfile.constants import WORKING_EXTENSION, MAPFILE_EXTENSION, SPINNER_DESC
from esgprep.mapfile.context import ProcessingContext
from esgprep.mapfile.models import FileInput, MapfileResult, MapfileEntry, Mapfile
from esgprep.mapfile.processor import MapfileProcessor


def build_mapfile_name(name, dataset, version):
    """
    Build a mapfile name from template.
    
    Args:
        name: Template string
        dataset: Dataset ID
        version: Version string
        
    Returns:
        Path object with the constructed mapfile name
    """
    # Inject dataset name
    if '{dataset_id}' in name:
        name = name.replace('{dataset_id}', dataset)

    # Inject dataset version
    if '{version}' in name:
        if version:
            name = name.replace('{version}', version)
        else:
            name = name.replace('.{version}', '')

    # Inject date
    if '{date}' in name:
        name = name.replace('{date}', datetime.now().strftime("%Y%m%d"))

    # Inject job id
    if '{job_id}' in name:
        name = name.replace('{job_id}', str(os.getpid()))

    # Return path object with working extension
    return Path(name).with_suffix(WORKING_EXTENSION)


def build_mapfile_entry(dataset_name, dataset_version, ffp, size, optional_attrs):
    """
    Generate mapfile line corresponding to the source.
    
    Args:
        dataset_name: Dataset ID
        dataset_version: Dataset version
        ffp: File path
        size: File size
        optional_attrs: Dictionary of optional attributes
        
    Returns:
        Mapfile entry as a string
    """
    # Create a MapfileEntry object
    entry = MapfileEntry(
        dataset_id=dataset_name,
        version=dataset_version,
        path=Path(ffp),
        size=size,
        mod_time=optional_attrs.get('mod_time'),
        checksum=optional_attrs.get('checksum'),
        checksum_type=optional_attrs.get('checksum_type'),
        tech_notes_url=optional_attrs.get('dataset_tech_notes'),
        tech_notes_title=optional_attrs.get('dataset_tech_notes_title')
    )
    
    # Return the entry as a string
    return str(entry) + '\n'


def write(outpath, line):
    """
    Append line to a mapfile with thread safety.
    
    Args:
        outpath: Path to the mapfile
        line: Line to append
    """
    # Create directory if it doesn't exist
    outpath.parent.mkdir(parents=True, exist_ok=True)
    
    # Append line to file
    with open(outpath, 'a+') as mapfile:
        mapfile.write(line)


def run(args):
    """
    Main process for mapfile generation.
    
    Args:
        args: Command-line arguments
    """
    # Deal with 'quiet' option separately
    # Turn off all output before creating ProcessingContext
    # Turn it on only when needed
    quiet = args.quiet if hasattr(args, 'quiet') else False
    if quiet:
        _STDOUT.stdout_off()

    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        # Instantiate the runner
        r = Runner(ctx.processes)

        # Get results
        results = r.run(ctx.sources, ctx)

        # Final print
        msg = f'\r{" " * ctx.msg_length.value}'
        Print.progress(msg)
        msg = f'\r{COLORS.OKBLUE(SPINNER_DESC)} {FINAL_FRAME} {FINAL_STATUS}\n'
        Print.progress(msg)

        # Flush buffer
        Print.flush()

        # Get number of sources (without "Completed" step)
        ctx.nbsources = ctx.progress.value

        # Number of success (excluding errors/skipped files)
        ctx.success = len(list(filter(None, results)))

        # Number of generated mapfiles
        ctx.nbmap = len(list(filter(None, set(results))))

        # Evaluate the list of results triggering action
        if any(results):
            # Iterate over written mapfiles
            for mapfile in filter(None, set(results)):
                # Set mapfile final extension
                result = mapfile.with_suffix(MAPFILE_EXTENSION)

                # Print mapfiles to be generated
                if ctx.cmd == 'show':
                    # Disable quiet mode to print results
                    if quiet:
                        _STDOUT.stdout_on()
                        print(str(result))
                        _STDOUT.stdout_off()
                    else:
                        Print.result(str(result))

                # Do mapfile renaming
                elif ctx.cmd == 'make':
                    # Count number of expected lines
                    expected_lines = results.count(mapfile)

                    # Count number of lines in written mapfile
                    with open(mapfile) as f:
                        lines = len(f.readlines())

                    # Sanity check that the mapfile has the appropriate lines number
                    assert lines == expected_lines, f"Wrong lines number: {lines}, {expected_lines} expected - {mapfile}"

                    # A final mapfile is silently overwritten if already exists
                    mapfile.rename(result)

    # Evaluate errors & exit with corresponding return code
    if ctx.errors.value > 0:
        sys.exit(ctx.errors.value)
