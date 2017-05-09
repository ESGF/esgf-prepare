#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Checks DRS vocabulary against configuration files.

"""

import logging
import os
import sys

from tqdm import tqdm

from esgprep.checkvocab.constants import *
from esgprep.utils import parser, utils
from esgprep.utils.constants import *
from esgprep.utils.exceptions import *


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.project = args.project
        self.filter = args.filter
        self.project_section = 'project:{0}'.format(args.project)
        self.cfg = parser.CfgParser(args.i, section=self.project_section)
        if args.directory:
            self.directory = args.directory
            self.pattern = self.cfg.translate_directory_format(self.project_section)
        else:
            self.dataset_list = args.dataset_list
            self.pattern = self.cfg.translate_dataset_format(self.project_section)
        self.facets = set(re.compile(self.pattern).groupindex.keys()).difference(set(IGNORED_KEYS))


def yield_datasets_from_file(ctx):
    """
    Yields datasets to process from a text file.  Each line may contain the dataset with optional 
    appended .v<version> or #<version>, and only the part without the version is returned.
    
    :param esgprep.checkvocab.main.ProcessingContext ctx: The processing context
    :returns: The dataset ID with or without version
    :rtype: *iter*
    
    """
    trailing = re.compile("((\.v|#)[0-9]+)?\s*$")  # re for optional version and any whitespace
    with open(ctx.dataset_list) as f:
        for line in f:
            yield trailing.sub("", line)


def yield_files_from_tree(ctx):
    """
    Yields datasets to process. The file full path is returned to match the whole directory format.

    :param esgprep.checkvocab.main.ProcessingContext ctx: The processing context
    :returns: The file full path of the DRS tree
    :rtype: *iter*

    """
    for directory in ctx.directory:
        for root, _, filenames in utils.walk(directory, followlinks=True):
            if '/files/' not in root:
                for filename in filenames:
                    ffp = os.path.join(root, filename)
                    if os.path.isfile(ffp) and re.match(ctx.filter, filename) is not None:
                        yield ffp


def get_facet_values_from_tree(ctx, dsets, facets):
    """
    Returns all used values of each facet from the DRS tree, according to the supplied directories.

    :param esgprep.checkvocab.main.ProcessingContext ctx: The processing context
    :param iter dsets: The dataset part of the DRS tree
    :param list facets: The facets list
    :returns: The declared values of each facet
    :rtype: *dict*

    """
    used_values = dict((facet, set()) for facet in facets)
    # Get the number of files to scan
    nfiles = sum(1 for _ in utils.Tqdm(yield_files_from_tree(ctx),
                                       desc='Collecting files'.ljust(LEN_MSG),
                                       unit='files',
                                       file=sys.stdout))
    for dset in tqdm(dsets,
                     desc='Harvesting facets values from DRS tree'.ljust(LEN_MSG),
                     total=nfiles,
                     bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} files',
                     ncols=100,
                     unit='files',
                     file=sys.stdout):
        try:
            attributes = re.match(ctx.pattern, dset).groupdict()
        except:
            raise DirectoryNotMatch(os.path.realpath(dset), ctx.pattern, ctx.project_section, ctx.cfg.read_paths)
        # Each facet is ensured to be included into "attributes" from matching
        for facet in facets:
            used_values[facet].add(attributes[facet])
    return used_values


def get_facet_values_from_dataset_list(ctx, dsets, facets):
    """
    Returns all used values of each facet from the supplied of dataset IDs.

    :param esgprep.checkvocab.main.ProcessingContext ctx: The processing context
    :param iter dsets: The dataset part of the DRS tree
    :param list facets: The facets list
    :returns: The declared values of each facet
    :rtype: *dict*

    """
    used_values = dict((facet, set()) for facet in facets)
    # Get the number of files to scan
    nids = sum(1 for _ in utils.Tqdm(yield_datasets_from_file(ctx),
                                     desc='Collecting datasets'.ljust(LEN_MSG),
                                     unit='files',
                                     file=sys.stdout))
    for dset in utils.Tqdm(dsets,
                           desc='Harvesting facets values from dataset list'.ljust(LEN_MSG),
                           total=nids,
                           bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} files',
                           ncols=100,
                           unit='dataset ids',
                           file=sys.stdout):
        try:
            attributes = re.match(ctx.pattern, dset).groupdict()
        except:
            raise DatasetNotMatch(dset, ctx.pattern, ctx.project_section, ctx.cfg.read_paths)
        # Each facet is ensured to be included into "attributes" from matching
        for facet in facets:
            used_values[facet].add(attributes[facet])
    return used_values


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
                from_keys, _ = parser.split_map_header(maptable.split('\n')[0])
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
        # Walk trough DRS to get all dataset roots
        dsets = yield_files_from_tree(ctx)
        # Get facets values used by DRS tree
        facet_values_found = get_facet_values_from_tree(ctx, dsets, list(ctx.facets))
    else:
        dsets = yield_datasets_from_file(ctx)
        facet_values_found = get_facet_values_from_dataset_list(ctx, dsets, list(ctx.facets))
    # Get facets values declared in configuration file
    facet_values_config = get_facet_values_from_config(ctx.cfg, ctx.project_section, ctx.facets)
    # Compare values from tree against values from configuration file
    any_disallowed = compare_values(ctx.project, list(ctx.facets), facet_values_found, facet_values_config)
    if any_disallowed:
        sys.exit(1)
