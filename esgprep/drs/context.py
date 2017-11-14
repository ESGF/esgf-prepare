#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import logging
import os
import sys
from multiprocessing.dummy import Pool as ThreadPool
from uuid import uuid4 as uuid

from ESGConfigParser import SectionParser

from constants import *
from esgprep.utils.collectors import Collector
from esgprep.utils.custom_exceptions import *
from esgprep.utils.misc import cmd_exists, load
from handler import DRSTree, DRSPath


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.pbar = args.pbar
        self.config_dir = args.i
        self.directory = args.directory
        self.root = os.path.normpath(args.root)
        self.set_values = {}
        if args.set_value:
            self.set_values = dict(args.set_value)
        self.set_keys = {}
        if args.set_key:
            self.set_keys = dict(args.set_key)
        self.threads = args.max_threads
        self.project = args.project
        self.action = args.action
        if args.copy:
            self.mode = 'copy'
        elif args.link:
            self.mode = 'link'
        elif args.symlink:
            self.mode = 'symlink'
        else:
            self.mode = 'move'
        self.version = args.version
        DRSPath.TREE_VERSION = 'v{}'.format(args.version)
        self.no_checksum = args.no_checksum
        self.scan = True
        self.scan_errors = None
        self.scan_files = None
        self.scan_err_log = logging.getLogger().handlers[0].baseFilename

    def __enter__(self):
        # Get checksum client
        self.checksum_client, self.checksum_type = self.get_checksum_client()
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        self.facets = self.cfg.get_facets('directory_format')
        self.pattern = self.cfg.translate('filename_format')
        # Init DRS tree
        self.tree = DRSTree(self.root, self.version, self.mode)
        # Disable file scan if a previous DRS tree have generated using same context and no "list" action
        if self.action != 'list' and os.path.isfile(TREE_FILE):
            reader = load(TREE_FILE)
            old_args = reader.next()
            # Ensure that processing context is similar to previous step
            if self.check_args(old_args):
                self.scan = False
        # Init data collector
        self.sources = Collector(sources=self.directory,
                                 data=self)
        # Init file filter
        # Only supports netCDF files
        self.sources.FileFilter[uuid()] = ('^.*\.nc$', False)
        # And exclude hidden files
        self.sources.FileFilter[uuid()] = ('^\..*$', True)
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
                logging.warning('==> All files have been ignored or have failed leading to no DRS tree.')
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

    def check_args(self, old_args):
        """
        Checks command-line argument to avoid discrepancies between ``esgprep drs`` steps.

        :param *dict* old_args: The recorded arguments
        :raises Error: If one argument differs

        """
        for k in CONTROLLED_ARGS:
            if self.__getattribute__(k) != old_args[k]:
                logging.warning('"{}" argument has changed: "{}" instead of "{}". '
                                'File scan re-run...'.format(k,
                                                             self.__getattribute__(k),
                                                             old_args[k]))
                return False
        return True
