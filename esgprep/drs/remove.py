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
from pathlib import Path
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
            # print("SOURCE : ",source)
            # Convert dataset identifier into directory_structure.
            if isinstance(source, Dataset):
                current_path = directory_structure(source)
            else:
                current_path = source

            # Validate directory structure.
            assert get_terms(source), 'Invalid path {}'.format(source)

            root = get_root(current_path)
            assert root, 'Invalid root path {}'.format(source)
            version = get_version(current_path)
            assert version, 'Invalid path version {}'.format(source)

            # Get all existing version.
            versions = get_versions(current_path)

            # Keep only the current, latest and next versions of the file.
            if not current_path in versions :
                return False
            current_idx = versions.index(current_path) # crashes here if current_path is a file cause the are only folder in versions
            versions = versions[(current_idx - 1 if current_idx - 1 >= 0 else 0): current_idx + 2]

            # Get latest version.
            latest_version = 'Initial'
            if versions:
                latest_version = get_version(versions[-1])

            # Iterate over files in the version directory to remove.
            for root, _, files in os.walk(current_path):
                for file in files:

                    # Convert file into pathlib.Path()
                    file = Path(root, file)

                    # Check file is a symlink.
                    if file.is_symlink():

                        # Check if targets of previous and next versions exists and are the same.
                        if any(v == current_path for v in versions) or len(versions) == 1:
                            # Remove the current file from the "files" folder. ORIGINAL
                            # self.tree.create_leaf(nodes=with_file_folder(current_path).parts,
                            #                      label=path.name,
                            #                      mode=self.mode)

                            # Remove the current file from the "files" folder.
                            self.tree.create_leaf(nodes=with_file_folder(file).parts,
                                                  label=file.name,
                                                  src=None,
                                                  mode=self.mode)

                            # self.tree.create_leaf(nodes=with_file_folder(file).parts,
                            #                       # Lolo Change current_path par file
                            #                       label=file.name,  # Lolo Change current_path par file
                            #                       mode=self.mode)
                    # Remove the current file symlink from the "vYYYYMMDD" folder in any case.
                    src = ['..']+['..'] * len(get_drs_down(current_path).parts)
                    src.append('files')
                    src += get_drs_down(with_file_folder(file)).parts
                    self.tree.create_leaf(nodes=file.parts,
                                          label='{}{}{}'.format(file.name, LINK_SEPARATOR, os.path.join(*src)),
                                          src=None,
                                          mode=self.mode,
                                          force=True)

                    # Record entry for list() and uniqueness checkup.


            # Record entry for list() and uniqueness checkup.
            # En regardant make :
            record = {#s'src': source,
                      'dst': current_path,
                      'is_duplicate': False
                      }
            #####
            key = str(get_drs_up(source).parent) # Lolo Change file to source
            if key in self.tree.paths:
                self.tree.append_path(key, "files", record)
                #self.tree.paths[key]['files'].append(record) # Lolo Change file to record
                assert latest_version == self.tree.paths[key]['latest']
                assert version == self.tree.paths[key]['upgrade']
            else:
                infos = {"files": [record], "latest": 'Initial' if len(versions) == 1 else get_version(versions[-1])}
                self.tree.add_path(key, infos)

                # Lolo Change into add_path method to set instance variable (pb for shared DRSTree between process)

                #self.tree.paths[key] = {}
                #self.tree.paths[key]['files'] = [record] # Lolo Change file to record
                #self.tree.paths[key]['latest'] = 'Initial' if len(versions) == 1 else get_version(versions[-1])
                ##self.tree.paths[key]['upgrade'] = version

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
