# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

"""
import traceback

from esgprep._exceptions import *
from esgprep._utils.checksum import get_checksum
from esgprep._utils.path import *
from esgprep._utils.print import *
from esgprep.constants import FRAMES
from esgprep.drs.constants import *
from esgprep._handlers.constants import LINK_SEPARATOR
from esgprep._handlers.dataset_id import Dataset
from esgprep._utils.dataset import directory_structure
from esgprep._utils.path import get_terms, get_root, get_version


class Process(object):
    """
    Child process.

    """

    def __init__(self, ctx):
        """
        Shared processing context between child processes.

        """
        self.tree = ctx.tree
        self.root = ctx.root
        self.set_values = ctx.set_values
        self.set_keys = ctx.set_keys
        self.lock = ctx.lock
        self.errors = ctx.errors
        self.msg_length = ctx.msg_length
        self.progress = ctx.progress
        self.no_checksum = ctx.no_checksum
        self.checksums_from = ctx.checksums_from
        self.checksum_type = ctx.checksum_type
        self.mode = ctx.mode
        self.upgrade_from_latest = ctx.upgrade_from_latest
        self.ignore_from_latest = ctx.ignore_from_latest
        self.ignore_from_incoming = ctx.ignore_from_incoming

    def __call__(self, source):
        """
        Any error switches to the next child process.
        It does not stop the main process at all.

        """
        # Escape in case of error.
        try:

            # Convert dataset identifier into directory_structure.
            if isinstance(source, Dataset):
                current_path = directory_structure(source)
            else:
                current_path = source

            # Validate directory structure.
            assert get_terms(source), f'Invalid path {source}'

            # Get all existing version.
            versions = get_versions(current_path)
            assert versions, 'No versions found'

            # Get latest version.
            latest_version = get_version(versions[-1])

            # Add the "latest" symlink node.
            nodes = list(current_path.parts[:-1])
            nodes.append('latest')

            self.tree.create_leaf(nodes=nodes,
                                  label='{}{}{}'.format('latest', LINK_SEPARATOR, latest_version),
                                  src=latest_version,
                                  mode='symlink')

            # Print info.
            msg = 'DRS Path = {}'.format(get_drs_up(current_path))
            msg += ' <-- ' + current_path.name
            Print.success(msg)

            # Return True if success.
            return True

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
