# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Generates ESGF mapfiles upon a local ESGF node or not.

"""

import traceback, re, os
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
        self.cfg = ctx.cfg
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
        # Escape in case of error.
        try:

            # Import utilities depending on the source type.
            if isinstance(source, Path):
                from esgprep._utils.path import get_terms, dataset_id, get_project
            else:
                from esgprep._utils.dataset import get_terms, dataset_id, get_project

            # Build dataset identifier.
            # DRS terms are validated during this step.
            identifier = dataset_id(source)

            # Check dataset identifier is not None.
            if not identifier:
                Print.debug('Dataset identifier is None')
                return False

            # Split identifier into name & version.
            # Identifier does not always end by a version.
            dataset = identifier
            version = None

            if re.search(r'\.latest|\.v[0-9]*$', str(identifier)):
                version = identifier.split('.')[-1][1:]  # remove "v" only for name in mapfile NOT for the mapfile name
                dataset = '.'.join(identifier.split('.')[:-1])

            # Build mapfile name.
            outfile = build_mapfile_name(self.mapfile_name, dataset, version)

            # Build mapfile directory.
            outdir = Path(self.outdir).resolve(strict=False)
            try:
                outdir = outdir.joinpath(self.cfg.get(section='config:{}'.format(get_project(source)),
                                                      option='mapfile_drs',
                                                      vars=get_terms(source)))

            except:
                pass

            # Build full mapfile path.
            outpath = outdir.joinpath(outfile)

            # Create mapfile directory.
            try:
                os.makedirs(outdir)
            except OSError:
                pass

            # Gathers optional mapfile info into a dictionary.
            optional_attrs = dict()
            optional_attrs['mod_time'] = source.stat().st_mtime
            if not self.no_checksum:
                optional_attrs['checksum'] = get_checksum(str(source), self.checksum_type, self.checksums_from)
                optional_attrs['checksum_type'] = self.checksum_type.upper()
            optional_attrs['dataset_tech_notes'] = self.notes_url
            optional_attrs['dataset_tech_notes_title'] = self.notes_title

            # Generate the corresponding mapfile entry/line.
            line = build_mapfile_entry(dataset_name=dataset,
                                       dataset_version=version,
                                       ffp=str(source),
                                       size=source.stat().st_size,
                                       optional_attrs=optional_attrs)

            # Write line into mapfile.
            write(outpath, line)

            # Print success.
            msg = '{} <-- {}'.format(outfile.with_suffix(''), source)
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
                msg = TAGS.SKIP + COLORS.HEADER(str(source)) + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)

            return None

        finally:

            # Lock progress value.
            with self.lock:

                # Increase progress counter.
                self.progress.value += 1

                # Clear previous print.
                msg = '\r{}'.format(' ' * self.msg_length.value)
                Print.progress(msg)

                # Print progress bar.
                msg = '\r{} {} {}'.format(COLORS.OKBLUE(SPINNER_DESC),
                                          FRAMES[self.progress.value % len(FRAMES)],
                                          source)
                Print.progress(msg)

                # Set new message length.
                self.msg_length.value = len(msg)
