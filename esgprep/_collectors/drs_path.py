# -*- coding: utf-8 -*-

"""
.. module:: esgprep._collectors.drs_path.py
   :platform: Unix
   :synopsis: DRS path collector.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import os

from esgprep._collectors import Collector
from esgprep._exceptions import NoFileFound
from esgprep._utils.path import (
    get_drs,
    get_project,
    get_version_index,
    get_versions,
    is_latest_symlink,
    with_latest_target,
)
from esgprep._utils.print import Print
from pathlib import Path


class DRSPathCollector(Collector):
    """
    Collector class to yield files from a structured and versioned tree, aka DRS.

    """

    def __init__(self, *args, **kwargs):
        super(DRSPathCollector, self).__init__(*args, **kwargs)

        # Initialize default behavior to False.
        self.default = False

        # Initialize dataset path switch.
        self.dataset_parent = False

    def __iter__(self):
        # StopIteration error means no files found in all input sources.
        try:
            Print.debug(
                f"DRSPathCollector: Starting iteration over sources: {self.sources}"
            )

            # Iterate on input sources.
            for source in self.sources:
                Print.debug(f"DRSPathCollector: Processing source: {source}")
                # Walk through each source.
                for root, dirs, filenames in os.walk(str(source), followlinks=True):
                    Print.debug(
                        f"DRSPathCollector: Walking root={root}, dirs={dirs}, filenames={filenames}"
                    )
                    # Instantiate path object.
                    path = Path(root)

                    # Get project from path.
                    project = get_project(path)
                    Print.debug(f"DRSPathCollector: path={path}, project={project}")
                    # Get version index using the smart algorithm from path utils.
                    try:
                        idx = get_version_index(path)
                        Print.debug(f"DRSPathCollector: version_index={idx}")
                    except ValueError as e:
                        # If no version found in path, skip this path
                        Print.debug(
                            f"DRSPathCollector: No version found in path {path}: {e}, skipping"
                        )
                        continue

                    # When DRS version depth/level is reached, it takes priority.
                    if len(get_drs(path).parts) == idx:  # on en est à la version
                        # Apply default behavior.
                        if self.default:
                            #  Pick up the latest existing versions for the corresponding dataset.
                            # We need to get versions from the parent directory (dataset level), not the current version directory
                            dataset_path = path.parent
                            versions = get_versions(dataset_path)
                            Print.debug(
                                f"DRSPathCollector: get_versions({dataset_path}) returned: {versions}"
                            )
                            if versions:
                                latest_version = versions[-1]
                                Print.debug(
                                    f"DRSPathCollector: latest_version={latest_version}, latest_version.name={latest_version.name}"
                                )
                                # Add version filter with latest version.
                                self.PathFilter.add(
                                    name="version_filter",
                                    regex="/{}".format(latest_version.name),
                                )
                            else:
                                Print.debug(
                                    f"DRSPathCollector: No versions found for dataset path {dataset_path}"
                                )

                        # Remove undesired subdirectories to prune os.walk.
                        original_dirs = dirs.copy()
                        dirs[:] = [d for d in dirs if self.PathFilter("/{}".format(d))]
                        Print.debug(
                            f"DRSPathCollector: PathFilter applied - original_dirs={original_dirs}, filtered_dirs={dirs}"
                        )

                        if self.dataset_parent and self.PathFilter(root):
                            Print.debug(
                                f"DRSPathCollector: dataset_parent mode, processing root={root}"
                            )

                            # Iterate of sub-directories.
                            for dir in dirs:
                                # Yield the version directory.
                                yield Path(root, dir)

                    elif len(get_drs(path).parts) > idx and self.dataset_parent:
                        # yield the version directory
                        yield dataset_path(path)  # Lolo change to Path(...) or not

                    # Iterate on discovered sorted filenames.
                    Print.debug(
                        f"DRSPathCollector: Processing {len(filenames)} filenames: {filenames}"
                    )
                    for filename in sorted(filenames):
                        # Ensure that root path satisfies PathFilter.
                        path_filter_result = self.PathFilter(root)
                        Print.debug(
                            f"DRSPathCollector: PathFilter({root}) = {path_filter_result}"
                        )
                        if path_filter_result:
                            # Instantiate DRSPath object.
                            path = Path(root, filename)
                            Print.debug(
                                f"DRSPathCollector: Processing file path: {path}"
                            )

                            # Dereference "latest" symlink version.
                            if is_latest_symlink(path):
                                original_path = path
                                path = with_latest_target(path)
                                Print.debug(
                                    f"DRSPathCollector: Dereferenced latest symlink {original_path} -> {path}"
                                )

                            # Apply file filters on filename.
                            is_file = path.is_file()
                            file_filter_result = self.FileFilter(path.name)
                            Print.debug(
                                f"DRSPathCollector: is_file={is_file}, FileFilter({path.name})={file_filter_result}"
                            )
                            if is_file and file_filter_result:
                                # Yield DRSPath object.
                                Print.debug(f"DRSPathCollector: YIELDING file: {path}")
                                yield path
                            else:
                                Print.debug(
                                    f"DRSPathCollector: SKIPPING file: {path} (is_file={is_file}, file_filter={file_filter_result})"
                                )

        except StopIteration:
            raise NoFileFound(self.sources)
