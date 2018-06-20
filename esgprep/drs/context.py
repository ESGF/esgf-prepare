#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import re
import sys
from multiprocessing import cpu_count, Lock, Value
from multiprocessing.managers import SyncManager
from uuid import uuid4 as uuid

from ESGConfigParser import SectionParser

from constants import *
from custom_exceptions import *
from esgprep.utils.collectors import Collector
from esgprep.utils.custom_exceptions import *
from esgprep.utils.misc import load, Print, COLORS
from handler import DRSTree, DRSPath


class ProcessManager(SyncManager):
    pass


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.config_dir = args.i
        self.directory = args.directory
        self.root = os.path.normpath(args.root)
        self.rescan = args.rescan
        self.commands_file = args.commands_file
        self.overwrite_commands_file = args.overwrite_commands_file
        self.upgrade_from_latest = args.upgrade_from_latest
        try:
            self.ignore_from_latest = args.ignore_from_latest.read().splitlines()
            self.upgrade_from_latest = True
        except (TypeError, IOError, AttributeError):
            self.ignore_from_latest = list()
        try:
            self.ignore_from_incoming = args.ignore_from_incoming.read().splitlines()
        except (TypeError, IOError, AttributeError):
            self.ignore_from_latest = list()
        self.set_values = {}
        if args.set_value:
            self.set_values = dict(args.set_value)
        self.set_keys = {}
        if args.set_key:
            self.set_keys = dict(args.set_key)
        self.processes = args.max_processes if args.max_processes <= cpu_count() else cpu_count()
        self.use_pool = (self.processes != 1)
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
        # Declare counters for summary
        self.scan_errors = 0
        self.scan_files = 0
        self.scan = True
        if self.commands_file and self.action != 'todo':
            msg = COLORS.BOLD + '"todo" action ignores "--commands-file" argument' + COLORS.ENDC
            Print.warning(msg)
            self.commands_file = None
        if self.overwrite_commands_file and not self.commands_file:
            msg = COLORS.BOLD + '"--overwrite-commands-file" ignored' + COLORS.ENDC
            Print.warning(msg)
        self.no_checksum = args.no_checksum
        if self.no_checksum:
            msg = COLORS.BOLD + 'Checksumming disabled, DRS breach could occur -- '
            msg += 'It is highly recommend to activate checksumming processes.' + COLORS.ENDC
            Print.warning(msg)
        # Init process manager
        if self.use_pool:
            SyncManager.register('tree', DRSTree, exposed=('create_leaf',
                                                           'get_display_lengths',
                                                           'check_uniqueness',
                                                           'list',
                                                           'todo',
                                                           'tree'
                                                           'upgrade'))
            manager = SyncManager()
            manager.start()
            self.tree = manager.tree()
            self.progress = manager.Value('i', 0)
        else:
            self.tree = DRSTree()
            self.progress = Value('i', 0)
        self.lock = Lock()
        self.nbsources = None

    def __enter__(self):
        # Get checksum client
        self.checksum_type = self.get_checksum_type()
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        # Check if --commands-file argument specifies existing file
        self.check_existing_commands_file()
        # Get DRS facets
        self.facets = self.cfg.get_facets('directory_format')
        # Raise error when %(version)s is not part of the final directory format
        if 'version' not in self.facets:
            raise NoVersionPattern(self.cfg.get('directory_format'), self.facets)
        # Consider hard-coded elements in directory format
        idx = 0
        for pattern_element in self.cfg.get('directory_format').strip().split("/"):
            try:
                # If pattern is %(...)s
                # Get its index in the list of facets
                key = re.match(re.compile(r'%\(([\w]+)\)s'), pattern_element).groups()[0]
                idx = self.facets.index(key)
            except AttributeError:
                # If pattern is not %(...)s
                # Generate a uuid()
                key = str(uuid())
                # Insert hard-coded string in self.facets to be part of DRS path
                self.facets.insert(idx + 1, key)
                # Set the value using --set-value
                self.set_values[key] = pattern_element
                # Add the uuid to the ignored keys
                IGNORED_KEYS.append(key)
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
        self.sources = Collector(sources=self.directory)
        # Init file filter
        # Only supports netCDF files
        self.sources.FileFilter.add(regex='^.*\.nc$')
        # And exclude hidden files
        self.sources.FileFilter.add(regex='^\..*$', inclusive=False)
        # Get number of sources
        self.nbsources = len(self.sources)
        return self

    def __exit__(self, *exc):
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
        msg += '\n\nNumber of file(s) scanned: {}'.format(self.scan_files)
        msg += '\nNumber of errors: {}'
        if self.scan:
            msg += ' (from orginal scan previously written to {})'.format(Print.ERRFILE)
        msg += COLORS.ENDC
        # Print summary
        Print.summary(msg)
        # Print log path if exists
        Print.log(COLORS.HEADER + '\nSee log: {}\n'.format(Print.LOGFILE) + COLORS.ENDC)

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
                msg = COLORS.FAIL
                msg += '\nCommand file "{}" already exists --'.format(self.commands_file)
                msg += 'Please use "--overwrite-commands-file" option.'
                msg += COLORS.ENDC
                Print.error(msg)
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
        Checks command-line argument to avoid discrepancies between ``esgdrs`` steps.

        :param *dict* old_args: The recorded arguments
        :raises Error: If one argument differs

        """
        for k in CONTROLLED_ARGS:
            if self.__getattribute__(k) != old_args[k]:
                msg = COLORS.BOLD
                msg += '"{}" argument has changed: "{}" instead of "{}" -- '.format(k,
                                                                                    self.__getattribute__(k),
                                                                                    old_args[k])
                msg += 'Rescan files...'
                msg += COLORS.ENDC
                Print.warning(msg)
                return False
        return True
