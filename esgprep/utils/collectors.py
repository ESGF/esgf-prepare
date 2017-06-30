#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to collect files from directories.

"""

# Module imports
import os
from esgprep.utils.utils import match, remove


class Collector(object):
    """
    Base collector class to yield all regular NetCDF files.

    """
    def __init__(self, sources):
        self.sources = sources
        assert isinstance(self.sources, list)

    def __iter__(self):
        for source in self.sources:
            for root, _, filenames in os.walk(source, followlinks=True):
                for filename in filenames:
                    ffp = os.path.join(root, filename)
                    if os.path.isfile(ffp) and not match('^[!.].*\.nc$', filename):
                        yield ffp

    def __len__(self):
        """
        Returns collector length.

        :returns: The number of items in the collector.
        :rtype: *int*

        """
        return sum(1 for _ in self.__iter__())


class PathCollector(Collector):
    """
    Collector class to yield files from a list of direcotries to parse.

    """
    def __init__(self, directories, dir_filter='^.*/(files|latest|\.[\w]*).*$', file_filter='^[!.].*\.nc$'):
        super(PathCollector, self).__init__(directories)
        self.dir_filter = dir_filter
        self.file_filter = file_filter

    def __iter__(self):
        """
        Yields files full path NON-matching the directory filter but matching the file filter.

        :returns: The collected file full paths
        :rtype: *iter*

        """
        for source in self.sources:
            for root, _, filenames in os.walk(source, followlinks=True):
                if not match(self.dir_filter, root):
                    for filename in filenames:
                        ffp = os.path.join(root, filename)
                        if os.path.isfile(ffp) and not match(self.file_filter, filename):
                            yield ffp


    #TODO: Add version finder on path for mapfile walker


class DatasetCollector(Collector):
    """
    Collector class to yield datasets from a list of files to read.

    """
    def __iter__(self):
        """
        Yields datasets to process from a text file. Each line may contain the dataset with optional
        appended ``.v<version>`` or ``#<version>`, and only the part without the version is returned.

        :returns: The dataset ID without `he version
        :rtype: *iter*

        """
        for source in self.sources:
            with open(source) as f:
                for line in f:
                    yield remove('((\.v|#)[0-9]+)?\s*$', line)
