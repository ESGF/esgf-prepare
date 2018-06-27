#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from constants import *
from esgprep.utils.collectors import PathCollector, DatasetCollector, Collector
from esgprep.utils.context import MultiprocessingContext
from esgprep.utils.custom_print import *


class ProcessingContext(MultiprocessingContext):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: The command-line arguments parser
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        super(ProcessingContext, self).__init__(args)
        # True if undeclared facets
        self.any_undeclared = False
        # Add sources values to process manager
        if self.use_pool:
            self.source_values = self.manager.dict({})
        else:
            self.source_values = dict()

    def __enter__(self):
        super(ProcessingContext, self).__enter__()
        # Get the DRS facet keys from pattern
        self.facets = list()
        self.facets = re.compile(self.cfg.translate('directory_format', add_ending_filename=True)).groupindex.keys()
        self.facets.extend(re.compile(self.cfg.translate('dataset_id')).groupindex.keys())
        self.facets = set(self.facets).difference(set(IGNORED_KEYS))
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
        return self
