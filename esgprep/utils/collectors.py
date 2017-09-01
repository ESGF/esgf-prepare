#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to collect files from directories.

"""

# Module imports
import os
import re

from esgprep.utils.misc import match, remove


class Collector(object):
    """
    Base collector class to yield all regular NetCDF files.

    :param list sources: The list of sources to parse
    :param str file_filter: The regular expression to include files in the collection
    :returns: The data collector
    :rtype: *iter*

    """

    def __init__(self, sources, file_filter='^[!.].*\.nc$', data=None):
        self.sources = sources
        self.file_filter = file_filter
        self.data = data
        assert isinstance(self.sources, list)

    def __iter__(self):
        for source in self.sources:
            for root, _, filenames in os.walk(source, followlinks=True):
                for filename in filenames:
                    ffp = os.path.join(root, filename)
                    if os.path.isfile(ffp) and not match(self.file_filter, filename):
                        yield self.attach(ffp)

    def __len__(self):
        """
        Returns collector length.

        :returns: The number of items in the collector.
        :rtype: *int*

        """
        return sum(1 for _ in self.__iter__())

    def attach(self, item):
        """
        Attach a "data" object to the each item.

        :param str item: The iterator item.
        :returns: The item and the data
        :rtype: *tuple*

        """
        return (item, self.data) if self.data else item


class PathCollector(Collector):
    """
    Collector class to yield files from a list of directories to parse.

    :param str dir_filter: The regular expression to exclude directories from the collection

    """

    def __init__(self, *args, **kwargs):
        super(PathCollector, self).__init__(*args, **kwargs)
        self.PathFilter = self.PathFilter()

    def __iter__(self):
        """
        Yields files full path according to filters on path and filename.

        :returns: The collected file full paths
        :rtype: *iter*

        """
        for source in self.sources:
            for root, _, filenames in os.walk(source, followlinks=True):
                if self.PathFilter(root):
                    for filename in filenames:
                        ffp = os.path.join(root, filename)
                        if os.path.isfile(ffp) and not match(self.file_filter, filename):
                            yield self.attach(ffp)

    class PathFilter(dict):
        """
        Regex dictionary with a call method to evaluate a string against all regular expressions.
        The dictionary values are 2-tuples with the regular expression as a string and a boolean
        indicating to match or non-match the corresponding expression.

        """

        def __setitem__(self, key, value):
            # Assertions on filters values
            if isinstance(value, tuple):
                assert len(value) == 2
                assert isinstance(value[0], str)
                assert isinstance(value[1], bool)
            else:
                assert isinstance(value, str)
                # Set negative = False by default
                value = (value, False)
            dict.__setitem__(self, key, value)

        def __call__(self, path):
            return all([match(regex, path, negative=negative) for regex, negative in self.values()])


class VersionedPathCollector(PathCollector):
    """
    Collector class to yield files from a list of versioned directories to parse.

    :param str dir_format: The regular expression of the directory format

    """

    def __init__(self, dir_format, *args, **kwargs):
        super(VersionedPathCollector, self).__init__(*args, **kwargs)
        self.format = dir_format

    def __iter__(self):
        """
        Yields files full path according to filters on path and filename.

        :returns: The collected file full paths
        :rtype: *iter*

        """
        for source in self.sources:
            # Find if the version among path if exists
            source_version = self.version_finder(directory=source)
            if source_version:
                # Path version takes priority on command-line flags and default behavior
                # Overwrite the version filter
                self.PathFilter['version_filter'] = '/{}'.format(source_version)
            for root, _, filenames in os.walk(source, followlinks=True):
                # Reset version filter if latest_version exists to allow new filter for another dataset/version
                if 'latest_version' in locals():
                    try:
                        del self.PathFilter['version_filter']
                    except KeyError:
                        pass
                for filename in filenames:
                    ffp = os.path.join(root, filename)
                    path_version = self.version_finder(directory=root)
                    # If no version filter, and path version exists, set default behavior
                    if path_version and 'version_filter' not in self.PathFilter:
                        # Find latest version
                        path_versions = [v for v in os.listdir(ffp.split(path_version)[0]) if
                                         re.compile(r'^v[\d]+$').search(v)]
                        latest_version = sorted(path_versions)[-1]
                        # Pick up the latest version among encountered versions
                        self.PathFilter['version_filter'] = '/{}'.format(latest_version)
                    if self.PathFilter(root):
                        # Dereference latest symlink (only) in the end
                        if path_version == 'latest':
                            target = os.path.realpath(os.path.join(*re.split(r'/(latest)/', ffp)[:-1]))
                            ffp = os.path.join(target, *re.split(r'/(latest)/', ffp)[-1:])
                        if os.path.isfile(ffp) and not match(self.file_filter, filename):
                            yield self.attach(ffp)

    def version_finder(self, directory):
        regex = re.compile(self.format)
        version = None
        # Process directory_format regex without <filename> part
        while 'version' in regex.groupindex.keys():
            if regex.search(directory):
                # If version facet found return its value
                version = regex.search(directory).groupdict()['version']
                break
            else:
                # Walk backward the regex to find the version facet if exists
                regex = re.compile('/'.join(regex.pattern.split('/')[:-1]))
        return version


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
                    yield self.attach(remove('((\.v|#)[0-9]+)?\s*$', line))
