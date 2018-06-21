#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import logging
import re
import sys

from ESGConfigParser import SectionParser
from tqdm import tqdm

from constants import *
from esgprep.utils.collectors import PathCollector, DatasetCollector
from esgprep.utils.ctx_base import BaseContext


class ProcessingContext(BaseContext):
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
        self.any_undeclared = False

    def __enter__(self):
        # Init configuration parser
        self.cfg = SectionParser(section='project:{}'.format(self.project), directory=self.config_dir)
        # Init data collector
        if self.directory:
            # The source is a list of directories
            # Instantiate file collector to walk through the tree
            self.source_type = 'files'
            if self.pbar:
                self.sources = PathCollector(sources=self.directory)
            else:
                self.sources = PathCollector(sources=self.directory,
                                             spinner=False)
            # Init file filter
            for regex, inclusive in self.file_filter:
                self.sources.FileFilter.add(regex=regex, inclusive=inclusive)
            # Init dir filter
            self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)
            self.pattern = self.cfg.translate('directory_format', add_ending_filename=True)
        else:
            # The source is a list of files (i.e., several dataset lists)
            # Instantiate dataset collector to parse the files
            self.source_type = 'datasets'
            if self.pbar:
                self.sources = DatasetCollector(source=[x.strip() for x in self.dataset_list.readlines() if x.strip()],
                                                versioned=False)
            else:
                self.sources = DatasetCollector(source=[x.strip() for x in self.dataset_list.readlines() if x.strip()],
                                                spinner=False,
                                                versioned=False)
            self.pattern = self.cfg.translate('dataset_id')
        # Get the facet keys from pattern
        self.facets = set(re.compile(self.pattern).groupindex.keys()).difference(set(IGNORED_KEYS))
        # Init progress bar
        nfiles = len(self.sources)
        if self.pbar and nfiles:
            self.sources = tqdm(self.sources,
                                desc='Harvesting facets values from data',
                                total=nfiles,
                                bar_format='{desc}: {percentage:3.0f}% | {n_fmt}/{total_fmt} ' + self.source_type,
                                ncols=100,
                                file=sys.stdout)
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
