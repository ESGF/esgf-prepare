#!/usr/bin/env python

import re
import os
import sys
import logging
from esgprep.utils import utils, parser


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

    :param argparse.ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*
    :raises Error: If no section corresponds to the project name in the configuration file

    """
    def __init__(self, args):
        for path in args.directory:
            utils.check_directory(path)
        self.directory = args.directory
        self.project = args.project
        self.verbosity = args.v
        self.project_section = 'project:{0}'.format(args.project)
        self.cfg = parser.config_parse(args.i, args.project, self.project_section)
        self.facets = set(re.findall(re.compile(r'%\(([^()]*)\)s'),
                                     self.cfg.get(self.project_section, 'dataset_id', raw=True)))
        self.pattern = parser.translate_directory_format(self.cfg.get(self.project_section,
                                                                      'directory_format',
                                                                      raw=True)).split('/(?P<version>')[0]


def get_dsets_from_tree(ctx):
    """
    Yields datasets to process. Only the "dataset part" of the DRS tree is returned
    (i.e., from "root" to before the "version" facet).

    :param esgprep.checkvocab.main.ProcessingContext ctx: The processing context
    :returns: The dataset as a part of the DRS tree
    :rtype: *iter*

    """
    for directory in ctx.directory:
        for root, _, _ in os.walk(directory):
            if re.compile(r'/v[0-9]{8}/').search(root):
                yield os.path.dirname(root)


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
            msg = 'Matching failed to deduce DRS attributes from {0}. Please check the ' \
                  '"directory_format" regex in the [project:{1}] section.'.format(os.path.realpath(dset), ctx.project)
            logging.warning(msg)
            raise Exception(msg)
        del attributes['root']
        for key in attributes.keys():
            used_values[key].add(attributes[key])
    return used_values


def get_facet_values_from_config(ctx):
    """
    Returns all declared values of each facet from the configuration file, according to the project section.

    :param esgprep.checkvocab.main.ProcessingContext ctx: The processing context
    :returns: The declared values of each facet
    :rtype: *dict*

    """
    declared_values = {}
    for facet in ctx.facets:
        logging.info('Collecting values from INI file(s) for "{0}" facet...'.format(facet))
        try:
            declared_values[facet] = set(parser.get_facet_options(ctx.cfg, ctx.project_section, facet))
        except:
            # Catch the exception to keep empty set()
            declared_values[facet] = set()
    return declared_values


def compare_values(facets, used_values, declared_values, verbosity=False):
    """
    Compares used values from DRS tree with all declared values in configuration file for each facet.

    :param list facets: The facets list
    :param dict used_values: Dictionary of sets of used values from DRS tree
    :param dict declared_values: Dictionary of sets of  declared values from the configuration file
    :returns: True if undeclared values in configuration file are used in DRS tree
    :rtype: *boolean*

    """
    any_undeclared = False
    for facet in facets:
        if verbosity:
            if not declared_values[facet]:
                logging.warning('{0} facet - No declared values'.format(facet))
                logging.info('{0} facet - Used values: {1}'.format(facet, ', '.join(used_values[facet])))
            else:
                logging.info('{0} facet - Declared values: {1}'.format(facet, ', '.join(declared_values[facet])))
                logging.info('{0} facet - Used values: {1}'.format(facet, ', '.join(used_values[facet])))
        undeclared_values = used_values[facet].difference(declared_values[facet])
        unused_values = declared_values[facet].difference(used_values[facet])
        updated_values = used_values[facet].union(declared_values[facet])
        if undeclared_values:
            logging.info('{0} facet - UNDECLARED values: {1}'.format(facet, ', '.join(undeclared_values)))
            any_undeclared = True
            logging.info('{0} facet - UPDATED values to declare: {1}'.format(facet, ', '.join(updated_values)))
        if unused_values and verbosity:
            logging.info('{0} facet - Unused values: {1}'.format(facet, ', '.join(unused_values)))
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
    facet_values_config = get_facet_values_from_config(ctx)
    # Walk trough DRS to get all dataset roots
    dsets = get_dsets_from_tree(ctx)
    # Get facets values used by DRS tree
    facet_values_tree = get_facet_values_from_tree(ctx, dsets, list(ctx.facets))
    any_disallowed = compare_values(list(ctx.facets), facet_values_tree, facet_values_config, ctx.verbosity)
    if any_disallowed:
        sys.exit(1)
