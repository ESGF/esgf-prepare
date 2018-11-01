#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from uuid import uuid4 as uuid

from ESGConfigParser import SectionParser
from constants import *
from custom_exceptions import *
from esgprep.utils.collectors import Collector
from esgprep.utils.context import MultiprocessingContext
from esgprep.utils.custom_print import *
from handler import DRSTree, DRSPath


class ProcessingContext(MultiprocessingContext):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        super(ProcessingContext, self).__init__(args)
        # DRS root tree
        self.root = os.path.normpath(args.root)
        # Scan behavior
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
            self.ignore_from_incoming = list()
        # DRS migration mode
        if args.copy:
            self.mode = 'copy'
        elif args.link:
            self.mode = 'link'
        elif args.symlink:
            self.mode = 'symlink'
        else:
            self.mode = 'move'
        # Specified version
        self.version = args.version
        DRSPath.TREE_VERSION = 'v{}'.format(args.version)
        # Declare counters for summary
        self.scan = True
        if self.commands_file and self.action != 'todo':
            Print.warning('"todo" action ignores "--commands-file" argument')
            self.commands_file = None
        if self.overwrite_commands_file and not self.commands_file:
            Print.warning('"--overwrite-commands-file" ignored')
        self.no_checksum = args.no_checksum
        if self.no_checksum:
            msg = 'Checksumming disabled, DRS breach could occur -- '
            msg += 'Incoming files are all supposed to be different from latest version if exists --'
            msg += 'It is highly recommend to activate checksumming processes.'
            Print.warning(msg)

    def __enter__(self):
        super(ProcessingContext, self).__enter__()
        # Get the DRS facet keys from pattern
        self.facets = self.cfg.get_facets('directory_format')
        # Check if --commands-file argument specifies existing file
        self.check_existing_commands_file()
        # Raise error when %(version)s is not part of the final directory format
        if 'version' not in self.facets:
            raise NoVersionPattern(self.cfg.get('directory_format'), self.facets)
        # Consider hard-coded elements in directory format
        idx = 0
        for pattern_element in self.cfg.get('directory_format').strip().split("/"):
            try:
                # If pattern is %(...)s, get its index in the list of facets
                key = re.match(re.compile(r'%\(([\w]+)\)s'), pattern_element).groups()[0]
                idx = self.facets.index(key)
            except AttributeError:
                # If pattern is not %(...)s, generate a uuid()
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
                msg = 'Command file "{}" already exists --'.format(self.commands_file)
                msg += 'Please use "--overwrite-commands-file" option.'
                Print.error(COLORS.FAIL(msg))
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
