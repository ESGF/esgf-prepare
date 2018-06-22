#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import fnmatch
import os
from multiprocessing import Lock, Value, cpu_count
from multiprocessing.managers import SyncManager

from ESGConfigParser import SectionParser
from ESGConfigParser.custom_exceptions import NoConfigOption, NoConfigSection

from constants import *
from esgprep.utils.collectors import VersionedPathCollector, DatasetCollector
from esgprep.utils.custom_exceptions import *
from esgprep.utils.misc import Print, COLORS


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: The command-line arguments parser
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.version = None
        self.dataset_list = None
        self.dataset_id = None
        self.no_checksum = None
        self.notes_title = None
        self.notes_url = None
        self.checksums_from = None
        self.config_dir = args.i
        self.project = args.project
        self.action = args.action
        self.mapfile_name = args.mapfile
        self.outdir = args.outdir
        self.no_version = args.no_version
        self.processes = args.max_processes if args.max_processes <= cpu_count() else cpu_count()
        self.use_pool = (self.processes != 1)
        self.dataset_name = args.dataset_name
        self.dir_filter = args.ignore_dir
        self.basename = args.basename if hasattr(args, 'basename') else False
        self.quiet = args.quiet if hasattr(args, 'quiet') else False
        self.file_filter = []
        if args.include_file:
            self.file_filter.extend([(f, True) for f in args.include_file])
        else:
            # Default includes netCDF only
            self.file_filter.append(('^.*\.nc$', True))
        if args.exclude_file:
            # Default exclude hidden files
            self.file_filter.extend([(f, False) for f in args.exclude_file])
        else:
            self.file_filter.append(('^\..*$', False))
        self.all = args.all_versions
        if self.all:
            self.no_version = False
        if args.version:
            self.version = 'v{}'.format(args.version)
        if args.latest_symlink:
            self.version = 'latest'
        if not args.no_cleanup:
            self.clean()
        self.no_cleanup = args.no_cleanup
        self.directory = args.directory
        if hasattr(args, 'dataset_list'):
            self.dataset_list = args.dataset_list
        if hasattr(args, 'dataset_id'):
            self.dataset_id = args.dataset_id
        if hasattr(args, 'no_checksum'):
            self.no_checksum = args.no_checksum
        if hasattr(args, 'tech_notes_title'):
            self.notes_title = args.tech_notes_title
        if hasattr(args, 'tech_notes_url'):
            self.notes_url = args.tech_notes_url
        if hasattr(args, 'checksums_from'):
            if args.checksums_from:
                self.checksums_from = self.load_checksums(args.checksums_from)
            else:
                self.checksums_from = args.checksums_from
        # Declare counters for summary
        self.scan_errors = 0
        self.scan_files = 0
        self.nb_map = 0
        # Init process manager
        if self.use_pool:
            manager = SyncManager()
            manager.start()
            self.progress = manager.Value('i', 0)
        else:
            self.progress = Value('i', 0)
        self.lock = Lock()
        self.nbsources = None

    def __enter__(self):
        # Get checksum client
        self.checksum_type = self.get_checksum_type()
        # Get mapfile DRS is set in configuration file
        # Has to be read before "project:id" section to raise proper exception infos
        try:
            _cfg = SectionParser(section='config:{}'.format(self.project), directory=self.config_dir)
            self.mapfile_drs = _cfg.get('mapfile_drs')
        except (NoConfigOption, NoConfigSection):
            self.mapfile_drs = None
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.facets = self.cfg.get_facets('dataset_id')
        # Init data collector
        if self.directory:
            # The source is a list of directories
            # Instantiate file collector to walk through the tree
            self.source_type = 'file'
            self.sources = VersionedPathCollector(sources=self.directory,
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
        # Decline outputs depending on the scan results
        if self.nbsources == self.scan_files:
            # All files have been successfully scanned without errors
            msg = COLORS.OKGREEN
        elif self.nbsources == self.scan_errors:
            # All files have been skipped with errors
            msg = COLORS.FAIL
        else:
            # Some files have been scanned with at least one error
            msg = COLORS.WARNING
        msg += 'Number of file(s) scanned: {}\n'.format(self.scan_files)
        msg += 'Number of errors: {}\n'.format(self.scan_errors)
        if self.action == 'show':
            msg += 'Mapfile(s) to be generated: {}\n'.format(self.nb_map)
        elif self.action == 'make':
            msg += 'Mapfile(s) generated: {} (see {})\n'.format(self.nb_map, self.outdir)
        msg += COLORS.ENDC
        # Print summary
        Print.summary(msg)
        # Print log path if exists
        Print.log(Print.LOGFILE)

    def get_checksum_type(self):
        """
        Gets the checksum type to use.
        Be careful to Exception constants by reading two different sections.

        :returns: The checksum type
        :rtype: *str*

        """
        if self.no_checksum:
            return None
        _cfg = SectionParser(section='DEFAULT', directory=self.config_dir)
        if _cfg.has_option('checksum'):
            checksum_type = _cfg.get_options_from_table('checksum')[0][1].lower()
        else:  # Use SHA256 as default because esg.ini not mandatory in configuration directory
            checksum_type = 'sha256'
        if checksum_type not in checksum_types:
            raise InvalidChecksumType(checksum_type)
        return checksum_type

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
