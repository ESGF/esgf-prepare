#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Class to handle files for mapfile generation.

"""

import os
import re

from esgprep.utils.utils import checksum
from esgprep.utils.config import interpolate
from esgprep.utils.constants import *
from esgprep.utils.exceptions import *


class File(object):
    """
    Handler providing methods to deal with file processing.

    """

    def __init__(self, ffp):
        # Retrieve file full path
        self.ffp = ffp
        # File attributes as dict(): {institute: 'IPSL', project : 'CMIP5', ...}
        self.attributes = {}
        # Retrieve file size
        self.size = os.stat(self.ffp).st_size
        # Retrieve file mtime
        self.mtime = os.stat(self.ffp).st_mtime

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

    def load_attributes(self, project, pattern):
        """
        The DRS attributes are deduced from the file full path using
        the directory_format regex pattern. The project facet is added in any case with lower case.

        :param str project: The project name
        :param str pattern: The ``directory_format`` pattern/regex
        :raises Error: If the file full path does not match the ``directory_format`` pattern/regex

        """
        try:
            # re.search() method is required to search through the entire string.
            # In this case we aim to match the regex starting from the filename (i.e., the end of the string)
            self.attributes = re.search(pattern, self.ffp).groupdict()
            # Only required to build proper dataset_id
            self.attributes['project'] = project.lower()
        except:
            raise ExpressionNotMatch(self.ffp, pattern)

    def check_facets(self, facets, not_ignored, config):
        """
        Checks each facet against the esg.<project>.ini
        If a DRS attribute is missing regarding the dataset_id template,
        the DRS attributes are completed from esg.<project>.ini maptables.
        If some keys has to be resolved through ini instead of ignored: remove it from the IGNORED_KEYS list

        :param list facets: The list of facet to check
        :param list not_ignored: The list of facet to not ignore
        :param esgprep.utils.config.SectionParser config: The configuration parser
        :raises Error: If one facet checkup fails

        """
        ignored_keys = set(IGNORED_KEYS) - set(not_ignored)
        for facet in set(facets).intersection(self.attributes.keys()) - ignored_keys:
            config.check_options({facet: self.attributes[facet]})
        for facet in set(facets).difference(self.attributes.keys()) - ignored_keys:
            try:
                self.attributes[facet] = config.get_option_from_map('{}_map'.format(facet), self.attributes)
            except:
                raise NoConfigOptions(facet)

    def get_dataset_id(self, dataset_format):
        """
        Builds the dataset identifier from ``dataset_format`` interpolation.

        :param str dataset_format: The ``dataset_id`` pattern/regex
        :returns: The dataset identifier
        :rtype: *str*
        :raises Error: If a facet key is missing

        """
        try:
            return interpolate(dataset_format, self.attributes)
        except:
            raise MissingPatternKey(self.attributes.keys(), dataset_format)

    def get_dataset_version(self, no_version=False):
        """
        Retrieve the dataset version. If the version facet cannot be deduced from full path
        (e.g., with --latest-symlink flag), it follows the symlink to complete the DRS attributes.

        :param boolean no_version: True to not append version to the dataset ID
        :returns: The dataset version
        :rtype: *str*

        """
        if 'version' in self.attributes and not no_version:
            return self.get('version')
        else:
            return None

    def checksum(self, checksum_type, checksum_client):
        """
        Does the checksum by the Shell avoiding Python memory limits.

        :param str checksum_client: Shell command line for checksum
        :param str checksum_type: Checksum type
        :returns: The checksum
        :rtype: *str*
        :raises Error: If the checksum fails

        """
        return checksum(self.ffp, checksum_type, checksum_client)
