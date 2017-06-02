#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Class to handle files for mapfile generation.

"""

import os
import re

from esgprep.mapfile.exceptions import *
from esgprep.utils.constants import *
from esgprep.utils.exceptions import *
from ConfigParser import InterpolationMissingOptionError


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

    def load_attributes(self, ctx):
        """
        The DRS attributes are deduced from the file full path using
        the directory_format regex pattern. The project facet is added in any case with lower case.

         * Matches file full path with corresponding project pattern to get DRS attributes values
         * attributes.keys() are facet names
         * attributes[facet] is the facet values.

        :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
        :raises Error: If the file full path does not match the ``directory_format`` pattern/regex

        """
        try:
            # re.search() method is required to search through the entire string.
            # In this case we aim to match the regex starting from the filename (i.e., the end of the string)
            self.attributes = re.search(ctx.pattern, self.ffp).groupdict()
            # Only required to build proper dataset_id
            self.attributes['project'] = ctx.project.lower()
        except:
            raise DirectoryNotMatch(self.ffp, ctx.pattern, ctx.project_section, ctx.cfg.read_paths)

    def get_dataset_id(self, ctx):
        """
        Builds the dataset identifier. If the dataset name is not specified (i.e., --dataset flag is None), it:

         * Checks each value which the facet is found in dataset_id AND attributes keys,
         * Gets missing attributes from the maptables in the esg.<project>.ini,
         * Builds the dataset identifier from the attributes.

        :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
        :returns: The dataset identifier
        :rtype: *str*
        :raises Error: If a facet cannot be checked

        """
        # Check each facet required by the dataset_id template from esg.<project>.ini
        # Facet values to check are deduced from file full-path
        # If a DRS attribute is missing regarding the dataset_id template,
        # the DRS attributes are completed from esg.<project>.ini maptables.
        # If default keys has to be resolved through ini instead of ignored: remove it from the IGNORED_KEYS list
        ignored_keys = set(IGNORED_KEYS) - set(ctx.not_ignored)
        if not ctx.dataset:
            for facet in set(ctx.facets).intersection(self.attributes.keys()) - ignored_keys:
                ctx.cfg.check_options(ctx.project_section, {facet: self.attributes[facet]})
            for facet in set(ctx.facets).difference(self.attributes.keys()) - ignored_keys:
                try:
                    self.attributes[facet] = ctx.cfg.get_option_from_map(ctx.project_section,
                                                                         '{0}_map'.format(facet),
                                                                         self.attributes)
                except:
                    raise NoConfigVariable(facet,
                                           ctx.cfg.get(ctx.project_section, 'directory_format', raw=True).strip(),
                                           ctx.project_section,
                                           ctx.cfg.read_paths)
            try:
                dataset_id = ctx.cfg.get(ctx.project_section, 'dataset_id', 0, self.attributes)
            except InterpolationMissingOptionError:
                raise MissingPatternKey(self.attributes.keys(),
                                        ctx.cfg.get(ctx.project_section, 'dataset_id', 1),
                                        ctx.project_section,
                                        ctx.cfg.read_paths)
        else:
            dataset_id = ctx.dataset
        return dataset_id

    def get_dataset_version(self, ctx):
        """
        Retrieve the dataset version. If the version facet cannot be deduced from full path
        (e.g., with --latest-symlink flag), it follows the symlink to complete the DRS attributes.

        :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
        :returns: The dataset version
        :rtype: *str*

        """
        if 'version' in self.attributes and not ctx.no_version:
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
        if not checksum_client:
            return None
        try:
            shell = os.popen("{0} {1} | awk -F ' ' '{{ print $1 }}'".format(checksum_client, self.ffp))
            return shell.readline()[:-1]
        except:
            raise ChecksumFail(self.ffp, checksum_type)
