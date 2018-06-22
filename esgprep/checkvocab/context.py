#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import re
from ctypes import c_char_p
from multiprocessing import Value, Lock, cpu_count
from multiprocessing.managers import SyncManager

from ESGConfigParser import SectionParser
from constants import *
from esgprep.utils.collectors import PathCollector, DatasetCollector, Collector
from esgprep.utils.misc import COLORS, Print


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: The command-line arguments parser
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.project = args.project
        self.config_dir = args.i
        self.directory = args.directory
        # stdin is always opened by argparse so never None
        self.dataset_list = args.dataset_list
        self.dataset_id = args.dataset_id
        self.incoming = args.incoming
        self.processes = args.max_processes if args.max_processes <= cpu_count() else cpu_count()
        self.use_pool = (self.processes != 1)
        self.set_keys = {}
        if args.set_key:
            self.set_keys = dict(args.set_key)
        self.dir_filter = args.ignore_dir
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
        self.scan_errors = 0
        self.scan_data = 0
        self.any_undeclared = False
        # Init process manager
        if self.use_pool:
            manager = SyncManager()
            manager.start()
            self.progress = manager.Value('i', 0)
            self.source_values = manager.dict({})
            Print.BUFFER = manager.Value(c_char_p, '')
        else:
            self.progress = Value('i', 0)
            self.source_values = dict()
        self.lock = Lock()

    def __enter__(self):
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        # Init data collector
        if self.directory:
            # The source is a list of directories
            self.source_type = 'file'
            self.sources = PathCollector(sources=self.directory)
            # Init file filter
            for regex, inclusive in self.file_filter:
                self.sources.FileFilter.add(regex=regex, inclusive=inclusive)
            # Init dir filter
            self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)
            self.pattern = self.cfg.translate('directory_format', add_ending_filename=True)
        elif self.incoming:
            # The source is a dataset ID (potentially from stdin)
            self.source_type = 'file'
            self.sources = Collector(sources=self.incoming)
            # Init file filter
            for regex, inclusive in self.file_filter:
                self.sources.FileFilter.add(regex=regex, inclusive=inclusive)
            # Init dir filter
            self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)
            # Translate dataset_id format
            self.pattern = self.cfg.translate('filename_format')
        elif self.dataset_id:
            # The source is a dataset ID (potentially from stdin)
            self.source_type = 'dataset'
            self.sources = DatasetCollector(sources=[self.dataset_id], versioned=False)
            # Translate dataset_id format
            self.pattern = self.cfg.translate('dataset_id')
        else:
            # The source is a list of files (i.e., several dataset lists)
            # Has to be tested at the end because args.dataset_list never None, see __init__ comment.
            self.source_type = 'dataset'
            self.sources = DatasetCollector(sources=[x.strip() for x in self.dataset_list.readlines() if x.strip()],
                                            versioned=False)
            self.pattern = self.cfg.translate('dataset_id')
        # Get number of sources
        self.nbsources = len(self.sources)
        # Get the facet keys from patterns
        self.facets = list()
        self.facets = re.compile(self.cfg.translate('directory_format', add_ending_filename=True)).groupindex.keys()
        self.facets.extend(re.compile(self.cfg.translate('dataset_id')).groupindex.keys())
        self.facets = set(self.facets).difference(set(IGNORED_KEYS))
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        # Decline outputs depending on the scan results
        if self.nbsources == self.scan_data:
            # All files have been successfully scanned without errors
            msg = COLORS.OKGREEN
        elif self.nbsources == self.scan_errors:
            # All files have been skipped with errors
            msg = COLORS.FAIL
        else:
            # Some files have been scanned with at least one error
            msg = COLORS.WARNING
        msg += 'Number of {} scanned: {}\n'.format(SOURCE_TYPE[self.source_type], self.scan_data)
        msg += 'Number of errors: {}'.format(self.scan_errors)
        msg += COLORS.ENDC
        # Print summary
        Print.summary(msg)
        # Print log path if exists
        Print.log(Print.LOGFILE)
