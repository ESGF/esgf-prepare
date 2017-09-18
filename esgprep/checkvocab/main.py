#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Checks DRS vocabulary against configuration files.

"""

import logging
import re

from ESGConfigParser import split_map_header
from ESGConfigParser.custom_exceptions import ExpressionNotMatch, NoConfigOptions

from constants import *
from context import ProcessingContext


def run(args):
    """
    Main process that:

     * Instantiates processing context
     * Parses the configuration files options and values,
     * Deduces facets and values from directories or dataset lists,
     * Compares the values of each facet between both,
     * Print or log the checking.

    :param ArgumentParser args: The command-line arguments parser

    """
    # Instantiate processing context manager
    with ProcessingContext(args) as ctx:
        # Get facets values used by the source
        source_values = dict((facet, set()) for facet in ctx.facets)
        for source in ctx.sources:
            try:
                attributes = re.match(ctx.pattern, source).groupdict()
                for facet in ctx.facets:
                    source_values[facet].add(attributes[facet])
            except AttributeError:
                logging.error(ExpressionNotMatch(source, ctx.pattern))
                ctx.scan_errors += 1
        # Get facets values declared in configuration file
        config_values = {}
        for facet in ctx.facets:
            logging.info('Collecting values from INI file(s) for "{}" facet...'.format(facet))
            try:
                config_values[facet], _ = ctx.cfg.get_options(facet)
                if not isinstance(config_values[facet], type(re.compile(""))):
                    config_values[facet] = set(config_values[facet])
            except NoConfigOptions:
                for option in ctx.cfg.get_options_from_list('maps'):
                    maptable = ctx.cfg.get(option)
                    from_keys, _ = split_map_header(maptable.split('\n')[0])
                    if facet in from_keys:
                        config_values[facet] = set(ctx.cfg.get_options_from_map(option, facet))
            finally:
                if facet not in config_values.keys():
                    raise NoConfigOptions(facet)
        # Compare values from sources against values from configuration file
        print(''.center(WIDTH, '='))
        print('{} :: {}'.format('Facet'.ljust(FACET_WIDTH), 'Status'.rjust(STATUS_WIDTH)))
        print(''.center(WIDTH, '-'))
        for facet in ctx.facets:
            if isinstance(config_values[facet], type(re.compile(""))):
                config_values[facet] = set([v for v in source_values[facet] if config_values[facet].search(v)])
            if not source_values[facet]:
                print('{} :: {}'.format(facet.ljust(FACET_WIDTH), STATUS[2].rjust(STATUS_WIDTH)))
            elif not config_values[facet]:
                print('{} :: {}'.format(facet.ljust(FACET_WIDTH), STATUS[3].rjust(STATUS_WIDTH)))
            else:
                undeclared_values = source_values[facet].difference(config_values[facet])
                updated_values = source_values[facet].union(config_values[facet])
                if undeclared_values:
                    print('{} :: {}'.format(facet.ljust(FACET_WIDTH), STATUS[1].rjust(STATUS_WIDTH)))
                    _values = ', '.join(sorted(undeclared_values))
                    logging.error('{} :: UNDECLARED VALUES :: {}'.format(facet, _values))
                    _values = ', '.join(sorted(updated_values))
                    logging.error('{} :: UPDATED VALUES    :: {}'.format(facet, _values))
                    ctx.any_undeclared = True
                else:
                    print('{} :: {}'.format(facet.ljust(FACET_WIDTH), STATUS[0].rjust(STATUS_WIDTH)))
        print(''.center(WIDTH, '='))
