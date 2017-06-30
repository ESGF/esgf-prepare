#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Checks DRS vocabulary against configuration files.

"""

import logging
import re
import sys
from tqdm import tqdm

from esgprep.checkvocab.constants import *
from esgprep.utils.config import CfgParser, split_map_header
from esgprep.utils.constants import *
from esgprep.utils.exceptions import *
from esgprep.utils.collectors import PathCollector, DatasetCollector


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.project = args.project
        self.dir_filter = args.ignore_dir_filter
        self.file_filter = args.include_file_filter
        self.project_section = 'project:{0}'.format(args.project)
        self.cfg = CfgParser(args.i, section=self.project_section)
        if args.directory:
            self.directory = args.directory
            self.pattern = self.cfg.translate_directory_format(self.project_section)
        else:
            self.dataset_list = args.dataset_list
            self.pattern = self.cfg.translate_dataset_format(self.project_section)
        self.facets = set(re.compile(self.pattern).groupindex.keys()).difference(set(IGNORED_KEYS))


def get_facet_values_from_source(ctx, collector, facets):
    """
    Returns all used values of each facet according to the supplied directories or list of datasets.

    :param esgprep.checkvocab.main.ProcessingContext ctx: The processing context
    :param esgprep.utils.collector.Collector collector: The file or dataset collector
    :param list facets: The facets list
    :returns: The declared values of each facet
    :rtype: *dict*

    """
    scan_errors = 0
    used_values = dict((facet, set()) for facet in facets)
    if collector.__class__.__name__ == 'FileCollector':
        source_type = 'files'
    else:
        source_type = 'datasets'
    print('Collecting {0}...\r'.format(source_type)),
    for dset in tqdm(collector,
                     desc='Harvesting facets values from source'.format(source_type).ljust(LEN_MSG),
                     total=len(collector),
                     bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} ' + source_type,
                     ncols=100,
                     file=sys.stdout):
        try:
            attributes = re.match(ctx.pattern, dset).groupdict()
            # Each facet is ensured to be included into "attributes" from matching
            for facet in facets:
                used_values[facet].add(attributes[facet])
        except:
            logging.error(DirectoryNotMatch(dset, ctx.pattern, ctx.project_section, ctx.cfg.read_paths))
            scan_errors += 1
    if scan_errors > 0:
        print('{0}: {1} (see {2})'.format('Scan errors'.ljust(LEN_MSG),
                                          scan_errors,
                                          logging.getLogger().handlers[0].baseFilename))
    return used_values, scan_errors


def get_facet_values_from_config(cfg, section, facets):
    """
    Returns all declared values of each facet from the configuration file, according to the project section.

    :param CfgParser cfg: The configuration file parser
    :param str section: The section name to parse
    :param set facets: The set of facets to check
    :returns: The declared values of each facet
    :rtype: *dict*

    """
    declared_values = {}
    for facet in facets:
        logging.info('Collecting values from INI file(s) for "{0}" facet...'.format(facet))
        try:
            declared_values[facet], _ = cfg.get_options(section, facet)
            if not isinstance(declared_values[facet], type(re.compile(""))):
                declared_values[facet] = set(declared_values[facet])
        except NoConfigOptions:
            for option in cfg.get_options_from_list(section, 'maps'):
                maptable = cfg.get(section, option)
                from_keys, _ = split_map_header(maptable.split('\n')[0])
                if facet in from_keys:
                    declared_values[facet] = set(cfg.get_options_from_map(section, option, facet))
        finally:
            if facet not in declared_values.keys():
                raise NoConfigOptions(facet, section, cfg.read_paths)
    return declared_values


def compare_values(project, facets, used_values, declared_values):
    """
    Compares used values from DRS tree with all declared values in configuration file for each facet.

    :param str project: The project ID
    :param list facets: The facets list
    :param dict used_values: Dictionary of sets of used values from DRS tree
    :param dict declared_values: Dictionary of sets of  declared values from the configuration file
    :returns: True if undeclared values in configuration file are used in DRS tree
    :rtype: *boolean*

    """
    any_undeclared = False
    lengths = [max([len(facet) for facet in facets]), max([len(status) for status in STATUS.itervalues()])]
    lengths.append(sum(lengths) + 4)
    print(''.center(lengths[-1], '='))
    print('{0} :: {1}'.format('Facet'.ljust(lengths[0]),
                              'Status'.rjust(lengths[1]), ))
    print(''.center(lengths[-1], '-'))
    for facet in facets:
        if isinstance(declared_values[facet], type(re.compile(""))):
            declared_values[facet] = set([v for v in used_values[facet] if declared_values[facet].search(v)])
        if not used_values[facet]:
            print('{0} :: {1}'.format(facet.ljust(lengths[0]),
                                      STATUS[2].ljust(lengths[1])))
        elif not declared_values[facet]:
            print('{0} :: {1}'.format(facet.ljust(lengths[0]),
                                      STATUS[3].ljust(lengths[1])))
        else:
            undeclared_values = used_values[facet].difference(declared_values[facet])
            updated_values = used_values[facet].union(declared_values[facet])
            if undeclared_values:
                print('{0} :: {1}'.format(facet.ljust(lengths[0]),
                                          STATUS[1].ljust(lengths[1])))
                values = ', '.join(sorted(undeclared_values))
                logging.error('{0} :: UNDECLARED VALUES :: {1}'.format(facet, values))
                values = ', '.join(sorted(updated_values))
                logging.error('{0} :: UPDATED VALUES    :: {1}'.format(facet, values))
                any_undeclared = True
            else:
                print('{0} :: {1}'.format(facet.ljust(lengths[0]),
                                          STATUS[0].ljust(lengths[1])))
    print(''.center(lengths[-1], '='))
    if any_undeclared:
        print('Please update "esg.{0}.ini" following: {1}'.format(project,
                                                                  logging.getLogger().handlers[0].baseFilename))
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
    if args.directory:
        # The source is a list of directories
        # Instanciate file collector to walk through the tree
        collector = PathCollector(ctx.directory, ctx.dir_filter, ctx.file_filter)
    else:
        # The source is a list of files (i.e., several dataset lists)
        # Instanciate dataset collector to parse the files
        collector = DatasetCollector(ctx.dataset_list)
    # Get facets values used by the source
    facet_values_found, scan_errors = get_facet_values_from_source(ctx, collector, list(ctx.facets))
    # Get facets values declared in configuration file
    facet_values_config = get_facet_values_from_config(ctx.cfg, ctx.project_section, ctx.facets)
    # Compare values from tree against values from configuration file
    any_undeclared = compare_values(ctx.project, list(ctx.facets), facet_values_found, facet_values_config)
    # Exit status
    if scan_errors:
        sys.exit(1)
    if any_undeclared:
        sys.exit(2)
