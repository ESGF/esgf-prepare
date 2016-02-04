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
from datetime import datetime
from esgmapfilesutils import init_logging, check_directory, config_parse, MultilineFormatter
from esgmapfilesutils import translate_directory_format, split_line, split_map

# Program version
__version__ = 'v{0} {1}'.format('0.2', datetime(year=2016, month=01, day=05).strftime("%Y-%d-%m"))


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
    | *self*.pattern         | *re object* | DRS regex pattern                          |
    +------------------------+-------------+--------------------------------------------+
    | *self*.facets          | *list*      | List of the DRS facets                     |
    +------------------------+-------------+--------------------------------------------+

    :param dict args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *dict*
    :raises Error: If no section name corresponds to the project name in the configuration file

    """
    def __init__(self, args):
        """
        Returns the processing context as a dictionary.

        :param dict args: Parsed command-line arguments
        :returns: The processing context
        :rtype: *dict*
        """
        init_logging(args.log)
        for path in args.directory:
            check_directory(path)
        self.directory = args.directory
        self.project = args.project
        self.cfg = config_parse(args.i, args.project)
        self.project_section = 'project:{0}'.format(args.project)
        if not self.cfg.has_section(self.project_section):
            raise Exception('No section in configuration file corresponds to "{0}". '
                            'Available sections are {1}.'.format(self.project_section,
                                                                 self.cfg.sections()))
        # Get expected facets from dataset_id in configuration file
        self.facets = set(re.findall(re.compile(r'%\(([^()]*)\)s'),
                                     self.cfg.get(self.project_section,
                                                  'dataset_id',
                                                  raw=True)))
        # Get DRS pattern from directory_format in configuration file
        self.pattern = translate_directory_format(self.cfg.get(self.project_section,
                                                               'directory_format',
                                                               raw=True)).split('/(?P<version>[\w.-]+)')[0]


def get_args():
    """
    Returns parsed command-line arguments. See ``esgscan_check_vocab -h`` for full description.

    :returns: The corresponding ``argparse`` Namespace

    """
    parser = argparse.ArgumentParser(
        prog='esgscan_check_vocab',
        description="""The mapfile generation relies on the ESGF node configuration files.
                    These "esg.<project>.ini" files declares the Data Reference Syntax (DRS) and
                    the controlled vocabularies of each project.|n|n

                    "esgscan_check_vocab" allows you to easily check the configuration file. It
                    implies that your directory structure strictly follows the project DRS
                    including the version facet.""",
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog="""Developed by:|n
                  Levavasseur, G. (CNRS/IPSL - glipsl@ipsl.jussieu.fr)|n
                  Iwi, A. (STFC/BADC - alan.iwi@stfc.ac.uk)""")
    parser._optionals.title = "Optional arguments"
    parser._positionals.title = "Positional arguments"
    parser.add_argument(
        'directory',
        type=str,
        nargs='+',
        help="""One or more directories to recursively scan. Unix wildcards|n
                are allowed.""")
    parser.add_argument(
        '--project',
        metavar='<project_id>',
        type=str,
        required=True,
        help="""Required lower-cased project name.""")
    parser.add_argument(
        '-i',
        metavar='/esg/config/esgcet/.',
        type=str,
        default='/esg/config/esgcet/.',
        help="""Initialization/configuration directory containing "esg.ini"|n
                and "esg.<project>.ini" files. If not specified, the usual|n
                datanode directory is used.""")
    parser.add_argument(
        '--log',
        metavar='$PWD',
        type=str,
        const=os.getcwd(),
        nargs='?',
        help="""Logfile directory. If not, standard output is used.""")
    parser.add_argument(
        '-h', '--help',
        action="help",
        help="""Show this help message and exit.\n\n""")
    parser.add_argument(
        '-V', '--Version',
        action='version',
        version='%(prog)s ({0})'.format(__version__),
        help="""Program version.""")
    return parser.parse_args()


def get_dsets_from_tree(ctx):
    """
    Yields datasets to process. Only the "dataset part" of the DRS tree is returned
    (i.e., from "root" to "member/ensemble" facet).

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The dataset as a part of the DRS tree
    :rtype: *iter*

    """
    for directory in ctx.directory:
        for root, _, _ in os.walk(directory):
            if re.compile(r'/v[0-9]*/').search(root):
                yield os.path.dirname(root)


def strip_hash_to_end(dataset_id):
    """
    Cuts the ``dataset_id`` before the ending version.

    :param str dataset_id: The ``dataset_id`` string
    :returns: The ``dataset_id`` without version
    :rtype: *str*

    """
    try:
        return dataset_id[:dataset_id.index("#")]
    except ValueError:
        return dataset_id


def id_components(dataset_id):
    """
    Converts/splits the ``dataset_id`` string into a list of facets.

    :param str dataset_id: The ``dataset_id`` string
    :returns: The facets list
    :rtype: *list*

    """
    return strip_hash_to_end(dataset_id).split(".")


def get_facets_from_config(ctx):
    """
    Returns all facets described by the ``dataset_id`` option from the configuration file.

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The facets list
    :rtype: *list*

    """
    return id_components(ctx.cfg.get(ctx.project_section, "dataset_id"))


def get_facet_values_from_tree(ctx, dsets, facets):
    """
    Returns all used values of each facet from the DRS tree, according to the supplied directories.

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
                logging.warning('{0} skipped because of {1} facets instead of {2} expected.'.format(dset,
                                                                                                    len(attributes),
                                                                                                    len(facets)))
            else:
                for key in attributes.keys():
                    used_values[key].add(attributes[key])
    return used_values


def get_facet_values_from_config(ctx):
    """
    Returns all declared values of each facet from the configuration file, according to the project section.

    :param checkvocab.ProcessingContext ctx: The processing context (as a :func:`checkvocab.ProcessingContext` class instance)
    :returns: The declared values of each facet
    :rtype: *dict*

    """
    declared_values = {}
    for facet in ctx.facets:
        if ctx.cfg.has_option(ctx.project_section, '{0}_options'.format(facet)):
            declared_values[facet] = set(split_line(ctx.cfg.get(ctx.project_section,
                                                                '{0}_options'.format(facet)),
                                                    sep=','))
        elif ctx.cfg.has_option(ctx.project_section, '{0}_map'.format(facet)):
            from_keys, to_keys, value_map = split_map(ctx.cfg.get(ctx.project_section, '{0}_map'.format(facet)))
            if facet not in to_keys:
                raise Exception('{0}_map is miss-declared in esg.{1}.ini. '
                                '"{0}" facet has to be in "destination facet"'.format(facet,
                                                                                      ctx.project))
            declared_values[facet] = set([value[to_keys.index(facet)] for value in value_map.itervalues()])
        else:
            declared_values[facet] = None
    return declared_values


def compare_values(facets, used_values, declared_values):
    """
    Compares used values from DRS tree with all declared values in configuration file for each facet.

    :param list facets: The facets list
    :param dict used_values: The used values from DRS tree
    :param dict declared_values: The declared values from the configuration file
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
            updated_values = used_values[facet].union(declared_values[facet])
            if disallowed_values:
                logging.info('{0}_options - UNDECLARED values: {1}'.format(facet, ', '.join(used_values[facet])))
                any_disallowed = True
                logging.info('{0}_options - UPDATED values to declare: {1}'.format(facet, ', '.join(updated_values)))
            if unused_values:
                logging.info('{0}_options - Unused values: {1}'.format(facet, ', '.join(unused_values)))
    if any_disallowed:
        logging.warning(' THERE WERE UNDECLARED VALUES USED '.center(50, '!'))
    return any_disallowed


def main():
    """
    Main process that:

     * Instantiates processing context
     * Parses the configuration files options and values,
     * Deduces facets and values from directories,
     * Compares the values of each facet between both,
     * Print or log the checking.

    """
    # Instantiate processing context from command-line arguments or SYNDA job dictionary
    ctx = ProcessingContext(get_args())
    # Get facets values declared into configuration file
    facet_values_config = get_facet_values_from_config(ctx)
    # Get dataset list from DRS tree
    dsets = get_dsets_from_tree(ctx)
    # Get facets values used by DRS tree
    facet_values_tree = get_facet_values_from_tree(ctx, dsets, ctx.facets)
    any_disallowed = compare_values(ctx.facets, facet_values_tree, facet_values_config)
    if any_disallowed:
        sys.exit(1)


# Main entry point for stand-alone call.
if __name__ == '__main__':
    main()
