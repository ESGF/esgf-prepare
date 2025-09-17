# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

"""
import re
import traceback
from pathlib import Path

from esgprep._exceptions import *
from esgprep._utils.path import *
from esgprep._utils.print import *
from esgprep.constants import FRAMES
from esgprep.drs.constants import *
from esgprep._handlers.constants import LINK_SEPARATOR
from esgprep._handlers.dataset_id import Dataset


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
            # For dataset objects, skip processing as we can't convert them without pyessv
            if isinstance(source, Dataset):
                Print.debug(f"Skipping dataset object {source} - dataset conversion not supported without pyessv")
                return None

            # Work with path directly
            current_path = source

            # Basic validation - check if path looks like a DRS structure
            if not current_path.exists():
                Print.debug(f"Path does not exist: {current_path}")
                return None

            # If source is a file, we need to find the dataset directory (parent of version directory)
            if current_path.is_file():
                # Navigate up the path to find the dataset directory
                # Expected structure: .../dataset_dir/vYYYYMMDD/filename
                # or: .../dataset_dir/files/dYYYYMMDD/filename
                dataset_path = None
                for parent in current_path.parents:
                    # Look for version directories in this parent
                    version_dirs = []
                    try:
                        for child in parent.iterdir():
                            if child.is_dir() and re.match(r'^v\d{8}$', child.name):
                                version_dirs.append(child)
                    except (OSError, PermissionError):
                        continue

                    if version_dirs:
                        dataset_path = parent
                        break

                if not dataset_path:
                    Print.debug(f"Could not find dataset directory for file: {current_path}")
                    return None

                current_path = dataset_path
                Print.debug(f"Found dataset directory: {current_path}")

            # For latest symlink creation, we need to work at the dataset level
            # Find version directories in the current path
            versions = get_ordered_version_paths(current_path)
            if not versions:
                Print.debug(f"No version directories found in {current_path}")
                return None

            # Get latest version directory name
            latest_version_path = versions[-1]
            latest_version = extract_version(latest_version_path)

            # Create "latest" symlink at the dataset level (parent of version directories)
            dataset_path = latest_version_path.parent
            latest_symlink_path = dataset_path / "latest"

            # Check if latest symlink exists and points to the right version
            if latest_symlink_path.exists():
                if latest_symlink_path.is_symlink():
                    current_target = latest_symlink_path.readlink()
                    if current_target == Path(latest_version):
                        Print.debug(f"Latest symlink already correct: {latest_symlink_path} -> {latest_version}")
                        return True
                else:
                    Print.debug(f"Latest path exists but is not a symlink: {latest_symlink_path}")
                    return None

            # Add the "latest" symlink node to the tree
            nodes = list(latest_symlink_path.parts)
            self.tree.create_leaf(
                nodes=nodes,
                label=f"latest{LINK_SEPARATOR}{latest_version}",
                src=latest_version,
                mode='symlink'
            )

            # Print info.
            msg = f'Latest symlink = {latest_symlink_path} -> {latest_version}'
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
                msg = f"\r{' ' * self.msg_length.value}"
                Print.progress(msg)

                # Print progress bar.
                msg = f"\r{COLORS.OKBLUE(SPINNER_DESC)} {FRAMES[self.progress.value % len(FRAMES)]} {source}"
                Print.progress(msg)

                # Set new message length.
                self.msg_length.value = len(msg)