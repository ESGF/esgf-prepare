#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import fnmatch

from constants import *
from esgprep.utils.collectors import VersionedPathCollector, DatasetCollector
from esgprep.utils.context import MultiprocessingContext
from esgprep.utils.custom_print import *


class ProcessingContext(MultiprocessingContext):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: The command-line arguments parser
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        super(ProcessingContext, self).__init__(args)
        # Specified version
        self.version = None
        if args.version:
            self.version = 'v{}'.format(args.version)
        # Mapfile generation behavior
        self.no_checksum = None
        if hasattr(args, 'no_checksum'):
            self.no_checksum = args.no_checksum

        self.notes_title = None
        if hasattr(args, 'tech_notes_title'):
            self.notes_title = args.tech_notes_title
        self.notes_url = None
        if hasattr(args, 'tech_notes_url'):
            self.notes_url = args.tech_notes_url
        self.checksums_from = None
        if hasattr(args, 'checksums_from'):
            if args.checksums_from:
                self.checksums_from = self.load_checksums(args.checksums_from)
            else:
                self.checksums_from = args.checksums_from
        self.no_version = args.no_version
        self.dataset_name = args.dataset_name
        # Mapfile naming
        self.mapfile_name = args.mapfile
        self.outdir = args.outdir
        if not args.no_cleanup:
            self.clean()
        self.no_cleanup = args.no_cleanup
        # Mapfile path display behavior
        self.basename = args.basename if hasattr(args, 'basename') else False
        # Scan behavior
        self.all = args.all_versions
        if self.all:
            self.no_version = False
        if args.latest_symlink:
            self.version = 'latest'
        # Counters
        self.nbmap = 0

    def __enter__(self):
        super(ProcessingContext, self).__enter__()
        # Get the DRS facet keys from pattern
        self.facets = self.cfg.get_facets('dataset_id')
        # Init data collector
        if self.directory:
            # The source is a list of directories
            # Instantiate file collector to walk through the tree
            self.source_type = 'file'
            self.sources = VersionedPathCollector(sources=self.directory,
                                                  project=self.project,
                                                  dir_format=self.cfg.translate('directory_format'))
            # Translate directory format pattern
            self.pattern = self.cfg.translate('directory_format', add_ending_filename=True)
            # Init file filter
            for regex, inclusive in self.file_filter:
                self.sources.FileFilter.add(regex=regex, inclusive=inclusive)
            # Init dir filter
            self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)
            if self.all:
                # Pick up all encountered versions by adding "/latest" exclusion
                self.sources.PathFilter.add(name='version_filter', regex='/latest', inclusive=False)
            elif self.version:
                # Pick up the specified version only (--version flag) by adding "/v{version}" inclusion
                # If --latest-symlink, --version is set to "latest"
                self.sources.PathFilter.add(name='version_filter', regex='/{}'.format(self.version))
            else:
                # Default behavior: pick up the latest version among encountered versions
                self.sources.default = True
        elif self.dataset_list:
            # The source is a list of dataset from a TXT file
            self.source_type = 'dataset'
            self.sources = DatasetCollector(sources=[x.strip() for x in self.dataset_list.readlines() if x.strip()])
            # Translate dataset_id format
            self.pattern = self.cfg.translate('dataset_id', add_ending_version=True, sep='.')
        else:
            # The source is a dataset ID (potentially from stdin)
            self.source_type = 'dataset'
            self.sources = DatasetCollector(sources=[self.dataset_id])
            # Translate dataset_id format
            self.pattern = self.cfg.translate('dataset_id', add_ending_version=True, sep='.')
        # Get number of sources
        self.nbsources = len(self.sources)
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if self.action == 'show':
            msg = 'Mapfile(s) to be generated: {}'.format(self.nbmap)
        else:
            msg = 'Mapfile(s) generated: {} (in {})'.format(self.nbmap, self.outdir)
        if self.nbsources == self.scan_data:
            # All files have been successfully scanned without errors
            msg = COLORS.SUCCESS(msg)
        elif self.nbsources == self.scan_errors:
            # All files have been skipped with errors
            msg = COLORS.FAIL(msg)
        else:
            # Some files have been scanned with at least one error
            msg = COLORS.WARNING(msg)
        # Print summary
        Print.summary(msg)
        super(ProcessingContext, self).__exit__(exc_type, exc_val, traceback)

    def clean(self):
        """
        Clean directory from incomplete mapfiles.
        Incomplete mapfiles from a previous run are silently removed.

        """
        for root, _, filenames in os.walk(self.outdir):
            for filename in fnmatch.filter(filenames, '*{}'.format(WORKING_EXTENSION)):
                os.remove(os.path.join(root, filename))

    @staticmethod
    def load_checksums(checksum_file):
        """
        Convert checksums file input as dictionary where (key: value) pairs respectively
        are the file path and its checksum.

        :param FileObject checksum_file: The submitted checksum file
        :returns: The loaded checksums
        :rtype: *dict*

        """
        checksums = dict()
        for checksum, path in [entry.split() for entry in checksum_file.read().splitlines()]:
            path = os.path.abspath(os.path.normpath(path))
            checksums[path] = checksum
        return checksums
