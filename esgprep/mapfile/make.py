# -*- coding: utf-8 -*-

"""
:platform: Unix
:synopsis: Generates ESGF mapfiles upon a local ESGF node or not.

"""

import traceback
import re
import os
from pathlib import Path

from esgprep._utils.checksum import get_checksum
from esgprep.constants import FRAMES
from esgprep.mapfile import build_mapfile_name, build_mapfile_entry, write
from esgprep.mapfile.constants import SPINNER_DESC
from esgprep._utils.print import Print, COLORS, TAGS


class Process(object):
    """
    Child process.

    """

    def __init__(self, ctx):
        """
        Shared processing context between child processes.

        """
        self.mapfile_name = ctx.mapfile_name
        self.outdir = ctx.outdir
        #        self.cfg = ctx.cfg
        self.basename = ctx.basename
        self.no_checksum = ctx.no_checksum
        self.checksums_from = ctx.checksums_from
        self.checksum_type = ctx.checksum_type
        self.notes_url = ctx.notes_url
        self.notes_title = ctx.notes_title
        self.progress = ctx.progress
        self.msg_length = ctx.msg_length
        self.lock = ctx.lock
        self.errors = ctx.errors

    def __call__(self, source):
        """
        Any error switches to the next child process.
        It does not stop the main process at all.

        """
        Print.debug(
            f"Process.__call__: Processing source: {source} (type: {type(source)})"
        )
        # Escape in case of error.
        try:
            # Import utilities depending on the source type.
            if isinstance(source, Path):
                from esgprep._utils.path import dataset_id

                Print.debug(
                    f"Process.__call__: Using path utilities for source: {source}"
                )
            else:
                from esgprep._utils.dataset import dataset_id

                Print.debug(
                    f"Process.__call__: Using dataset utilities for source: {source}"
                )

            # Build dataset identifier.
            # DRS terms are validated during this step.
            Print.debug(f"Process.__call__: Building dataset identifier for: {source}")
            identifier = dataset_id(source)
            Print.debug(f"Process.__call__: Dataset identifier: {identifier}")

            # Check dataset identifier is not None.
            if not identifier:
                Print.debug(
                    f"Process.__call__: Dataset identifier is None for source: {source}"
                )
                return False

            # Split identifier into name & version.
            # For DRS structure, version is in the path, not the identifier.
            dataset = identifier
            version = None

            # First check if version is in the identifier (legacy support)
            if re.search(r"\.latest|\.v[0-9]*$", str(identifier)):
                version = identifier.split(".")[-1][
                    1:
                ]  # remove "v" only for name in mapfile NOT for the mapfile name
                dataset = ".".join(identifier.split(".")[:-1])
            else:
                # Extract version from file path (DRS structure)
                for part in source.parts:
                    if part.startswith("v") and part[1:].isdigit():
                        version = part[1:]  # remove "v" prefix
                        break
                    elif part == "latest":
                        version = "latest"
                        break

            # Build mapfile name.
            outfile = build_mapfile_name(self.mapfile_name, dataset, version)

            # Build mapfile directory.
            outdir = Path(self.outdir).resolve(strict=False)
            # try:
            #     outdir = outdir.joinpath(self.cfg.get(section='config:{}'.format(get_project(source)),
            #                                           option='mapfile_drs',
            #                                           vars=get_terms(source)))
            #
            # except:
            #     pass

            # Build full mapfile path.
            outpath = outdir.joinpath(outfile)

            # Create mapfile directory.
            try:
                os.makedirs(outdir, exist_ok=True)
            except OSError as e:
                Print.warning(f"Failed to create mapfile directory {outdir}: {e}")

            # Gathers optional mapfile info into a dictionary.
            optional_attrs = dict()
            optional_attrs["mod_time"] = source.stat().st_mtime
            if not self.no_checksum:
                optional_attrs["checksum"] = get_checksum(
                    str(source), self.checksum_type, self.checksums_from
                )
            optional_attrs["dataset_tech_notes"] = self.notes_url
            optional_attrs["dataset_tech_notes_title"] = self.notes_title

            # Generate the corresponding mapfile entry/line.
            line = build_mapfile_entry(
                dataset_name=dataset,
                dataset_version=version,
                ffp=str(source),
                size=source.stat().st_size,
                optional_attrs=optional_attrs,
            )

            # Write line into mapfile.
            write(outpath, line)

            # Print success.
            msg = "{} <-- {}".format(outfile.with_suffix(""), source)
            with self.lock:
                Print.success(msg)

            # Return mapfile path.
            return outpath

        except KeyboardInterrupt:
            # Lock error number.
            with self.lock:
                # Increase error counter.
                self.errors.value += 1

            raise

        # Catch known exception with its traceback.
        except Exception:
            # Lock error number.
            with self.lock:
                # Increase error counter.
                self.errors.value += 1

                # Format & print exception traceback.
                exc = traceback.format_exc().splitlines()
                msg = TAGS.SKIP + COLORS.HEADER(str(source)) + "\n"
                msg += "\n".join(exc)
                Print.exception(msg, buffer=True)

            return None

        finally:
            # Lock progress value.
            with self.lock:
                # Increase progress counter.
                self.progress.value += 1

                # Clear previous print.
                msg = "\r{}".format(" " * self.msg_length.value)
                Print.progress(msg)

                # Print progress bar.
                msg = "\r{} {} {}".format(
                    COLORS.OKBLUE(SPINNER_DESC),
                    FRAMES[self.progress.value % len(FRAMES)],
                    source,
                )
                Print.progress(msg)

                # Set new message length.
                self.msg_length.value = len(msg)
