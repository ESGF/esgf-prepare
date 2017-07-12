#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import logging
import re
import sys

from tqdm import tqdm

from esgprep.utils.collectors import PathCollector, DatasetCollector
from esgprep.utils.config import SectionParser
from esgprep.utils.constants import *


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.pbar = args.pbar
        self.project = args.project
        self.config_dir = args.i
        self.directory = args.directory
        self.dataset_list = args.dataset_list
        self.dir_filter = args.ignore_dir_filter
        self.file_filter = args.include_file_filter
        self.scan_errors = 0
        self.any_undeclared = False

    def __enter__(self):
        # Init configuration parser
        self.cfg = SectionParser(self.config_dir, section='project:{}'.format(self.project))
        # Init data collector
        if self.directory:
            # The source is a list of directories
            # Instantiate file collector to walk through the tree
            self.source_type = 'files'
            self.sources = PathCollector(sources=self.directory,
                                         dir_filter=self.dir_filter,
                                         file_filter=self.file_filter)
            self.pattern = self.cfg.translate('directory_format')
        else:
            # The source is a list of files (i.e., several dataset lists)
            # Instantiate dataset collector to parse the files
            self.source_type = 'datasets'
            self.sources = DatasetCollector(self.dataset_list)
            self.pattern = self.cfg.translate('dataset_id')
        # Get the facet keys from pattern
        self.facets = set(re.compile(self.pattern).groupindex.keys()).difference(set(IGNORED_KEYS))
        # Init progress bar
        self.sources = self.make_pbar(self.sources)
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

    def make_pbar(self, iterable):
        """
        Build progress pbar if desired

        :returns: The progress bar object as a list
        :rtype: *tqdm.tqdm* or *iter*

        """
        if self.pbar:
            return tqdm(iterable,
                        desc='Harvesting facets values from source',
                        total=len(iterable),
                        bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} ' + self.source_type,
                        ncols=100,
                        unit='files',
                        file=sys.stdout)
        else:
            return iterable
