# -*- coding: utf-8 -*-

"""
.. module:: esgprep._contexts.multiprocessing.py
   :platform: Unix
   :synopsis: Multiprocessing context.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import signal
from configparser import NoOptionError, NoSectionError
from ctypes import c_wchar_p
from hashlib import algorithms_available as checksum_types
from importlib import import_module
from multiprocessing import Lock, Pool
from multiprocessing.managers import BaseProxy, Namespace, SyncManager
from multiprocessing.sharedctypes import Value

import esgvoc.api as ev

from esgprep._contexts import BaseContext
from esgprep._exceptions import InvalidChecksumType, MissingCVdata
from esgprep._handlers.drs_tree import DRSTree
from esgprep._utils.print import COLORS, Print


class Manager(SyncManager):
    pass


class DRSTreeProxy(BaseProxy):
    _exposed_ = (
        "get_display_lengths",
        "add_path", 
        "append_path",
        "create_leaf",
        "has_path",
        "get_path",
        "get_path_value",
        "check_uniqueness",
        "list",
        "rmdir",
        "todo",
        "tree",
        "upgrade",
        "get_serializable_data",
        "restore_from_data",
    )

    def get_display_lengths(self):
        return self._callmethod("get_display_lengths")

    def add_path(self, key, value):
        return self._callmethod("add_path", (key, value))

    def append_path(self, key, what, value):
        return self._callmethod("append_path", (key, what, value))

    def create_leaf(self, nodes, label, src, mode, force=False):
        return self._callmethod("create_leaf", (nodes, label, src, mode, force))

    def has_path(self, key):
        return self._callmethod("has_path", (key,))

    def get_path(self, key):
        return self._callmethod("get_path", (key,))

    def get_path_value(self, key, field):
        return self._callmethod("get_path_value", (key, field))

    def check_uniqueness(self):
        return self._callmethod("check_uniqueness")

    def list(self, **kwargs):
        return self._callmethod("list", (), kwargs)

    def rmdir(self):
        return self._callmethod("rmdir")

    def todo(self, **kwargs):
        return self._callmethod("todo", (), kwargs)

    def tree(self, **kwargs):
        return self._callmethod("tree", (), kwargs)

    def upgrade(self, **kwargs):
        return self._callmethod("upgrade", (), kwargs)

    def get_serializable_data(self):
        return self._callmethod("get_serializable_data")

    def restore_from_data(self, data):
        return self._callmethod("restore_from_data", (data,))


Manager.register("DRSTree", DRSTree, DRSTreeProxy)


class MultiprocessingContext(BaseContext):
    """
    Base class for multiprocessing context manager.

    """

    def __init__(self, args):
        super(MultiprocessingContext, self).__init__(args)

        # Get sub-command line.
        self.cmd = self.set("cmd")

        # Set input action.
        self.action = self.set("action")

        # Set input DRS directory.
        self.directory = self.set("directory")

        # Set input dataset list.
        self.dataset = self.set("dataset_list")

        # Set input dataset ID.
        self.dataset = self.set("dataset_id")

        # Set input free directory.
        self.incoming = self.set("incoming")

        # Enable/disable checksumming process.
        self.no_checksum = self.set("no_checksum")

        # Set checksum type.
        self.checksum_type_arg = self.set("checksum_type")

        # Read pre-computed checksums.
        self.checksums_from = self.set("checksums_from")

        # Checksums file takes priority on checksumming behavior setting.
        if self.checksums_from:
            self.no_checksum = True
            Print.warning('"--checksums-from" ignores "--no-checksum".')

        # Set multiprocessing configuration. Processes number is caped by cpu_count().
        self.processes = self.set("max_processes")

        # Sequential processing disables multiprocessing pool usage.
        self.use_pool = self.processes != 1

        # Instantiate data counter.
        self.nbsources = 0

        # Instantiate success counter.
        self.success = 0

        # Instantiate multiprocessing manager & set progress counter.
        if self.use_pool:
            # Multiprocessing manager starts within a multiprocessing pool only.
            self.manager = Manager()
            self.manager.start()

            # Instantiate print buffer.
            Print.BUFFER = self.manager.Value(c_wchar_p, "")

            # Instantiate progress counter.
            self.progress = self.manager.Value("i", 0)

            # Instantiate error counter.
            self.errors = self.manager.Value("i", 0)

            # Instantiate spinner message length.
            self.msg_length = self.manager.Value("i", 0)

            # Instantiate stdout lock.
            self.lock = self.manager.Lock()
        else:
            self.errors = Value("i", 0)
            self.progress = Value("i", 0)
            self.msg_length = Value("i", 0)
            self.lock = Lock()

        # Discover a specified DRS version number.
        self.version = self.set("version")

        # Set directory filter.
        self.dir_filter = self.set("ignore_dir")

        # Set file filters.
        self.file_filter = list()
        if hasattr(args, "include_files"):
            self.file_filter += [(f, True) for f in args.include_file]
        if hasattr(args, "exclude_file"):
            self.file_filter += [(f, False) for f in args.exclude_file]

    def __enter__(self):
        super(MultiprocessingContext, self).__enter__()

        # Load project CV.
        Print.info("Loading CV")
        try:
            assert "institution" in ev.get_all_data_descriptors_in_universe()
        except AssertionError:
            raise MissingCVdata("esgvoc", "na")  # TODO improve error message

        # Get checksum client.
        self.checksum_type = self.get_checksum_type()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Build summary message.
        msg = f"Number of success(es): {self.success}\n"
        msg += f"Number of error(s): {self.errors.value}"

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

        # Get checksum type from command line argument or use default
        checksum_type = self.checksum_type_arg if hasattr(self, 'checksum_type_arg') and self.checksum_type_arg else "sha256"

        # Get checksum type from configuration.
        # if 'checksum' in self.cfg.defaults():
        #    checksum_type = self.cfg.defaults()['checksum'].split('|')[1].strip().lower()

        # Verify checksum type is valid.
        # Import multihash support here to avoid circular imports
        try:
            from esgprep._utils.checksum import is_multihash_algo
            if checksum_type not in checksum_types and not is_multihash_algo(checksum_type):
                raise InvalidChecksumType(checksum_type)
        except ImportError:
            # Fallback to original validation if multihash not available
            if checksum_type not in checksum_types:
                raise InvalidChecksumType(checksum_type)

        return checksum_type


class Runner(object):
    def __init__(self, processes):
        # Initialize the pool.
        self.pool = None

        if processes != 1:
            self.pool = Pool(processes=processes)

    def _handle_sigterm(self, signum, frame):
        # Properly kill the pool in case of SIGTERM.
        if self.pool:
            self.pool.terminate()

        os._exit(1)

    def run(self, sources, ctx):
        # Instantiate signal handler.
        sig_handler = signal.signal(signal.SIGTERM, self._handle_sigterm)

        # Import the appropriate worker.
        process = getattr(import_module(f"esgprep.{ctx.prog[3:]}.{ctx.cmd}"), "Process")

        # Convert sources to list for debugging
        sources_list = list(sources)
        Print.debug(f"Runner: Processing {len(sources_list)} sources")
        for i, source in enumerate(sources_list):
            Print.debug(f"Runner: Source {i}: {source}")

        # Instantiate pool of processes.
        if self.pool:
            # Instantiate pool iterator.
            processes = self.pool.imap(process(ctx), sources_list)

        # Sequential processing use basic map function.
        else:
            # Instantiate processes iterator.
            processes = map(process(ctx), sources_list)

        # Run processes & get the list of results.
        results = [x for x in processes]
        Print.debug(f"Runner: Got {len(results)} results: {results}")

        # Terminate pool in case of SIGTERM signal.
        signal.signal(signal.SIGTERM, sig_handler)

        # Close the pool.
        if self.pool:
            self.pool.close()
            self.pool.join()

        return results
