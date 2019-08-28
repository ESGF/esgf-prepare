# -*- coding: utf-8 -*-

"""
.. module:: esgprep._collectors.__init__.py
   :platform: Unix
   :synopsis: esgprep collector initializer.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from pathlib import Path
from typing import Pattern
from uuid import uuid4 as uuid

from esgprep._exceptions import NoFileFound
from esgprep._utils import match
from esgprep._utils.print import *


class Collector(object):
    """
    Base collector class to yield input sources.

    """

    def __init__(self, sources):

        # Get input sources.
        self.sources = sources
        assert isinstance(self.sources, list)

        # Instantiate filename filter.
        self.FileFilter = FilterCollection()

        # Instantiate path filter.
        self.PathFilter = FilterCollection()

    def __iter__(self):

        # StopIteration error means no files found in all input sources.
        try:

            # Iterate on input sources.
            for source in self.sources:

                # Walk through each source.
                for root, _, filenames in os.walk(source, followlinks=True):

                    # Source path can include hidden directories:
                    # So apply path filters on downstream tree only.
                    if self.PathFilter(root.split(source)[1]):

                        # Iterate on discovered sorted filenames.
                        for filename in sorted(filenames):

                            # Rebuild file full path aas pathlib.Path object.
                            path = Path(root, filename)

                            # Apply file filter on filename.
                            if path.is_file() and self.FileFilter(filename):
                                # Yield file full path.
                                yield path

        except StopIteration:
            raise NoFileFound(self.sources)


class FilterCollection(object):
    """
    Evaluates a string against a dictionary of several regular expressions.
    The dictionary includes 2-tuples with the regular expression as a string and a boolean
    indicating to match (i.e., include) or non-match (i.e., exclude) the corresponding expression.

    """
    FILTER_TYPES = (str, Pattern)

    def __init__(self):
        # Instantiate filters dictionary.
        self.filters = dict()

    def add(self, name=None, regex='*', inclusive=True):
        # Add new filter.
        if not name:
            name = str(uuid())
        assert isinstance(regex, self.FILTER_TYPES)
        assert isinstance(inclusive, bool)
        self.filters[name] = (regex, inclusive)

    def __call__(self, string):
        return all([match(regex, string, inclusive=inclusive) for regex, inclusive in self.filters.values()])
