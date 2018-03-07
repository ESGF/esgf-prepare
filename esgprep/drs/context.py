#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import logging
import os
import re
import sys
from multiprocessing.dummy import Pool as ThreadPool

from ESGConfigParser import SectionParser
from tqdm import tqdm

from constants import *
from esgprep.utils.collectors import Collector
from esgprep.utils.custom_exceptions import *
from esgprep.utils.misc import load
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
        self.rescan = args.rescan
        self.commands_file = args.commands_file
        self.overwrite_commands_file = args.overwrite_commands_file
        self.upgrade_from_latest = args.upgrade_from_latest
        try:
            self.ignore_from_latest = open(args.ignore_from_latest, 'r').read().splitlines()
            self.upgrade_from_latest = True
        except:
            self.ignore_from_latest = list()
        self.set_values = {}
        if args.set_value:
            self.set_values = dict(args.set_value)
        self.set_keys = {}
        if args.set_key:
            self.set_keys = dict(args.set_key)
        self.threads = args.max_threads
        self.use_pool = (self.threads > 1)
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
        self.scan = True
        self.scan_errors = None
        self.scan_files = None
        self.scan_err_log = logging.getLogger().handlers[0].baseFilename
        if self.commands_file and self.action != 'todo':
            print '"{}" action ignores "--commands-file" argument.'.format(self.action)
            self.commands_file = None
        if self.overwrite_commands_file and not self.commands_file:
            print '--overwrite-commands-file ignored'

    def __enter__(self):
        # Get checksum client
        self.checksum_type = self.get_checksum_type()
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        # check if --commands-file argument specifies existing file
        self.check_existing_commands_file()
        # Warn user about unconsidered hard-coded elements
        for pattern_element in self.cfg.get('directory_format').strip().split("/"):
            if not re.match(re.compile(r'%\([\w]+\)s'), pattern_element):
                msg = 'Hard-coded DRS elements (as "{}") in "directory_format"' \
                      'are not supported.'.format(pattern_element)
                if self.pbar:
                    print(msg)
                logging.warning(msg)
                break
        self.facets = self.cfg.get_facets('directory_format')
        self.pattern = self.cfg.translate('filename_format')
        # Init DRS tree
        self.tree = DRSTree(self.root, self.version, self.mode, self.commands_file)
        # Disable file scan if a previous DRS tree have generated using same context and no "list" action
        if not self.rescan and self.action != 'list' and os.path.isfile(TREE_FILE):
            reader = load(TREE_FILE)
            old_args = reader.next()
            # Ensure that processing context is similar to previous step
            if self.check_args(old_args):
                self.scan = False
        # Init data collector
        if self.pbar:
            self.sources = Collector(sources=self.directory, data=self)
        else:
            self.sources = Collector(sources=self.directory, spinner=False, data=self)
        # Init file filter
        # Only supports netCDF files
        self.sources.FileFilter.add(regex='^.*\.nc$')
        # And exclude hidden files
        self.sources.FileFilter.add(regex='^\..*$', inclusive=False)
        # Init progress bar
        if self.scan:
            nfiles = len(self.sources)
            if self.pbar and nfiles:
                self.pbar = tqdm(desc='Scanning incoming files',
                                 total=nfiles,
                                 bar_format='{desc}: {percentage:3.0f}% | {n_fmt}/{total_fmt} files',
                                 ncols=100,
                                 file=sys.stdout)
        else:
            msg = 'Skipping incoming files scan (use "--rescan" to force it) -- ' \
                  'Using cached DRS tree from {}'.format(TREE_FILE)
            if self.pbar:
                print(msg)
            logging.warning(msg)
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
            logging.info('==> Scan completed ({} file(s) scanned)'.format(self.scan_files))
        if not self.scan_files and not self.scan_errors:
            # Results list is empty = no files scanned/found
            if self.pbar:
                print('No files found')
            logging.warning('==> No files found')
            sys.exit(1)
        if self.scan_files and self.scan_errors:
            if self.scan:
                msg = 'Scan errors: {} (see {})'
            else:
                msg = 'Orginal scan errors: {} (previously written to {})'
            # Print number of scan errors in any case
            if self.pbar:
                print(msg.format(self.scan_errors, self.scan_err_log))
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

    def check_existing_commands_file(self):
        """
        Check for existing commands file,
        and depending on ``--overwrite-commands-file`` setting,
        either delete it or throw a fatal error.

        """
        if self.commands_file and os.path.exists(self.commands_file):
            if self.overwrite_commands_file:
                os.remove(self.commands_file)
            else:
                print "File '{}' already exists and '--overwrite-commands-file'" \
                      "option not used.".format(self.commands_file)
                sys.exit(1)

    def get_checksum_type(self):
        """
        Gets the checksum type to use.
        Be careful to Exception constants by reading two different sections.

        :returns: The checksum type
        :rtype: *str*

        """
        _cfg = SectionParser(section='DEFAULT', directory=self.config_dir)
        if _cfg.has_option('checksum', section='DEFAULT'):
            checksum_type = _cfg.get_options_from_table('checksum')[0][1].lower()
        else:  # Use SHA256 as default because esg.ini not mandatory in configuration directory
            checksum_type = 'sha256'
        if checksum_type not in checksum_types:
            raise InvalidChecksumType(checksum_type)
        return checksum_type

    def check_args(self, old_args):
        """
        Checks command-line argument to avoid discrepancies between ``esgprep drs`` steps.

        :param *dict* old_args: The recorded arguments
        :raises Error: If one argument differs

        """
        for k in CONTROLLED_ARGS:
            if self.__getattribute__(k) != old_args[k]:
                logging.warning('"{}" argument has changed: "{}" instead of "{}". '
                                'File rescan needed.'.format(k,
                                                             self.__getattribute__(k),
                                                             old_args[k]))
                return False
        return True
