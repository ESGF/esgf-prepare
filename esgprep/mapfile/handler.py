#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Class to handle files for mapfile generation.

"""

import os
import re

from ESGConfigParser import interpolate
from ESGConfigParser.custom_exceptions import ExpressionNotMatch, NoConfigOption, MissingPatternKey

from constants import *
from esgprep.utils.custom_exceptions import *
from esgprep.utils.misc import checksum


class Source(object):
    """
    Handler providing methods to deal with file processing.

    """

    def __init__(self, source):
        # Retrieve source
        self.source = source
        # File attributes as dict(): {institute: 'IPSL', project : 'CMIP5', ...}
        self.attributes = {}

    def get(self, key):
        """
        Returns the attribute value corresponding to the key.
        The submitted key can refer to ``File.key`` or ``File.attributes[key]``.

        :param str key: The key
        :returns: The corresponding value
        :rtype: *str* or *list* or *dict* depending on the key
        :raises Error: If unknown key

        """
        if key in self.attributes:
            return self.attributes[key]
        elif key in self.__dict__.keys():
            return self.__dict__[key]
        else:
            raise KeyNotFound(key, self.attributes.keys() + self.__dict__.keys())

    def load_attributes(self, pattern):
        """
        Loads DRS attributes catched from a regular expression match.
        The project facet is added in any case with lower case.

        :param str pattern: The regular expression to match
        :raises Error: If regular expression matching fails

        """
        try:
            # re.search() method is required to search through the entire string.
            # In this case we aim to match the regex starting from the filename (i.e., the end of the string)
            self.attributes = re.search(pattern, self.source).groupdict()
        except:
            raise ExpressionNotMatch(self.source, pattern)

    def check_facets(self, facets, config):
        """
        Checks each facet against the controlled vocabulary.
        If a DRS attribute is missing regarding the list of facets,
        the DRS attributes are completed from the configuration file maptables.

        :param list facets: The list of facet to check
        :param ESGConfigParser.SectionParser config: The configuration parser
        :raises Error: If one facet checkup fails

        """
        for facet in set(facets).intersection(self.attributes.keys()) - set(IGNORED_KEYS):
            config.check_options({facet: self.attributes[facet]})
        for facet in set(facets).difference(self.attributes.keys()) - set(IGNORED_KEYS):
            try:
                self.attributes[facet] = config.get_option_from_map('{}_map'.format(facet), self.attributes)
            except:
                raise NoConfigOption('{}_map'.format(facet))

    def get_dataset_id(self, dataset_format):
        """
        Builds the dataset identifier from the dataset template interpolation.

        :param str dataset_format: The dataset template pattern
        :returns: The resulting dataset identifier
        :rtype: *str*
        :raises Error: If a facet key is missing

        """
        try:
            return interpolate(dataset_format, self.attributes)
        except:
            raise MissingPatternKey(self.attributes.keys(), dataset_format)

    def get_dataset_version(self, no_version=False):
        """
        Retrieve the dataset version. If the version facet cannot be deduced from full path,
        it follows the symlink to complete the DRS attributes.

        :param boolean no_version: True to not append version to the dataset ID
        :returns: The dataset version
        :rtype: *str*

        """
        if 'version' in self.attributes and not no_version:
            return self.get('version')
        else:
            return None


class Dataset(Source):
    """
    Dataset handler class

    """

    def __init__(self, *args, **kwargs):
        super(Dataset, self).__init__(*args, **kwargs)


class File(Source):
    """
    File handler class

    """

    def __init__(self, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)
        # Retrieve file size
        self.size = os.stat(self.source).st_size
        # Retrieve file mtime
        self.mtime = os.stat(self.source).st_mtime

    def checksum(self, checksum_type):
        """
        Does the checksum by the Shell avoiding Python memory limits.

        :param str checksum_type: Checksum type
        :returns: The checksum
        :rtype: *str*
        :raises Error: If the checksum fails

        """
        return checksum(self.source, checksum_type)
