# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from esgprep._collectors import Collector
from esgprep._collectors.dataset_id import DatasetCollector
from esgprep._collectors.drs_path import DRSPathCollector
from esgprep._contexts.multiprocessing import MultiprocessingContext


class ProcessingContext(MultiprocessingContext):
    """
    Processing context class to drive main process.

    """

    def __init__(self, args):
        super(ProcessingContext, self).__init__(args)

    def __enter__(self):
        super(ProcessingContext, self).__enter__()

        # Instantiate data collector.
        # The input source is a list directories.
        if self.directory:

            # Instantiate file collector to walk through the tree.
            self.sources = DRSPathCollector(sources=self.directory)

            # Initialize file filter.
            for regex, inclusive in self.file_filter:
                self.sources.FileFilter.add(regex=regex, inclusive=inclusive)

            # Initialize directory filter.
            self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)

        # The source is a list of files (potentially from stdin).
        elif self.incoming:

            # Instantiate file collector to walk through the tree.
            self.sources = Collector(sources=self.incoming)

            # Initialize file filters.
            for regex, inclusive in self.file_filter:
                self.sources.FileFilter.add(regex=regex, inclusive=inclusive)

            # Initialize directory filter.
            self.sources.PathFilter.add(regex=self.dir_filter, inclusive=False)

        # The input source is a list of dataset identifiers (potentially from stdin).
        else:

            # Instantiate dataset collector.
            self.sources = DatasetCollector(sources=self.dataset)

        return self
