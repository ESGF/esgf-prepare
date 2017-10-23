#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import logging
import re
import sys
from uuid import uuid4 as uuid

from ESGConfigParser import SectionParser

from constants import *
from esgprep.utils.collectors import PathCollector, DatasetCollector
from esgprep.utils.misc import as_pbar


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: The command-line arguments parser
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.pbar = args.pbar
        self.project = args.project
        self.config_dir = args.i
        self.directory = args.directory
        self.dataset_list = args.dataset_list
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
        self.scan_errors = 0
        self.any_undeclared = False

    def __enter__(self):
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        # Init data collector
        if self.directory:
            # The source is a list of directories
            # Instantiate file collector to walk through the tree
            self.source_type = 'files'
            self.sources = PathCollector(sources=self.directory)
            # Init file filter
            for file_filter in self.file_filter:
                self.sources.FileFilter[uuid()] = file_filter
            # Init dir filter
            self.sources.PathFilter['base_filter'] = (self.dir_filter, True)
            self.pattern = self.cfg.translate('directory_format', filename_pattern=True)
        else:
            # The source is a list of files (i.e., several dataset lists)
            # Instantiate dataset collector to parse the files
            self.source_type = 'datasets'
            self.sources = DatasetCollector(self.dataset_list)
            self.pattern = self.cfg.translate('dataset_id')
        # Get the facet keys from pattern
        self.facets = set(re.compile(self.pattern).groupindex.keys()).difference(set(IGNORED_KEYS))
        # Init progress bar
        if self.pbar:
            self.sources = as_pbar(self.sources, desc='Harvesting facets values from source', units=self.source_type)
        return self

    def __exit__(self, *exc):
        # Default is sys.exit(0)
        if self.scan_errors > 0:
            print('{}: {} (see {})'.format('Scan errors',
                                           self.scan_errors,
                                           logging.getLogger().handlers[0].baseFilename))
            sys.exit(1)
        if self.any_undeclared:
            print('Please update "esg.{}.ini" following: {}'.format(self.project,
                                                                    logging.getLogger().handlers[0].baseFilename))
            sys.exit(2)
