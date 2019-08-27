# -*- coding: utf-8 -*-

"""
.. module:: esgprep._contexts.multiprocessing.py
   :platform: Unix
   :synopsis: Multiprocessing context.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from configparser import NoOptionError, NoSectionError
from hashlib import algorithms_available as checksum_types
from multiprocessing import Lock
from multiprocessing.managers import SyncManager
import pyessv
from esgprep._contexts import BaseContext
from esgprep._exceptions import InvalidChecksumType, MissingCVdata
from esgprep._utils.print import *


class MultiprocessingContext(BaseContext):
    """
    Base class for multiprocessing context manager.

    """

    def __init__(self, args):
        super(MultiprocessingContext, self).__init__(args)

        # Load configuration from esg.ini file.
        self.cfg = self.set('i')

        # Get sub-command line.
        self.cmd = self.set('cmd')

        # Set input action.
        self.action = self.set('action')

        # Set input DRS directory.
        self.directory = self.set('directory')

        # Set input dataset list.
        self.dataset_list = self.set('dataset_list')

        # Set input dataset ID.
        self.dataset_id = self.set('dataset_id')

        # Set input free directory.
        self.incoming = self.set('incoming')

        # Enable/disable checksumming process.
        self.no_checksum = self.set('no_checksum')

        # Read pre-computed checksums.
        self.checksums_from = self.set('checksums_from')

        # Checksums file takes priority on checksumming behavior setting.
        if self.checksums_from:
            self.no_checksum = True
            Print.warning('"--checksums-from" ignores "--no-checksum".')

        # Set multiprocessing configuration. Processes number is caped by cpu_count().
        self.processes = self.set('max_processes')

        # Sequential processing disables multiprocessing pool usage.
        self.use_pool = (self.processes != 1)

        # Instantiate data counter.
        self.nbsources = 0

        # Instantiate success counter.
        self.success = 0

        # Instantiate multiprocessing manager & set progress counter.
        if self.use_pool:
            # Multiprocessing manager starts within a multiprocessing pool only.
            self.manager = SyncManager()
            self.manager.start()

            # Instantiate print buffer.
            Print.BUFFER = self.manager.Value(c_wchar_p, '')

            # Instantiate progress counter.
            self.progress = self.manager.Value('i', 0)

            # Instantiate error counter.
            self.errors = self.manager.Value('i', 0)

            # Instantiate spinner message length.
            self.msg_length = self.manager.Value('i', 0)
        else:
            self.errors = Value('i', 0)
            self.progress = Value('i', 0)
            self.msg_length = Value('i', 0)

        # Instantiate stdout lock
        self.lock = Lock()

        # Discover a specified DRS version number.
        self.version = self.set('version')

        # Set directory filter.
        self.dir_filter = self.set('ignore_dir')

        # Set file filters.
        self.file_filter = list()
        if hasattr(args, 'include_files'):
            self.file_filter += [(f, True) for f in args.include_file]
        if hasattr(args, 'exclude_file'):
            self.file_filter += [(f, False) for f in args.exclude_file]

    def __enter__(self):
        super(MultiprocessingContext, self).__enter__()

        # Load project CV.
        Print.info('Loading CV')
        try:
            pyessv.load_cv(self.get_cv_authority(), self.project)
        except AssertionError:
            raise MissingCVdata(self.get_cv_authority(), self.project)

        # Get checksum client.
        self.checksum_type = self.get_checksum_type()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        # Build summary message.
        msg = 'Number of success(es): {}\n'.format(self.success)
        msg += 'Number of error(s): {}'.format(self.errors.value)

        # No errors occurred.
        if not self.errors.value:
            msg = COLORS.SUCCESS(msg)

        # All files skipped.
        elif self.nbsources == self.errors.value:
            msg = COLORS.FAIL(msg)

        # Partial success with at least one error.
        else:
            msg = COLORS.WARNING(msg)

        # Print summary.
        Print.summary(msg)

        super(MultiprocessingContext, self).__exit__(exc_type, exc_val, exc_tb)

    def get_checksum_type(self):
        """
        Returns the checksum type to use.

        """
        # Disabled checksumming returns None.
        if self.no_checksum:
            return None

        # Default set to sha256 checksum client.
        checksum_type = 'sha256'

        # Get checksum type from configuration.
        if 'checksum' in self.cfg.defaults():
            checksum_type = self.cfg.defaults()['checksum'].split('|')[1].strip().lower()

        # Verify checksum type is valid.
        if checksum_type not in checksum_types:
            raise InvalidChecksumType(checksum_type)

        return checksum_type

    def get_cv_authority(self):
        """
        Returns the CV authority to call pyessv.
        Default uses 'WCRP' CV.

        """
        try:
            return self.cfg.get(section='config:{}'.format(self.project), option='pyessv_authority')
        except (NoSectionError, NoOptionError):
            return 'wcrp'
