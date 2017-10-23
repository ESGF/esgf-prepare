#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to collect data from directories.

"""

import os
import re
import sys

from esgprep.utils.misc import match, remove


class Collecting:
    """
    Spinner pending data collection.

    """
    STATES = ('/', '-', '\\', '|')
    step = 0

    def __init__(self):
        self.next()

    def next(self):
        """
        Print collector spinner

        """
        sys.stdout.write('\rCollecting data... {}'.format(Collecting.STATES[Collecting.step % 4]))
        sys.stdout.flush()
        Collecting.step += 1


class Collector(object):
    """
    Base collector class to yield regular NetCDF files.

    :param list sources: The list of sources to parse
    :param object data: Any object to attach to each collected data
    :returns: The data collector
    :rtype: *iter*

    """

    def __init__(self, sources, data=None):
        self.sources = sources
        self.data = data
        self.FileFilter = Filter()
        assert isinstance(self.sources, list)

    def __iter__(self):
        for source in self.sources:
            for root, _, filenames in os.walk(source, followlinks=True):
                for filename in sorted(filenames):
                    ffp = os.path.join(root, filename)
                    if os.path.isfile(ffp) and self.FileFilter(filename):
                        yield self.attach(ffp)

    def __len__(self):
        """
        Returns collector length with animation.

        :returns: The number of items in the collector.
        :rtype: *int*

        """
        progress = Collecting()
        s = 0
        for _ in self.__iter__():
            progress.next()
            s += 1
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()
        return s

    def attach(self, item):
        """
        Attach any object to the each collector item.

        :param str item: The collector item
        :returns: The collector item with the "data" object
        :rtype: *tuple*

        """
        return (item, self.data) if self.data else item

    def first(self):
        """

        :return:
        """
        return self.__iter__().next()


class PathCollector(Collector):
    """
    Collector class to yield files from a list of directories to parse.

    :param str dir_filter: A regular expression to exclude directories from the collection

    """

    def __init__(self, *args, **kwargs):
        super(PathCollector, self).__init__(*args, **kwargs)
        self.PathFilter = Filter()

    def __iter__(self):
        """
        Yields files full path according to filters on path and filename.

        :returns: The collected file full paths
        :rtype: *iter*

        """
        for source in self.sources:
            for root, _, filenames in os.walk(source, followlinks=True):
                if self.PathFilter(root):
                    for filename in sorted(filenames):
                        ffp = os.path.join(root, filename)
                        if os.path.isfile(ffp) and self.FileFilter(filename):
                            yield self.attach(ffp)


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
                for filename in sorted(filenames):
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
                        if os.path.isfile(ffp) and self.FileFilter(filename):
                            yield self.attach(ffp)

    def version_finder(self, directory):
        """
        Returns the version number find into a DRS path
        :param str directory: The directory to parse
        :returns: The version
        :rtype: *str*

        """
        regex = re.compile(self.format)
        version = None
        # Test directory_format regex without <filename> part
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

        :returns: The dataset ID without the version
        :rtype: *iter*

        """
        for source in self.sources:
            with open(source) as f:
                for line in f:
                    yield self.attach(remove('((\.v|#)[0-9]+)?\s*$', line))


class Filter(dict):
    """
    Regex dictionary with a call method to evaluate a string against several regular expressions.
    The dictionary values are 2-tuples with the regular expression as a string and a boolean
    indicating to match (i.e., include) or non-match (i.e., exclude) the corresponding expression.

    """
    FILTER_TYPES = (str, re._pattern_type)

    def __setitem__(self, key, value):
        # Assertions on filters values
        if isinstance(value, tuple):
            assert len(value) == 2
            assert isinstance(value[0], self.FILTER_TYPES)
            assert isinstance(value[1], bool)
        else:
            assert isinstance(value, str)
            # Set negative = False by default
            value = (value, False)
        dict.__setitem__(self, key, value)

    def __call__(self, string):
        return all([match(regex, string, negative=negative) for regex, negative in self.values()])
