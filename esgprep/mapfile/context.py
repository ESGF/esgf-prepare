#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import fnmatch
import logging
import os
import sys
from multiprocessing.dummy import Pool as ThreadPool

from ESGConfigParser import SectionParser
from ESGConfigParser.custom_exceptions import NoConfigOption, NoConfigSection
from tqdm import tqdm

from constants import *
from esgprep.utils.collectors import VersionedPathCollector, DatasetCollector
from esgprep.utils.custom_exceptions import *
from esgprep.utils.ctx_base import BaseContext


class ProcessingContext(BaseContext):
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
        self.pbar = args.pbar
        self.config_dir = args.i
        self.project = args.project
        self.action = args.action
        self.mapfile_name = args.mapfile
        self.outdir = args.outdir
        self.no_version = args.no_version
        self.threads = args.max_threads
        self.use_pool = (self.threads > 1)
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
        self.scan_errors = None
        self.scan_files = None
        self.scan_err_log = logging.getLogger().handlers[0].baseFilename
        self.nb_map = None

    def __enter__(self):
        # Get checksum client
        self.checksum_type = self.get_checksum_type()
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.facets = self.cfg.get_facets('dataset_id')
        # Get mapfile DRS is set in configuration file
        try:
            _cfg = SectionParser(section='config:{}'.format(self.project), directory=self.config_dir)
            self.mapfile_drs = _cfg.get('mapfile_drs')
        except (NoConfigOption, NoConfigSection):
            self.mapfile_drs = None
        # Init data collector
        if self.directory:
            # The source is a list of directories
            # Instantiate file collector to walk through the tree
            self.source_type = 'file'
            if self.pbar:
                self.sources = VersionedPathCollector(sources=self.directory,
                                                      data=self,
                                                      dir_format=self.cfg.translate('directory_format'))
            else:
                self.sources = VersionedPathCollector(sources=self.directory,
                                                      data=self,
                                                      spinner=False,
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
            self.sources = DatasetCollector(sources=[x.strip() for x in self.dataset_list.readlines() if x.strip()],
                                            data=self,
                                            spinner=False)
            # Translate dataset_id format
            self.pattern = self.cfg.translate('dataset_id', add_ending_version=True, sep='.')
        else:
            # The source is a dataset ID (potentially from stdin)
            self.source_type = 'dataset'
            self.sources = DatasetCollector(sources=[self.dataset_id],
                                            data=self,
                                            spinner=False)
            # Translate dataset_id format
            self.pattern = self.cfg.translate('dataset_id', add_ending_version=True, sep='.')
        # Init progress bar
        nfiles = len(self.sources)
        if self.pbar and nfiles:
            self.pbar = tqdm(desc='Mapfile(s) generation',
                             total=nfiles,
                             bar_format='{desc}: {percentage:3.0f}% | {n_fmt}/{total_fmt} '
                                        + SOURCE_TYPE[self.source_type],
                             ncols=100,
                             file=sys.stdout)
        # Init threads pool
        if self.use_pool:
            self.pool = ThreadPool(int(self.threads))
        return self

    def __exit__(self, *exc):
        # Close threads pool
        if self.use_pool:
            self.pool.close()
            self.pool.join()
        # Decline outputs depending on the scan results
        # Raise errors when one or several files have been skipped or failed
        # Default is sys.exit(0)
        if self.scan_files and not self.scan_errors:
            # All files have been successfully scanned
            if self.action == 'show':
                # Print mapfiles to be generated
                if self.pbar:
                    print('{}: {}'.format('Mapfile(s) to be generated', self.nb_map))
                logging.info('{} mapfile(s) to be generated'.format(self.nb_map))
            elif self.action == 'make':
                # Print number of generated mapfiles
                if self.pbar:
                    print('{}: {} (see {})'.format('Mapfile(s) generated', self.nb_map, self.outdir))
                logging.info('{} mapfile(s) generated'.format(self.nb_map))
            logging.info('==> Scan completed ({} file(s) scanned)'.format(self.scan_files))
        if not self.scan_files and not self.scan_errors:
            # Results list is empty = no files scanned/found
            if self.pbar:
                print('No files found')
            logging.warning('==> No files found')
            sys.exit(1)
        if self.scan_files and self.scan_errors:
            # Print number of scan errors in any case
            if self.pbar:
                print('{}: {} (see {})'.format('Scan errors', self.scan_errors, self.scan_err_log))
            logging.warning('{} file(s) have been skipped'
                            ' (see {})'.format(self.scan_errors, self.scan_err_log))
            if self.scan_errors == self.scan_files:
                # All files have been skipped or failed during the scan
                logging.warning('==> All files have been ignored or have failed leading to no mapfile.')
                sys.exit(3)
            else:
                # Some files have been skipped or failed during the scan
                logging.info('==> Scan completed ({} file(s) scanned)'.format(self.scan_files))
                sys.exit(2)

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
        if _cfg.has_option('checksum', section='DEFAULT'):
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
        logging.info('{} cleaned'.format(self.outdir))

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
