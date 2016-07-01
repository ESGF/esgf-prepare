#!/usr/bin/env python

import os
import re
import logging
from esgprep.utils import parser


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

        """
        if key in self.attributes:
            return self.attributes[key]
        elif key in self.__dict__.keys():
            return self.__dict__[key]
        else:
            raise Exception('{0} not found. Available keys '
                            'are {1}'.format(key, self.attributes.keys() + self.__dict__.keys()))

    def load_attributes(self, ctx):
        """
        The DRS attributes are deduced from the file full path using
        the directory_format regex pattern. The project facet is added in any case with lower case.

         * Matches file full path with corresponding project pattern to get DRS attributes values
         * attributes.keys() are facet names
         * attributes[facet] is the facet value.

        :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
        :raises Error: If the file full path does not match the ``directory_format`` pattern/regex

        """
        try:
            self.attributes = re.match(ctx.pattern, self.ffp).groupdict()
            self.attributes['project'] = ctx.project.lower()
            # If file path is a symlink, deduce the version following the symlink
            if ctx.latest:
                pointed_path = os.path.realpath(''.join(re.split(r'(latest)', self.ffp)[:-1]))
                self.attributes['version'] = os.path.basename(pointed_path)
        except:
            msg = 'Matching failed to deduce DRS attributes from {0}. Please check the ' \
                  '"directory_format" regex in the [project:{1}] section.'.format(self.ffp, ctx.project)
            logging.warning(msg)
            raise Exception(msg)

    def get_dataset_id(self, ctx):
        """
        Builds the dataset identifier. If the dataset name is not specified (i.e., --dataset flag is None), it:

         * Checks each value which the facet is found in dataset_id AND attributes keys,
         * Gets missing attributes from the maptables in the esg.<project>.ini,
         * Builds the dataset identifier from the attributes.

        :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
        :returns: The dataset identifier
        :rtype: *str*

        """
        # Check each facet required by the dataset_id template from esg.<project>.ini
        # Facet values to check are deduced from file full-path
        # If a DRS attribute is missing regarding the dataset_id template,
        # the DRS attributes are completed from esg.<project>.ini maptables.
        if not ctx.dataset:
            for facet in ctx.facets.intersection(self.attributes.keys()):
                parser.check_facet(ctx.cfg, ctx.project_section, {facet: self.attributes[facet]})
            for facet in ctx.facets.difference(self.attributes.keys()):
                self.attributes[facet] = parser.get_option_from_map(ctx.cfg,
                                                                    ctx.project_section,
                                                                    facet, self.attributes)
            dataset_id = ctx.cfg.get(ctx.project_section, 'dataset_id', 0, self.attributes)
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
            shell = os.popen("{0} {1} | awk -F ' ' '{{ print $1 }}'".format(checksum_client, self.ffp), 'r')
            return shell.readline()[:-1]
        except:
            msg = '{0} checksum failed for {1}'.format(checksum_type, self.ffp)
            logging.warning(msg)
            raise Exception(msg)
