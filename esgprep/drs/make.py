# -*- coding: utf-8 -*-

"""
:platform: Unix
:synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

"""

import os
import traceback
from pathlib import Path

from esgvoc.apps.drs.generator import DrsGenerator

from esgprep._exceptions import DuplicatedFile, OlderUpgrade, UnchangedTrackingID
from esgprep._exceptions.netcdf import NoNetCDFAttribute
from esgprep._handlers.constants import LINK_SEPARATOR
from esgprep._utils.checksum import get_checksum
from esgprep._utils.ncfile import drs_path, get_ncattrs, get_tracking_id
from esgprep._utils.path import (
    extract_version,
    get_ordered_version_paths,
    get_path_to_version,
    get_version_and_subpath,
)
from esgprep._utils.print import COLORS, TAGS, Print
from esgprep.constants import FRAMES
from esgprep.drs.constants import SPINNER_DESC


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
        self.version = ctx.version
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
            # Ignore files from incoming
            if source.name in self.ignore_from_incoming:
                msg = TAGS.SKIP + COLORS.HEADER(str(source))
                with self.lock:
                    Print.exception(msg, buffer=True)
                return None

            # Print info.
            msg = f"Scanning {source}"
            Print.debug(msg)

            # Get current netcdf file attributes.
            current_attrs = get_ncattrs(source)

            # Add filename to attributes.
            current_attrs["filename"] = source.name

            # Add dataset-version to attributes.
            current_attrs["version"] = self.version

            # Instantiate file as no duplicate.
            is_duplicate = False

            # Build directory structure.
            # DRS terms are validated during this step.

            try:
                # drspath = drs_path(current_attrs, self.set_values, self.set_keys)
                dg = DrsGenerator("cmip6")
                # print(current_attrs)
                drs_path = dg.generate_directory_from_mapping(
                    {**current_attrs, **{"member_id": current_attrs["variant_label"]}}
                )
                if len(drs_path.errors) != 0:
                    raise Exception
                current_path: Path = (
                    Path(self.root)
                    / Path(drs_path.generated_drs_expression)
                    / source.name
                )
                # example : CMIP6/CMIP/CCCma/CanESM5/historical/r1i1p2f1/Amon/tas/gn/v20190429
            except TypeError:
                Print.debug("Directory structure is None")
                return False

            # Instantiate latest version to "Initial"
            latest_version = "Initial"

            # Get latest existing version of the file.
            all_versions = get_ordered_version_paths(current_path.parent)

            # latest_path = with_latest_version(current_path)
            latest_path = all_versions[-1] if len(all_versions) > 1 else None

            # 1. Check if a latest file version exists (i.e. with the same filename).
            if latest_path and latest_path.exists():
                # 2. Check latest version is older than current version.

                current_version = extract_version(current_path)
                latest_version = extract_version(latest_path)

                if latest_version > current_version:
                    raise OlderUpgrade(current_version, latest_version)

                # Get latest file version attributes.
                latest_attrs = get_ncattrs(str(latest_path))

                # 3. Check tracking IDs are different.
                current_tracking_id = get_tracking_id(current_attrs)
                latest_tracking_id = get_tracking_id(latest_attrs)
                if current_tracking_id == latest_tracking_id:
                    # 4. Check if file sizes are different.
                    if (
                        source.stat().st_size == latest_path.stat().st_size
                        and not self.no_checksum
                    ):
                        # 5. Check if file checksums are different.
                        current_checksum = get_checksum(
                            source, self.checksum_type, self.checksums_from
                        )
                        latest_checksum = get_checksum(
                            latest_path, self.checksum_type, self.checksums_from
                        )

                        if current_checksum == latest_checksum:
                            # Flags file to duplicate.
                            is_duplicate = True
                        # If different checksums, tracking IDs must be different too if exist.
                        elif current_tracking_id and latest_tracking_id:
                            raise UnchangedTrackingID(
                                latest_path,
                                latest_tracking_id,
                                current_path,
                                current_tracking_id,
                            )

                    # If different sizes, tracking IDs must be different too if exist.
                    elif current_tracking_id and latest_tracking_id:
                        raise UnchangedTrackingID(
                            latest_path,
                            latest_tracking_id,
                            current_path,
                            current_tracking_id,
                        )

            # Print info.
            Print.debug("Processing {source}")

            # Start DRS tree generation.
            if not is_duplicate:
                # Add the current file to the "vYYYYMMDD" folder.
                parts_from_version = get_version_and_subpath(current_path)
                src = [".."] * (len(parts_from_version) - 1)
                src.append("files")
                # src += get_version_and_subpath(with_file_folder(current_path))
                # src += parts_from_version
                src.append(
                    current_path.name
                )  # Lolo Test to add filename at the end of the relative path reconstructed

                self.tree.create_leaf(
                    nodes=current_path.parts,
                    label=f"{current_path.name}{LINK_SEPARATOR}{os.path.join(*src)}",
                    src=os.path.join(*src),
                    mode="symlink",
                    force=True,
                )

                # Add the "latest" symlink node.
                # nodes = list(dataset_path(current_path).parent.parts)
                nodes = list(current_path.parts)[
                    : -len(get_version_and_subpath(current_path))
                ]
                nodes.append("latest")
                self.tree.create_leaf(
                    nodes=nodes,
                    label=f"{'latest'}{LINK_SEPARATOR}{self.version}",
                    src=self.version,
                    mode="symlink",
                )

                nodes = list(current_path.parts)[
                    0 : -len(get_version_and_subpath(current_path))
                ]

                nodes.append("files")
                nodes.append(current_path.name)
                # Add the current file to the "files" folder.
                self.tree.create_leaf(
                    nodes=nodes,
                    label=current_path.name,
                    src=source,  # Lolo Change current_path to source
                    mode=self.mode,
                )

                # If latest file version exist and --upgrade-from-latest submitted.
                if latest_path and latest_path.exists() and self.upgrade_from_latest:
                    # Walk through the latest dataset version.
                    # Create a symlink for each file with a different filename than the current one
                    for root, _, filenames in os.walk(latest_path):
                        for latest_name in filenames:
                            # Add latest files as tree leaves with version to upgrade instead of latest version
                            # i.e., copy latest dataset leaves to the current tree.
                            # Except if file has be ignored from latest version (i.e., with known issue)
                            # Except if file leaf has already been created to avoid overwriting new version
                            # Leaf is not created if already exists (i.e., force = False).
                            if (
                                latest_name != current_path.name
                                and latest_name not in self.ignore_from_latest
                            ):
                                src = os.path.join(root, latest_name)
                                self.tree.create_leaf(
                                    nodes=list(current_path.parent.parts).append(
                                        latest_name
                                    ),
                                    label=f"{latest_name}{LINK_SEPARATOR}{os.readlink(src)}",
                                    src=os.readlink(src),
                                    mode="symlink",
                                )

            # In the case of the file is duplicated.
            # i.e., incoming file already exists in the latest version folder.
            else:
                # If upgrade from latest is activated, raise the error, no duplicated files allowed.
                # Incoming must only contain modifed/corrected files.
                if self.upgrade_from_latest:
                    raise DuplicatedFile(latest_path, source)

                # If default behavior, the incoming contains all data for a new version
                # In the case of a duplicated file, just pass to the expected symlink creation
                # and records duplicated file for further removal only if migration mode is the
                # default (i.e., moving files). In the case of --copy or --link, keep duplicates
                # in place into the incoming directory.
                else:
                    assert latest_path is not None
                    src = os.readlink(latest_path)
                    self.tree.create_leaf(
                        nodes=current_path.parts,
                        label=f"{current_path.name}{LINK_SEPARATOR}{src}",
                        src=src,
                        mode="symlink",
                    )
                    if self.mode == "move":
                        self.tree.duplicates.append(source)

            # Record entry for list() and uniqueness checkup.
            record = {"src": source, "dst": current_path, "is_duplicate": is_duplicate}
            key = str(get_path_to_version(current_path.parent))

            if key in self.tree.paths:
                # mean we already saw this dataset
                un = self.tree.paths[key]["latest"]
                self.tree.append_path(key, "files", record)
                deux = self.tree.paths[key]["latest"]

                # self.tree.paths[key]['files'].append(record)
                un = latest_version
                deux = self.tree.paths[key]["latest"]
                # print("CHECK_4 : ",latest_version, self.tree.paths[key]["latest"] )
                # if latest_version != self.tree.paths[key]['latest']:
                #    print("ERROR : ")
                # print(self.tree)

                # assert latest_version == self.tree.paths[key]['latest']
            else:
                infos = {
                    "files": [record],
                    "latest": latest_version,
                    "upgrade": self.version,
                }
                self.tree.add_path(key, infos)

            # Print info.
            msg = f"DRS Path = {get_path_to_version(current_path)}"
            msg += " <-- " + current_path.name
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
                msg = f"\r{' ' * self.msg_length.value}"
                Print.progress(msg)

                # Print progress bar.
                msg = f"\r{COLORS.OKBLUE(SPINNER_DESC)} {FRAMES[self.progress.value % len(FRAMES)]} {source}"
                Print.progress(msg)

                # Set new message length.
                self.msg_length.value = len(msg)
