#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Checks DRS vocabulary against configuration files.

"""

import itertools
import traceback
from multiprocessing import Pool

from ESGConfigParser import split_map_header
from ESGConfigParser.custom_exceptions import ExpressionNotMatch, NoConfigOptions
from constants import *
from context import ProcessingContext
from esgprep.utils.custom_print import *
from esgprep.utils.misc import ProcessContext, ncopen
from fuzzywuzzy.fuzz import partial_ratio
from fuzzywuzzy.process import extractOne


def process(source):
    """
    process(collector_input)

    Data process that:

     * Retrieve facet key, values pairs from file or directory attributes

    :param str source: The file full path to process or the dataset ID

    """
    # Get process content from process global env
    assert 'pctx' in globals().keys()
    pctx = globals()['pctx']
    # Block to avoid program stop if a thread fails
    try:
        if pctx.directory or pctx.dataset_id or pctx.dataset_list:
            # Get attributes from directory format or dataset_id format
            attributes = re.match(pctx.pattern, source).groupdict()
        else:
            # Get attributes from NetCDF global attributes
            attributes = dict()
            with ncopen(source) as nc:
                for attr in nc.ncattrs():
                    attributes[attr] = nc.getncattr(attr)
            # Get attributes from filename, overwriting existing ones
            match = re.search(pctx.pattern, source)
            if not match:
                raise ExpressionNotMatch(source, pctx.pattern)
            attributes.update(match.groupdict())
        # Get source values from attributes
        for facet in pctx.facets:
            if facet in pctx.set_keys.keys():
                try:
                    # Rename attribute key
                    attributes[facet] = attributes.pop(pctx.set_keys[facet])
                except KeyError:
                    raise NoNetCDFAttribute(pctx.set_keys[facet], source)
            elif facet in attributes.keys():
                # Facet exists in attribute keys
                pass
            else:
                # Find closest NetCDF attributes in terms of partial string comparison
                key, score = extractOne(facet, attributes.keys(), scorer=partial_ratio)
                if score >= 80:
                    # Rename attribute key
                    attributes[facet] = attributes.pop(key)
                    Print.debug('Consider "{}" attribute instead of "{}" facet'.format(key, facet))
                else:
                    raise NoNetCDFAttribute(pctx.set_keys[facet], source)
            with pctx.lock:
                s = pctx.source_values[0]
                s[facet].add(attributes[facet])
                pctx.source_values[0] = s
        msg = TAGS.SUCCESS + 'Deserialize {}'.format(COLORS.HEADER(source))
        with pctx.lock:
            Print.info(msg)
        return 1
    except KeyboardInterrupt:
        raise
    except Exception:
        exc = traceback.format_exc().splitlines()
        msg = TAGS.FAIL + COLORS.HEADER(source) + '\n'
        msg += '\n'.join(exc)
        with pctx.lock:
            Print.exception(msg, buffer=True)
        return 0
    finally:
        with pctx.lock:
            pctx.progress.value += 1
            percentage = int(pctx.progress.value * 100 / pctx.nbsources)
            msg = COLORS.OKBLUE('\rHarvesting facets values from data: ')
            msg += '{}% | {}/{} {}'.format(percentage, pctx.progress.value, pctx.nbsources,
                                           SOURCE_TYPE[pctx.source_type])
            Print.progress(msg)


def initializer(keys, values):
    """
    Initialize process context by setting particular variables as global variables.

    :param list keys: Argument name
    :param list values: Argument value

    """
    assert len(keys) == len(values)
    global pctx
    pctx = ProcessContext({key: values[i] for i, key in enumerate(keys)})


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
        # Init process context
        cctx = {name: getattr(ctx, name) for name in PROCESS_VARS}
        cctx['source_values'][0] = dict((facet, set()) for facet in ctx.facets)
        if ctx.use_pool:
            # Init processes pool
            pool = Pool(processes=ctx.processes, initializer=initializer, initargs=(cctx.keys(), cctx.values()))
            processes = pool.imap(process, ctx.sources)
        else:
            initializer(cctx.keys(), cctx.values())
            processes = itertools.imap(process, ctx.sources)
        # Process supplied sources
        results = [x for x in processes]
        # Close pool of workers if exists
        if 'pool' in locals().keys():
            locals()['pool'].close()
            locals()['pool'].join()
        Print.progress('\n')
        # Flush buffer
        Print.flush()
        ctx.scan_data = sum(results)
        ctx.scan_errors = results.count(0)
        # Get source values
        source_values = cctx['source_values'][0]
        # Get facets values declared in configuration file
        config_values = {}
        progress = 0
        nfacets = len(ctx.facets)
        for facet in ctx.facets:
            try:
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
                msg = TAGS.SUCCESS
                msg += 'Get values from {} for {}'.format(COLORS.HEADER(ctx.cfg.file),
                                                          COLORS.HEADER(facet))
                Print.info(msg)
            except KeyboardInterrupt:
                raise
            except Exception:
                exc = traceback.format_exc().splitlines()
                msg = TAGS.FAIL
                msg += 'Get values from {} for {}'.format(COLORS.HEADER(ctx.cfg.file),
                                                          COLORS.HEADER(facet)) + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)
                ctx.scan_errors += 1
            finally:
                progress += 1
                percentage = int(progress * 100 / nfacets)
                msg = COLORS.OKBLUE('\rCollecting facet values from INI file(s): ')
                msg += '{}% | {}/{} facet(s)'.format(percentage, progress, nfacets)
                Print.progress(msg)
        Print.progress('\n')
        # Flush buffer
        Print.flush()
        # Compare values from sources against values from configuration file
        Print.result(''.center(WIDTH, '='))
        Print.result('{} :: {}'.format('Facet'.ljust(FACET_WIDTH), 'Status'.rjust(STATUS_WIDTH)))
        Print.result(''.center(WIDTH, '-'))
        for facet in ctx.facets:
            if isinstance(config_values[facet], type(re.compile(""))):
                config_values[facet] = set([v for v in source_values[facet] if config_values[facet].search(v)])
            if not source_values[facet]:
                line = '{} :: '.format(facet.ljust(FACET_WIDTH))
                line += COLORS.WARNING(STATUS[2].rjust(STATUS_WIDTH))
                Print.result(line)
            elif not config_values[facet]:
                line = '{} :: '.format(facet.ljust(FACET_WIDTH))
                line += COLORS.WARNING(STATUS[3].rjust(STATUS_WIDTH))
                Print.result(line)
            else:
                undeclared_values = source_values[facet].difference(config_values[facet])
                updated_values = source_values[facet].union(config_values[facet])
                if undeclared_values:
                    line = '{} :: '.format(facet.ljust(FACET_WIDTH))
                    line += COLORS.FAIL(STATUS[1].rjust(STATUS_WIDTH))
                    Print.result(line)
                    _values = ', '.join(sorted(undeclared_values))
                    msg = COLORS.FAIL(':: UNDECLARED VALUES :: ')
                    msg += COLORS.HEADER(facet)
                    msg += COLOR().bold(' :: {}'.format(_values))
                    Print.error(msg, buffer=True)
                    _values = ', '.join(sorted(updated_values))
                    msg = COLORS.SUCCESS(':: UPDATED VALUES    :: ')
                    msg += COLORS.HEADER(facet)
                    msg += ' :: {}'.format(_values)
                    Print.error(msg, buffer=True)
                    ctx.any_undeclared = True
                else:
                    line = '{} :: '.format(facet.ljust(FACET_WIDTH))
                    line += COLORS.SUCCESS(STATUS[0].rjust(STATUS_WIDTH))
                    Print.result(line)
        Print.result(''.center(WIDTH, '='))
        # Flush buffer
        Print.flush()
    # Evaluate errors and exit with appropriated return code
    if ctx.scan_errors > 0:
        sys.exit(ctx.scan_errors)
    if ctx.any_undeclared:
        sys.exit(-2)
