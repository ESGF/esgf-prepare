#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to collect data from directories.

"""

import os
import re
import sys
from uuid import uuid4 as uuid

from esgprep.utils.custom_exceptions import NoFileFound
from esgprep.utils.misc import match, remove


class Collecting:
    """
    Spinner pending data collection.

    """
    STATES = ('/', '-', '\\', '|')
    step = 0

    def __init__(self, spinner):
        self.spinner = spinner
        self.next()

    def next(self):
        """
        Print collector spinner

        """
        if self.spinner:
            sys.stdout.write('\rCollecting data... {}'.format(Collecting.STATES[Collecting.step % 4]))
            sys.stdout.flush()
        Collecting.step += 1


class Collector(object):
    """
    Base collector class to yield regular NetCDF files.

    :param list sources: The list of sources to parse
    :returns: The data collector
    :rtype: *iter*

    """

    def __init__(self, sources, spinner=True):
        self.spinner = spinner
        self.sources = sources
        self.FileFilter = FilterCollection()
        self.PathFilter = FilterCollection()
        assert isinstance(self.sources, list)

    def __iter__(self):
        for source in self.sources:
            for root, _, filenames in os.walk(source, followlinks=True):
                # Apply path filters only on recursion
                # Source path can include hidden directories
                if self.PathFilter(root.split(source)[1]):
                    for filename in sorted(filenames):
                        ffp = os.path.join(root, filename)
                        if os.path.isfile(ffp) and self.FileFilter(filename):
                            yield ffp

    def __len__(self):
        """
        Returns collector length with animation.

        :returns: The number of items in the collector.
        :rtype: *int*

        """
        progress = Collecting(self.spinner)
        try:
            s = 0
            for _ in self.__iter__():
                progress.next()
                s += 1
            if self.spinner:
                sys.stdout.write('\r\033[K')
                sys.stdout.flush()
        except StopIteration:
            raise NoFileFound(self.sources)
        return s


class PathCollector(Collector):
    """
    Collector class to yield files from a list of directories to parse.

    :param str dir_filter: A regular expression to exclude directories from the collection

    """

    def __init__(self, *args, **kwargs):
        super(PathCollector, self).__init__(*args, **kwargs)

    def __iter__(self):
        """
        Yields files full path according to filters on path and filename.

        :returns: The collected file full paths
        :rtype: *iter*

        """
        for source in self.sources:
            for root, _, filenames in os.walk(source, followlinks=True):
                if self.PathFilter(root.split(source)[1]):
                    for filename in sorted(filenames):
                        ffp = os.path.join(root, filename)
                        if os.path.isfile(ffp) and self.FileFilter(filename):
                            yield ffp


class VersionedPathCollector(PathCollector):
    """
    Collector class to yield files from a list of versioned directories to parse.

    :param str dir_format: The regular expression of the directory format

    """

    def __init__(self, project, dir_format, *args, **kwargs):
        super(VersionedPathCollector, self).__init__(*args, **kwargs)
        self.project = project
        self.format = dir_format
        self.default = False

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
                # Set default behavior to false
                self.default = False
                # And overwrite the version filter
                self.PathFilter.add(name='version_filter', regex='/{}'.format(source_version))
            for root, _, filenames in os.walk(source, followlinks=True):
                for filename in sorted(filenames):
                    ffp = os.path.join(root, filename)
                    path_version = self.version_finder(directory=root)
                    # If no version filter, and path version exists, set default behavior
                    if path_version and self.default:
                        # Find latest version
                        path_versions = [v for v in os.listdir(ffp.split(path_version)[0]) if
                                         re.compile(r'^v[\d]+$').search(v)]
                        latest_version = sorted(path_versions)[-1]
                        # Pick up the latest version among encountered versions
                        self.PathFilter.add(name='version_filter', regex='/{}'.format(latest_version))
                    if self.PathFilter(root):
                        # if self.PathFilter(root.split(source)[1]):
                        # Dereference latest symlink (only) in the end
                        if path_version == 'latest':
                            # Keep parentheses in pattern to get "latest" part of the split list
                            target = os.path.realpath(os.path.join(*re.split(r'/(latest)/', ffp)[:-1]))
                            ffp = os.path.join(target, *re.split(r'/(latest)/', ffp)[-1:])
                        if os.path.isfile(ffp) and self.FileFilter(filename):
                            yield ffp

    def version_finder(self, directory):
        """
        Returns the version number find into a DRS path
        :param str directory: The directory to parse
        :returns: The version
        :rtype: *str*

        """
        # Replace project regex by its expected lower-cased value
        # This is to get an anchor in the regex
        # This ensure to capture the right version group in the directory format if exists in the directory input
        regex = re.compile(self.format.replace('/(?P<project>[\w.-]+)/', '/{}/'.format(self.project.lower())))
        version = None
        # Test directory_format regex without <filename> part
        while 'version' in regex.groupindex.keys():
            if regex.search(directory.lower()):
                # If version facet found return its value
                version = regex.search(directory.lower()).groupdict()['version']
                break
            else:
                # Walk backward the regex to find the version facet if exists
                regex = re.compile('/'.join(regex.pattern.split('/')[:-1]))
        return version


class DatasetCollector(Collector):
    """
    Collector class to yield datasets from a list of files to read.

    """

    def __init__(self, versioned=True, *args, **kwargs):
        super(DatasetCollector, self).__init__(*args, **kwargs)
        self.versioned = versioned

    def __iter__(self):
        """
        Yields datasets to process from a text file. Each line may contain the dataset with optional
        appended ``.v<version>`` or ``#<version>`, and only the part without the version is returned.

        :returns: The dataset ID without the version
        :rtype: *iter*

        """
        for source in self.sources:
            if self.versioned:
                yield source
            else:
                yield remove('((\.v|#)[0-9]+)?\s*$', source)


class FilterCollection(object):
    """
    Regex dictionary with a call method to evaluate a string against several regular expressions.
    The dictionary values are 2-tuples with the regular expression as a string and a boolean
    indicating to match (i.e., include) or non-match (i.e., exclude) the corresponding expression.

    """
    FILTER_TYPES = (str, re._pattern_type)

    def __init__(self):
        self.filters = dict()

    def add(self, name=None, regex='*', inclusive=True):
        """Add new filter"""
        if not name:
            name = str(uuid())
        assert isinstance(regex, self.FILTER_TYPES)
        assert isinstance(inclusive, bool)
        self.filters[name] = (regex, inclusive)

    def __call__(self, string):
        return all([match(regex, string, inclusive=inclusive) for regex, inclusive in self.filters.values()])
