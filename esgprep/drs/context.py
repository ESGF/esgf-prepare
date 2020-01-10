# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from esgprep._collectors import Collector
from esgprep._collectors.dataset_id import DatasetCollector
from esgprep._collectors.drs_path import DRSPathCollector
from esgprep._contexts.multiprocessing import MultiprocessingContext
from esgprep._handlers.drs_tree import DRSTree
from esgprep._utils.print import *


class ProcessingContext(MultiprocessingContext):
    """
    Processing context class to drive main process.

    """

    def __init__(self, args):
        super(ProcessingContext, self).__init__(args)

        # Set root of DRS tree.
        self.root = self.set('root')

        # Force rescanning files.
        self.rescan = self.set('rescan')

        # Remove all DRS versions.
        self.all = self.set('all_versions')

        # Set DRS facet value mapping.
        self.set_values = self.set('set_values', dict())

        # Update DRS facet value mapping with version.
        self.set_values.update({'dataset-version': self.version})

        # Set DRS facet key mapping.
        self.set_keys = self.set('set_keys', dict())

        # Set upgrade behavior.
        self.upgrade_from_latest = self.set('upgrade_from_latest')

        # Read filenames to ignore.
        try:
            self.ignore_from_latest = args.ignore_from_latest.read().splitlines()
            # Ignoring files from latest version takes priority on upgrade behavior setting.
            self.upgrade_from_latest = True
            Print.warning('"--ignore_from_latest" forces "--upgrade-from-latest" argument.')
        except (TypeError, IOError, AttributeError):
            self.ignore_from_latest = list()
        try:
            self.ignore_from_incoming = args.ignore_from_incoming.read().splitlines()
            Print.warning('"--ignore_from_incoming" ignores "--upgrade-from-latest" argument.')
        except (TypeError, IOError, AttributeError):
            self.ignore_from_incoming = list()

        # Set DRS migration mode.
        self.mode = 'move'
        for mode in ['copy', 'link', 'symlink']:
            if hasattr(args, mode) and getattr(args, mode):
                self.mode = mode
        # Set migration mode as subcommand value if not the default.
        if self.cmd != 'make':
            self.mode = self.cmd

        # Set output commands file.
        self.commands_file = self.set('commands_file', None)
        self.overwrite_commands_file = self.set('overwrite_commands_file', None)

        # Warn user about disabled checksum check.
        if self.no_checksum:
            msg = 'Checksumming disabled, DRS breach could occur -- '
            msg += 'Duplicated files will not be detected properly -- '
            msg += 'It is highly recommend to activate checksumming process.'
            Print.warning(msg)

        # Instantiate DRS tree.
        if self.use_pool:
            self.tree = self.manager.DRSTree(self.root, self.mode, self.commands_file)
        else:
            self.tree = DRSTree(self.root, self.mode, self.commands_file)

    def __enter__(self):
        super(ProcessingContext, self).__enter__()

        # Check if --commands-file argument specifies existing file
        self.check_commands_file()

        # Instantiate data collector.
        if self.cmd not in ['remove', 'latest']:

            # The input source is a list directories.
            self.sources = Collector(sources=self.directory)

        else:
            # The input source is a list directories.
            if self.directory:

                # Instantiate file collector to walk through the tree.
                self.sources = DRSPathCollector(sources=self.directory)

                # Initialize file filters.
                for regex, inclusive in self.file_filter:
                    self.sources.FileFilter.add(regex=regex, inclusive=inclusive)

                # Initialize directory filter.
                self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)

                # Set version filter.
                if self.all:
                    # Pick up all encountered versions by adding "/latest" exclusion
                    self.sources.PathFilter.add(name='version_filter', regex='/latest', inclusive=False)
                elif self.version:
                    # Pick up the specified version only (--version flag) by adding "/v{version}" inclusion
                    # If --latest-symlink, --version is set to "latest"
                    self.sources.PathFilter.add(name='version_filter', regex='/{}'.format(self.version))
                else:
                    # Default behavior: pick up the latest version among encountered versions.
                    self.sources.PathFilter.add(name='version_filter', regex='/latest', inclusive=False)
                    self.sources.default = True

                # Returns only dataset parent directory instead of files.
                self.sources.dataset_parent = True

            # The input source is a list of dataset identifiers (potentially from stdin).
            else:

                # Instantiate dataset collector.
                self.sources = DatasetCollector(sources=self.dataset)

        return self

    # noinspection PyTypeChecker
    def check_commands_file(self):
        """
        Checks commands file behavior.

        """
        # Actions takes priority on commands file setting.
        if self.commands_file and self.action != 'todo':
            Print.warning('"--commands-file" argument ignored.')
            self.commands_file = None

        # Overwrite commands file only if exists.
        if self.overwrite_commands_file and not self.commands_file:
            self.overwrite_commands_file = None
            Print.warning('"--overwrite-commands-file" argument ignored.')

        # Depending on --overwrite-commands-file setting, either delete it or throw a fatal error.
        if self.commands_file and os.path.exists(self.commands_file):
            if self.overwrite_commands_file:
                os.remove(self.commands_file)
            else:
                msg = 'Command file "{}" already exists --'.format(self.commands_file)
                msg += ' Please use "--overwrite-commands-file" option.'
                Print.error(COLORS.FAIL(msg))
                sys.exit(1)
