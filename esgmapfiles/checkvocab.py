#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Utility to check (and update) the configuration INI file used by esg_mapfiles.

"""

# Module imports
import re
import os
import sys
import logging
import argparse
from argparse import RawTextHelpFormatter
from esgmapfilesutils import init_logging, check_directory, config_parse

# Program version
__version__ = '{0} {1}-{2}-{3}'.format('v0.1', '2015', '10', '05')


class ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +---------------------+-------------+---------------------------------------+
    | Attribute           | Type        | Description                           |
    +=====================+=============+=======================================+
    | *self*.directory    | *list*      | Paths to scan                         |
    +---------------------+-------------+---------------------------------------+
    | *self*.project      | *str*       | Project                               |
    +---------------------+-------------+---------------------------------------+
    | *self*.cfg          | *callable*  | Configuration file parser             |
    +---------------------+-------------+---------------------------------------+
    | *self*.pattern      | *re object* | DRS regex pattern                     |
    +---------------------+-------------+---------------------------------------+

    :param dict args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *dict*
    :raises Error: If the project name is inconsistent with the sections names from the configuration file

    """
    def __init__(self, args):
        init_logging(args.logdir)
        for path in args.directory:
            check_directory(path)
        self.directory = args.directory
        self.cfg = config_parse(args.config)
        if args.project in self.cfg.sections():
            self.project = args.project
        else:
            raise Exception('No section in configuration file corresponds to "{0}" project. Supported projects are {1}.'.format(args.project, self.cfg.sections()))

        regex = self.cfg.get(self.project, 'directory_format').split('/')
        regex_end = [i for i, string in enumerate(regex) if re.search('version', string)][0]
        self.pattern = re.compile('/'.join(regex[:regex_end]))


def get_args():
    """
    Returns parsed command-line arguments. See ``esg_mapfiles_check_vocab -h`` for full description.

    :returns: The corresponding ``argparse`` Namespace

    """
    parser = argparse.ArgumentParser(
        description="""Check the configuration file to use with esg_mapfiles command-line.""",
        formatter_class=RawTextHelpFormatter,
        add_help=False,
        epilog="""Developed by Iwi, A. (BADC) and Levavasseur, G. (CNRS/IPSL)""")
    parser.add_argument(
        'directory',
        type=str,
        nargs='+',
        help='One or more directories to recursively scan. Unix wildcards are allowed.')
    parser.add_argument(
        '-h', '--help',
        action="help",
        help="""Show this help message and exit.\n\n""")
    parser.add_argument(
        '-p', '--project',
        type=str,
        required=True,
        help="""Required project name corresponding to a section of the configuration file.\n\n""")
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='{0}/config.ini'.format(os.path.dirname(os.path.abspath(__file__))),
        help="""Path of the configuration INI file to check\n(default is {0}/config.ini).\n\n""".format(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument(
        '-l', '--logdir',
        type=str,
        const=os.getcwd(),
        nargs='?',
        help="""Logfile directory (default is working directory).\nIf not, standard output is used.\n\n""")
    parser.add_argument(
        '-V', '--Version',
        action='version',
        version='%(prog)s ({0})'.format(__version__),
        help="""Program version.""")
    return parser.parse_args()


def get_dsets_from_tree(ctx):
    """
    Yields datasets to process. Only the "dataset part" of the DRS tree is returned (i.e., from "root" to "member/ensemble" facet).

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The dataset as a part of the DRS tree
    :rtype: *iter*

    """
    for directory in ctx.directory:
        for root, dirs, files in os.walk(directory):
            if re.compile('v[0-9]+$').search(root):
                yield os.path.dirname(root)


def strip_hash_to_end(id):
    """
    Cuts the ``dataset_ID`` before the ending version.

    :param str id: The ``dataset_id`` string
    :returns: The ``dataset_ID`` without version
    :rtype: *str*

    """
    try:
        return id[:id.index("#")]
    except ValueError:
        return id


def id_components(id):
    """
    Converts/splits the ``dataset_ID`` string into a list of facets.

    :param str id: The ``dataset_ID`` string
    :returns: The facets list
    :rtype: *list*

    """
    return strip_hash_to_end(id).split(".")


def get_facets_from_config(ctx):
    """
    Returns all facets described by the ``dataset_ID`` option from the configuration file.

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The facets list
    :rtype: *list*

    """
    return id_components(ctx.cfg.get(ctx.project, "dataset_ID"))


def get_facet_values_from_tree(ctx, dsets, facets):
    """
    Returns all used values of each facet from the DRS tree, according to the supplied direcotries.

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :param iter dsets: The dataset part of the DRS tree
    :param list facets: The facets list
    :returns: The declared values of each facet
    :rtype: *dict*

    """
    used_values = {}
    for facet in facets:
        used_values[facet] = set()
    for dset in dsets:
        try:
            attributes = re.match(ctx.pattern, os.path.realpath(dset)).groupdict()
        except:
            raise Exception('The "directory_format" regex cannot match {0}'.format(dset))
        else:
            del attributes['root']
            if len(attributes) != len(facets):
                logging.warning('{0} skipped because of {1} facets instead of {2} excpected.'.format(dset, len(attributes), len(facets)))
            else:
                for key in attributes.keys():
                    used_values[key].add(attributes[key])
    return used_values


def get_facet_values_from_config(ctx, facets):
    """
    Returns all declared values of each facet from the configuration file, according to the project section.

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :param list facets: The facets list
    :returns: The declared values of each facet
    :rtype: *dict*

    """
    declared_values = {}
    for facet in facets:
        key = '{0}_options'.format(facet)
        if ctx.cfg.has_option(ctx.project, key):
            declared_values[facet] = set(re.split(",\s+", ctx.cfg.get(ctx.project, key)))
        else:
            declared_values[facet] = None
    return declared_values


def compare_values(project, facets, used_values, declared_values):
    """
    Compares used values from DRS tree with all declared values in configuration file for each facet.

    :param str project: The project name
    :param list facets: The facets list
    :param dict used_values: The used values from DRS tree
    :param dict declared_values: The declred values from the configuration file

    :returns: True if undeclared values in configuration file are used in DRS tree
    :rtype: *boolean*

    """
    any_disallowed = False
    for facet in facets:
        if declared_values[facet] is None:
            logging.info('{0}_options - No declared values'.format(facet))
            logging.info('{0}_options - Used values: {1}'.format(facet, ', '.join(used_values[facet])))
        else:
            logging.info('{0}_options - Declared values: {1}'.format(facet, ', '.join(declared_values[facet])))
            logging.info('{0}_options - Used values: {1}'.format(facet, ', '.join(used_values[facet])))
            disallowed_values = used_values[facet].difference(declared_values[facet])
            unused_values = declared_values[facet].difference(used_values[facet])
            if disallowed_values:
                logging.info('{0}_options - UNDECLARED values: {1}'.format(facet, ', '.join(used_values[facet])))
                any_disallowed = True
                logging.info('{0}_options - UPDATED values to delcare: {1}'.format(facet, ', '.join(used_values[facet].union(declared_values[facet]))))
            if unused_values:
                logging.info('{0}_options - Unused values: {1}'.format(facet, ', '.join(unused_values)))
    if any_disallowed:
        logging.warning(' THERE WERE UNDECLARED VALUES USED '.center(50, '!'))
    return any_disallowed


def main():
    """
    Main process that\:
     * Instanciates processing context
     * Parses the configuration files options and values,
     * Deduces facets and values from directories,
     * Compares the values of each facet between both,
     * Print or log the checking.

    """
    # Instanciate processing context from command-line arguments or SYNDA job dictionnary
    ctx = ProcessingContext(get_args())
    # Get exepected facets from dataset_ID in configuration file
    facets = get_facets_from_config(ctx)
    # Get facets values declared into configuration file
    facet_values_config = get_facet_values_from_config(ctx, facets)
    # Get dataset list from DRS tree
    dsets = get_dsets_from_tree(ctx)
    # Get facets values used by DRS tree
    facet_values_tree = get_facet_values_from_tree(ctx, dsets, facets)
    any_disallowed = compare_values(ctx.project, facets, facet_values_tree, facet_values_config)
    if any_disallowed:
        sys.exit(1)


# Main entry point for stand-alone call.
if __name__ == '__main__':
    main()
