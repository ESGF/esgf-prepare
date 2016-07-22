#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: esgprep.checkvocab.main.py
    :platform: Unix
    :synopsis: Check DRS vocabulary against configuration files.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.jussieu.fr>

"""

import logging
import os
import re
import sys

from esgprep.utils import parser, utils
from esgprep.utils.constants import *


class ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +------------------------+-------------+--------------------------------------------+
    | Attribute              | Type        | Description                                |
    +========================+=============+============================================+
    | *self*.directory       | *list*      | Paths to scan                              |
    +------------------------+-------------+--------------------------------------------+
    | *self*.project         | *str*       | Project                                    |
    +------------------------+-------------+--------------------------------------------+
    | *self*.cfg             | *callable*  | Configuration file parser                  |
    +------------------------+-------------+--------------------------------------------+
    | *self*.project_section | *str*       | Project section name in configuration file |
    +------------------------+-------------+--------------------------------------------+
    | *self*.pattern         | *re object* | DRS regex pattern without version          |
    +------------------------+-------------+--------------------------------------------+
    | *self*.facets          | *list*      | List of the DRS facets                     |
    +------------------------+-------------+--------------------------------------------+

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*
    :raises Error: If no section corresponds to the project name in the configuration file

    """

    def __init__(self, args):
        self.directory = args.directory
        self.project = args.project
        self.verbosity = args.v
        self.project_section = 'project:{0}'.format(args.project)
        self.cfg = parser.config_parse(args.i, args.project, self.project_section)
        self.pattern = parser.translate_directory_format(self.cfg, self.project, self.project_section)
        self.pattern = self.pattern.split('/(?P<version>')[0] + '$'
        self.facets = set(re.compile(self.pattern).groupindex.keys()).difference(set(IGNORED_FACETS))


def get_dsets_from_tree(ctx):
    """
    Yields datasets to process. Only the "dataset part" of the DRS tree is returned
    (i.e., from "root" to before the "version" facet).

    :param esgprep.checkvocab.main.ProcessingContext ctx: The processing context
    :returns: The dataset as a part of the DRS tree
    :rtype: *iter*

    """
    for directory in ctx.directory:
        # Compile directory_format regex from start to the facet before <version> part
        regex = re.compile(ctx.pattern)
        # If the supplied directory is deeper than the version level, walk up the tree
        for root, _, _ in utils.walk(directory, downstream=False, followlinks=True):
            if regex.search(root):
                yield root
        # Or walk down.
        for root, _, _ in utils.walk(directory, downstream=True, followlinks=True):
            if regex.search(root):
                yield root


def get_facet_values_from_tree(ctx, dsets, facets):
    """
    Returns all used values of each facet from the DRS tree, according to the supplied directories.

    :param esgprep.checkvocab.main.ProcessingContext ctx: The processing context
    :param iter dsets: The dataset part of the DRS tree
    :param list facets: The facets list
    :returns: The declared values of each facet
    :rtype: *dict*

    """
    logging.info('Harvesting facets values from DRS tree...')
    used_values = {facet: set() for facet in facets}
    for dset in dsets:
        try:
            attributes = re.match(ctx.pattern, os.path.realpath(dset)).groupdict()
        except:
            msg = 'DRS attributes cannot be deduce from matching.\n' \
                  'Please check the "directory_format" regex in the [project:{0}] section.\n' \
                  'path  -> {1}\n' \
                  'regex -> {2}'.format(ctx.project, os.path.realpath(dset), ctx.pattern)
            raise Exception(msg)
        # Each facet is ensured to be included into "attributes" from matching
        for facet in facets:
            used_values[facet].add(attributes[facet])
    return used_values


def get_facet_values_from_config(cfg, section, facets):
    """
    Returns all declared values of each facet from the configuration file, according to the project section.

    :param RawConfigParser cfg: The configuration file parser (as a :func:`ConfigParser.RawConfigParser` class instance)
    :param str section: The section name to parse
    :param set facets: The set of facets to check
    :returns: The declared values of each facet
    :rtype: *dict*

    """
    declared_values = {}
    for facet in facets:
        logging.info('Collecting values from INI file(s) for "{0}" facet...'.format(facet))
        try:
            declared_values[facet] = parser.get_facet_options(cfg, section, facet)
            if not isinstance(declared_values[facet], re._pattern_type):
                declared_values[facet] = set(declared_values[facet])
        except:
            for m in parser.get_maps(cfg, section):
                maptable = cfg.get(section, m)
                from_keys, _ = parser.split_map_header(maptable.split('\n')[0])
                if facet in from_keys:
                    declared_values[facet] = set(parser.get_options_from_map_in_sources(cfg, section, m, facet))
        finally:
            if facet not in declared_values.keys():
                msg = '"{0}" is not declared in section "{1}"'.format(facet, section)
                raise Exception(msg)
    return declared_values


def compare_values(facets, used_values, declared_values, verbosity=False):
    """
    Compares used values from DRS tree with all declared values in configuration file for each facet.

    :param list facets: The facets list
    :param dict used_values: Dictionary of sets of used values from DRS tree
    :param dict declared_values: Dictionary of sets of  declared values from the configuration file
    :param boolean verbosity: Display declared/undeclared and used/unused values if True
    :returns: True if undeclared values in configuration file are used in DRS tree
    :rtype: *boolean*

    """
    any_undeclared = False
    for facet in facets:
        if isinstance(declared_values[facet], type(re.compile("", 0))):
            declared_values[facet] = set([v for v in used_values[facet] if declared_values[facet].search(v)])
        if verbosity:
            if not declared_values[facet]:
                logging.warning('{0} facet - No declared values'.format(facet))
                values = ', '.join(sorted(used_values[facet]))
                logging.info('{0} facet - Used values: {1}'.format(facet, values))
            else:
                values = ', '.join(sorted(declared_values[facet]))
                logging.info('{0} facet - Declared values: {1}'.format(facet, values))
                values = ', '.join(sorted(used_values[facet]))
                logging.info('{0} facet - Used values: {1}'.format(facet, values))
        undeclared_values = used_values[facet].difference(declared_values[facet])
        unused_values = declared_values[facet].difference(used_values[facet])
        updated_values = used_values[facet].union(declared_values[facet])
        if undeclared_values:
            values = ', '.join(sorted(undeclared_values))
            logging.info('{0} facet - UNDECLARED values: {1}'.format(facet, values))
            any_undeclared = True
            values = ', '.join(sorted(updated_values))
            logging.info('{0} facet - UPDATED values to declare: {1}'.format(facet, values))
        if unused_values and verbosity:
            values = ', '.join(sorted(unused_values))
            logging.info('{0} facet - Unused values: {1}'.format(facet, values))
    if any_undeclared:
        logging.error('Result: THERE WERE UNDECLARED VALUES USED.')
    else:
        logging.info('Result: ALL USED VALUES ARE PROPERLY DECLARED.')
    return any_undeclared


def main(args):
    """
    Main process that:

     * Instantiates processing context
     * Parses the configuration files options and values,
     * Deduces facets and values from directories,
     * Compares the values of each facet between both,
     * Print or log the checking.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Instantiate processing context from command-line arguments or SYNDA job dictionary
    ctx = ProcessingContext(args)
    # Get facets values declared into configuration file
    facet_values_config = get_facet_values_from_config(ctx.cfg, ctx.project_section, ctx.facets)
    # Walk trough DRS to get all dataset roots
    dsets = get_dsets_from_tree(ctx)
    # Get facets values used by DRS tree
    facet_values_tree = get_facet_values_from_tree(ctx, dsets, list(ctx.facets))
    # Compare values from tree against values from configuration file
    any_disallowed = compare_values(list(ctx.facets), facet_values_tree, facet_values_config, ctx.verbosity)
    if any_disallowed:
        sys.exit(1)
