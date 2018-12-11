#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to use with this package.

"""

import getpass
from multiprocessing import cpu_count, Lock
from multiprocessing.managers import SyncManager

from ESGConfigParser import SectionParser
from ESGConfigParser.custom_exceptions import NoConfigOption, NoConfigSection
from esgprep.utils.custom_print import *
from requests.auth import HTTPBasicAuth


class BaseContext(object):
    """
    Base class for processing context manager.

    """

    def __init__(self, args):
        # Init print management
        Print.init(log=args.log, debug=args.debug, cmd=args.prog)
        # Print command-line
        Print.command()
        self._process_color_arg(args)
        # Get project
        self.project = args.project

    def __enter__(self):
        pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Print log path if exists
        Print.log()

    def _process_color_arg(self, args):
        # process --color / --no-color arg if present
        if 'color' in args and args.color:
            enable_colors()
        if 'no_color' in args and args.no_color:
            disable_colors()


class GitHubBaseContext(BaseContext):
    """
    Base manager class for esgfetch* modules.

    """

    def __init__(self, args):
        super(GitHubBaseContext, self).__init__(args)
        # Fetching behavior
        self.keep = args.k
        self.overwrite = args.o
        self.backup_mode = args.b
        # GitHub credentials
        self.gh_user = args.gh_user
        self.gh_password = args.gh_password
        self.auth = None
        # Error counter
        self.error = False

    def __enter__(self):
        super(GitHubBaseContext, self).__enter__()
        # If the username is set but not the password, prompt for it interactively
        if self.gh_user and not self.gh_password and sys.stdout.isatty():
            msg = COLOR().bold('Github password for user {}: '.format(self.gh_user))
            self.gh_password = getpass.getpass(msg)
        # GitHub authentication
        self.auth = self.authenticate()
        return self

    def authenticate(self):
        """
        Builds GitHub HTTP authenticator

        :returns: The HTTP authenticator
        :rtype: *requests.auth.HTTPBasicAuth*

        """
        return HTTPBasicAuth(self.gh_user, self.gh_password) if self.gh_user and self.gh_password else None


class MultiprocessingContext(BaseContext):
    """
    Base manager class for esgmapfile, esgdrs and esgcheckvocab modules.

    """

    def __init__(self, args):
        super(MultiprocessingContext, self).__init__(args)
        # Configuration directory (i.e., INI files folder)
        self.config_dir = args.i
        # Command line action
        if hasattr(args, 'action'):
            self.action = args.action
        # Input
        self.directory = args.directory
        if hasattr(args, 'dataset_list'):
            self.dataset_list = args.dataset_list
        if hasattr(args, 'dataset_id'):
            self.dataset_id = args.dataset_id
        if hasattr(args, 'incoming'):
            self.incoming = args.incoming
        # Multiprocessing configuration
        self.processes = args.max_processes if args.max_processes <= cpu_count() else cpu_count()
        self.use_pool = (self.processes != 1)
        # Scan counters
        self.scan_errors = 0
        self.scan_data = 0
        self.nbsources = 0
        # Process manager
        if self.use_pool:
            self.manager = SyncManager()
            self.manager.start()
            self.progress = self.manager.Value('i', 0)
            Print.BUFFER = self.manager.Value(c_char_p, '')
        else:
            self.progress = Value('i', 0)
        # Stdout lock
        self.lock = Lock()
        # Directory filter (esgmapfile + esgcheckvocab)
        if hasattr(args, 'ignore_dir'):
            self.dir_filter = args.ignore_dir
        # File filters (esgmapfile + esgcheckvocab)
        self.file_filter = []
        if hasattr(args, 'include_files'):
            if args.include_file:
                self.file_filter.extend([(f, True) for f in args.include_file])
            else:
                # Default includes netCDF only
                self.file_filter.append(('^.*\.nc$', True))
        if hasattr(args, 'exclude_file'):
            if args.exclude_file:
                self.file_filter.extend([(f, False) for f in args.exclude_file])
            else:
                # Default exclude hidden files
                self.file_filter.append(('^\..*$', False))
        # Facet declaration (esgcheckvocab + esgdrs)
        self.set_values = {}
        if hasattr(args, 'set_value') and args.set_value:
            self.set_values = dict(args.set_value)
        self.set_keys = {}
        if hasattr(args, 'set_key') and args.set_key:
            self.set_keys = dict(args.set_key)

    def __enter__(self):
        super(MultiprocessingContext, self).__enter__()
        # Get checksum client
        self.checksum_type = self.get_checksum_type()
        # Get mapfile DRS
        self.mapfile_drs = self.get_mapfile_drs()
        # Configuration parser to be loaded in the end
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Decline outputs depending on the scan results
        msg = 'Number of file(s) scanned: {}\n'.format(self.scan_data)
        msg += 'Number of error(s): {}'.format(self.scan_errors)
        if not self.scan_errors:
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
        super(MultiprocessingContext, self).__exit__(exc_type, exc_val, exc_tb)

    def get_checksum_type(self):
        """
        Gets the checksum type to use.
        Be careful to Exception constants by reading two different sections.

        :returns: The checksum type
        :rtype: *str*

        """
        if hasattr(self, 'no_checksum') and self.no_checksum:
            return None
        _cfg = SectionParser(section='DEFAULT', directory=self.config_dir)
        if _cfg.has_option('checksum'):
            checksum_type = _cfg.get_options_from_table('checksum')[0][1].lower()
        else:  # Use SHA256 as default because esg.ini not mandatory in configuration directory
            checksum_type = 'sha256'
        if checksum_type not in checksum_types:
            raise InvalidChecksumType(checksum_type)
        _cfg.reset()
        return checksum_type

    def get_mapfile_drs(self):

        try:
            _cfg = SectionParser(section='config:{}'.format(self.project), directory=self.config_dir)
            mapfile_drs = _cfg.get('mapfile_drs')
            _cfg.reset()
        except (NoConfigOption, NoConfigSection):
            mapfile_drs = None
        return mapfile_drs
