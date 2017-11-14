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
from uuid import uuid4 as uuid

from ESGConfigParser import SectionParser
from ESGConfigParser.custom_exceptions import NoConfigOption

from constants import *
from esgprep.utils.collectors import VersionedPathCollector
from esgprep.utils.custom_exceptions import *
from esgprep.utils.misc import cmd_exists


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: The command-line arguments parser
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.pbar = args.pbar
        self.config_dir = args.i
        self.project = args.project
        self.directory = args.directory
        self.mapfile_name = args.mapfile
        self.outdir = args.outdir
        self.notes_title = args.tech_notes_title
        self.notes_url = args.tech_notes_url
        self.no_version = args.no_version
        self.threads = args.max_threads
        self.dataset = args.dataset
        if not args.no_cleanup:
            self.clean()
        self.no_cleanup = args.no_cleanup
        self.no_checksum = args.no_checksum
        self.dir_filter = args.ignore_dir
        self.file_filter = []
        if args.include_file:
            self.file_filter.extend([(f, False) for f in args.include_file])
        else:
            # Default includes netCDF only
            self.file_filter.append(('^.*\.nc$', False))
        if args.exclude_file:
            # Default exclude hidden files
            self.file_filter.extend([(f, True) for f in args.exclude_file])
        else:
            self.file_filter.append(('^\..*$', True))
        self.all = args.all_versions
        if self.all:
            self.no_version = False
        self.version = None
        if args.version:
            self.version = 'v{}'.format(args.version)
        if args.latest_symlink:
            self.version = 'latest'
        self.scan_errors = None
        self.scan_files = None
        self.scan_err_log = logging.getLogger().handlers[0].baseFilename
        self.nb_map = None

    def __enter__(self):
        # Get checksum client
        self.checksum_client, self.checksum_type = self.get_checksum_client()
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.facets = self.cfg.get_facets('dataset_id')
        self.pattern = self.cfg.translate('directory_format', filename_pattern=True)
        # Get mapfile DRS is set in configuration file
        try:
            self.mapfile_drs = self.cfg.get('mapfile_drs')
        except NoConfigOption:
            self.mapfile_drs = None
        # Init data collector
        self.sources = VersionedPathCollector(sources=self.directory,
                                              data=self,
                                              dir_format=self.cfg.translate('directory_format'))
        # Init file filter
        for file_filter in self.file_filter:
            self.sources.FileFilter[uuid()] = file_filter
        # Init dir filter
        self.sources.PathFilter['base_filter'] = (self.dir_filter, True)
        if self.all:
            # Pick up all encountered versions by adding "/latest" exclusion
            self.sources.PathFilter['version_filter'] = ('/latest', True)
        elif self.version:
            # Pick up the specified version only (--version flag) by adding "/v{version}" inclusion
            # If --latest-symlink, --version is set to "latest"
            self.sources.PathFilter['version_filter'] = '/{}'.format(self.version)
        # Init threads pool
        self.pool = ThreadPool(int(self.threads))
        return self

    def __exit__(self, *exc):
        # Close threads pool
        self.pool.close()
        self.pool.join()
        # Decline outputs depending on the scan results
        # Raise errors when one or several files have been skipped or failed
        # Default is sys.exit(0)
        if self.scan_files and not self.scan_errors:
            # All files have been successfully scanned
            # Print number of generated mapfiles
            if self.pbar:
                print('{}: {} (see {})'.format('Mapfile(s) generated', self.nb_map, self.outdir))
            logging.info('{} mapfile(s) generated'.format(self.nb_map))
            logging.info('==> Scan completed ({} file(s) scanned)'.format(self.scan_files))
        if not self.scan_files and not self.scan_errors:
            # Results list is empty = no files scanned/found
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

    def get_checksum_client(self):
        """
        Gets the checksum client to use.
        Be careful to Exception constants by reading two different sections.

        :returns: The checksum client
        :rtype: *str*

        """
        if self.no_checksum:
            return None, None
        else:
            _cfg = SectionParser(section='DEFAULT', directory=self.config_dir)
            if _cfg.has_option('checksum', section='DEFAULT'):
                checksum_client, checksum_type = _cfg.get_options_from_table('checksum')[0]
            else:  # Use SHA256 as default because esg.ini not mandatory in configuration directory
                checksum_client, checksum_type = 'sha256sum', 'SHA256'
            if not cmd_exists(checksum_client):
                raise ChecksumClientNotFound(checksum_client)
            else:
                return checksum_client, checksum_type

    def clean(self):
        """
        Clean directory from incomplete mapfiles.
        Incomplete mapfiles from a previous run are silently removed.

        """
        for root, _, filenames in os.walk(self.outdir):
            for filename in fnmatch.filter(filenames, '*{}'.format(WORKING_EXTENSION)):
                os.remove(os.path.join(root, filename))
        logging.info('{} cleaned'.format(self.outdir))
