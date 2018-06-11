#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Generates ESGF mapfiles upon a local ESGF node or not.

"""

import itertools
import logging
import os
import re
import sys
from datetime import datetime
from multiprocessing import Pool

from ESGConfigParser import interpolate, MissingPatternKey, BadInterpolation, InterpolationDepthError
from lockfile import LockFile

from constants import *
from context import ProcessingContext
from esgprep.utils.misc import evaluate, remove, get_checksum_pattern, ProcessContext
from handler import File, Dataset


def get_output_mapfile(outdir, attributes, mapfile_name, dataset_id, dataset_version, mapfile_drs=None, basename=False):
    """
    Builds the mapfile full path depending on:

     * the --mapfile name using tokens,
     * an optional mapfile tree declared in configuration file with ``mapfile_drs``,
     * the --outdir output directory.

    :param str outdir: The output directory (default is current working directory)
    :param dict attributes: The facets values deduces from file full path
    :param str mapfile_name: An optional mapfile name from the command-line
    :param str dataset_id: The dataset id
    :param str dataset_version: The dataset version
    :param str mapfile_drs: The optional mapfile tree
    :param boolean basename: True to only get mapfile name without root directory
    :returns: The mapfile full path
    :rtype: *str*

    """
    # Deduce output directory from --outdir and 'mapfile_drs'
    if not basename:
        if mapfile_drs:
            try:
                outdir = os.path.join(outdir, interpolate(mapfile_drs, attributes))
            except (BadInterpolation, InterpolationDepthError):
                raise MissingPatternKey(attributes.keys(), mapfile_drs)
        else:
            outdir = os.path.realpath(outdir)
    # Create output directory if not exists, catch OSError instead
    try:
        os.makedirs(outdir)
    except OSError:
        pass
    # Deduce mapfile name from --mapfile argument
    if re.compile(r'{dataset_id}').search(mapfile_name):
        mapfile_name = re.sub(r'{dataset_id}', dataset_id, mapfile_name)
    if re.compile(r'{version}').search(mapfile_name):
        if dataset_version:
            mapfile_name = re.sub(r'{version}', dataset_version, mapfile_name)
        else:
            mapfile_name = re.sub(r'\.{version}', '', mapfile_name)
    if re.compile(r'{date}').search(mapfile_name):
        mapfile_name = re.sub(r'{date}', datetime.now().strftime("%Y%d%m"), mapfile_name)
    if re.compile(r'{job_id}').search(mapfile_name):
        mapfile_name = re.sub(r'{job_id}', str(os.getpid()), mapfile_name)
    # Add a "working extension" pending for the end of process
    if basename:
        return mapfile_name + WORKING_EXTENSION
    else:
        return os.path.join(outdir, mapfile_name) + WORKING_EXTENSION


def mapfile_entry(dataset_id, dataset_version, ffp, size, optional_attrs):
    """
    Builds the mapfile entry corresponding to a processed file.

    :param str dataset_id: The dataset id
    :param str dataset_version: The dataset version
    :param str ffp: The file full path
    :param str size: The file size
    :param dict optional_attrs: Optional attributes to append to mapfile lines
    :returns: The mapfile line/entry
    :rtype: *str*

    """
    line = [dataset_id]
    # Add version number to dataset identifier if --no-version flag is disabled
    if dataset_version:
        line = ['{}#{}'.format(dataset_id, dataset_version[1:])]
    line.append(ffp)
    line.append(str(size))
    for k, v in optional_attrs.items():
        if v:
            line.append('{}={}'.format(k, v))
    return ' | '.join(line) + '\n'


def write(outfile, entry):
    """
    Inserts a mapfile entry.
    It generates a lockfile to avoid that several threads write on the same file at the same time.
    A LockFile is acquired and released after writing. Acquiring LockFile is timeouted if it's locked by other thread.
    Each process adds one line to the appropriate mapfile

    :param str outfile: The output mapfile full path
    :param str entry: The mapfile entry to write

    """
    lock = LockFile(outfile)
    with lock:
        with open(outfile, 'a+') as mapfile:
            mapfile.write(entry)


def process(source):
    """
    File process that:

     * Handles file,
     * Harvests directory attributes,
     * Check DRS attributes against CV,
     * Builds dataset ID,
     * Retrieves file size,
     * Does checksums,
     * Deduces mapfile name,
     * Writes the corresponding mapfile entry.

    Any error leads to skip the file. It does not stop the process.

    :param str source: The source to process could be a path or a dataset ID
    :returns: The output mapfile full path
    :rtype: *str*

    """
    # Get process content from process global env
    assert 'pctx' in globals().keys()
    pctx = globals()['pctx']
    # Block to avoid program stop if a thread fails
    try:
        if pctx.source_type == 'file':
            # Instantiate source handle as file
            sh = File(source)
        else:
            # Instantiate source handler as dataset
            sh = Dataset(source)
        # Matching between directory_format and file full path
        sh.load_attributes(pattern=pctx.pattern)
        # Deduce dataset_id
        dataset_id = pctx.dataset_name
        if not pctx.dataset_name:
            sh.check_facets(facets=pctx.facets,
                            config=pctx.cfg)
            dataset_id = sh.get_dataset_id(pctx.cfg.get('dataset_id', raw=True))
        # Ensure that the first facet is ALWAYS the same as the called project section (case insensitive)
        assert dataset_id.lower().startswith(pctx.project.lower()), 'Inconsistent dataset identifier. ' \
                                                                    'Must start with "{}/" ' \
                                                                    '(case-insensitive)'.format(pctx.project)
        # Deduce dataset_version
        dataset_version = sh.get_dataset_version(pctx.no_version)
        # Build mapfile name depending on the --mapfile flag and appropriate tokens
        outfile = get_output_mapfile(outdir=pctx.outdir,
                                     attributes=sh.attributes,
                                     mapfile_name=pctx.mapfile_name,
                                     dataset_id=dataset_id,
                                     dataset_version=dataset_version,
                                     mapfile_drs=pctx.mapfile_drs,
                                     basename=pctx.basename)
        # Dry-run: don't write mapfile to only show their paths
        if pctx.action == 'make':
            # Generate the corresponding mapfile entry/line
            optional_attrs = dict()
            optional_attrs['mod_time'] = sh.mtime
            if not pctx.no_checksum:
                if pctx.checksums_from:
                    if source in pctx.checksums_from.keys():
                        if re.match(get_checksum_pattern(pctx.checksum_type), pctx.checksums_from[source]):
                            optional_attrs['checksum'] = pctx.checksums_from[source]
                        else:
                            logging.warning('Invalid {} checksum pattern: {} -- '
                                            'Recomputing checksum.'.format(pctx.checksum_type,
                                                                           pctx.checksums_from[source]))
                            optional_attrs['checksum'] = sh.checksum(pctx.checksum_type)
                    else:
                        logging.warning('Entry not found in checksum file: {} -- '
                                        'Recomputing checksum.'.format(source))
                        optional_attrs['checksum'] = sh.checksum(pctx.checksum_type)
                else:
                    optional_attrs['checksum'] = sh.checksum(pctx.checksum_type)
                optional_attrs['checksum_type'] = pctx.checksum_type.upper()
            optional_attrs['dataset_tech_notes'] = pctx.notes_url
            optional_attrs['dataset_tech_notes_title'] = pctx.notes_title
            line = mapfile_entry(dataset_id=dataset_id,
                                 dataset_version=dataset_version,
                                 ffp=source,
                                 size=sh.size,
                                 optional_attrs=optional_attrs)
            write(outfile, line)
            logging.info('{} <-- {}'.format(os.path.splitext(os.path.basename(outfile))[0], source))
        # Return mapfile name
        return outfile
    # Catch any exception into error log instead of stop the run
    except Exception as e:
        logging.error('{} skipped\n{}: {}'.format(source, e.__class__.__name__, e.message))
        return None
    finally:
        pctx.progress.value += 1
        percentage = int(pctx.progress.value * 100 / pctx.nbsources)
        msg = '\rMapfile(s) generation: {}% | {}/{} {}'.format(percentage,
                                                               pctx.progress.value,
                                                               pctx.nbsources,
                                                               SOURCE_TYPE[pctx.source_type])
        pctx.lock.acquire()
        logging.info(msg)
        sys.stdout.write(msg)
        sys.stdout.flush()
        pctx.lock.release()


def initializer(keys, values):
    """
    Initialize process context by setting particular variables as global variables.

    :param list keys: Argument name list
    :param list values: Argument value list

    """
    assert len(keys) == len(values)
    global pctx
    pctx = ProcessContext({key: values[i] for i, key in enumerate(keys)})


def run(args):
    """
    Main process that:

     * Instantiates processing context,
     * Parallelizes file processing with threads pools,
     * Copies mapfile(s) to the output directory,
     * Evaluate exit status.

    :param ArgumentParser args: Command-line arguments parser

    """
    # TODO: Review print strategy
    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        logging.info('==> Scan started')
        # Init process context
        cctx = {name: getattr(ctx, name) for name in PROCESS_VARS}
        # Init progress bar
        if ctx.use_pool:
            # Init processes pool
            pool = Pool(processes=ctx.processes, initializer=initializer, initargs=(cctx.keys(),
                                                                                    cctx.values()))
            processes = pool.imap(process, ctx.sources)
        else:
            initializer(cctx.keys(), cctx.values())
            processes = itertools.imap(process, ctx.sources)
        # Process supplied sources
        results = [x for x in processes]
        if 'pool' in locals().keys():
            locals()['pool'].close()
            locals()['pool'].join()
        # Get number of files scanned (including skipped files)
        ctx.scan_files = len(results)
        # Get number of scan errors
        ctx.scan_errors = results.count(None)
        # Get number of generated mapfiles
        ctx.nb_map = len(filter(None, set(results)))
        # Evaluates the scan results to finalize mapfiles writing
        if evaluate(results):
            for mapfile in filter(None, set(results)):
                # Remove mapfile working extension
                if ctx.action == 'show':
                    # Print mapfiles to be generated
                    if ctx.pbar or ctx.quiet:
                        print(remove(WORKING_EXTENSION, mapfile))
                    logging.info(remove(WORKING_EXTENSION, mapfile))
                elif ctx.action == 'make':
                    # A final mapfile is silently overwritten if already exists
                    os.rename(mapfile, remove(WORKING_EXTENSION, mapfile))
    # Evaluate errors and exit with appropriate return code
    if not ctx.scan_files and not ctx.scan_errors:
        # Results list is empty = no files scanned/found
        sys.exit(1)
    if ctx.scan_files and ctx.scan_errors:
        if ctx.scan_errors == ctx.scan_files:
            # All files have been skipped or failed during the scan
            sys.exit(3)
        else:
            # Some files have been skipped or failed during the scan
            sys.exit(2)
