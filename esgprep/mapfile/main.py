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
from datetime import datetime

from ESGConfigParser import interpolate, NoConfigKey
from lockfile import LockFile

from constants import *
from context import ProcessingContext
from esgprep.utils.misc import evaluate
from handler import File, Dataset


def get_output_mapfile(outdir, attributes, mapfile_name, dataset_id, dataset_version, mapfile_drs=None):
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
    :returns: The mapfile full path
    :rtype: *str*

    """
    # Deduce output directory from --outdir and 'mapfile_drs'
    if mapfile_drs:
        outdir = os.path.join(outdir, interpolate(mapfile_drs, attributes))
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


def process(collector_input):
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

    :param tuple collector_input: A tuple with the file path and the processing context
    :returns: The output mapfile full path
    :rtype: *str*

    """
    # Deserialize inputs from collector
    source, ctx = collector_input
    # Block to avoid program stop if a thread fails
    try:
        if ctx.source_type == 'file':
            # Instantiate source handle as file
            sh = File(source)
        else:
            # Instantiate source handler as dataset
            sh = Dataset(source)
        # Matching between directory_format and file full path
        sh.load_attributes(pattern=ctx.pattern)
        # Apply proper case to each attribute
        for key in sh.attributes:
            # Try to get the appropriate facet case for "category_default"
            try:
                sh.attributes[key] = ctx.cfg.get_options_from_pairs('category_defaults', key)
            except NoConfigKey:
                # If not specified keep facet case from local path, do nothing
                pass
        # Deduce dataset_id
        dataset_id = ctx.dataset
        if not ctx.dataset:
            sh.check_facets(facets=ctx.facets,
                            config=ctx.cfg)
            dataset_id = sh.get_dataset_id(ctx.cfg.get('dataset_id', raw=True))
        # Deduce dataset_version
        dataset_version = sh.get_dataset_version(ctx.no_version)
        # Build mapfile name depending on the --mapfile flag and appropriate tokens
        outfile = get_output_mapfile(outdir=ctx.outdir,
                                     attributes=sh.attributes,
                                     mapfile_name=ctx.mapfile_name,
                                     dataset_id=dataset_id,
                                     dataset_version=dataset_version,
                                     mapfile_drs=ctx.mapfile_drs)
        # Dry-run: don't write mapfile to only show their paths
        if ctx.action == 'make':
            # Generate the corresponding mapfile entry/line
            optional_attrs = dict()
            optional_attrs['mod_time'] = sh.mtime
            if not ctx.no_checksum:
                optional_attrs['checksum'] = sh.checksum(ctx.checksum_type)
                optional_attrs['checksum_type'] = ctx.checksum_type.upper()
            optional_attrs['dataset_tech_notes'] = ctx.notes_url
            optional_attrs['dataset_tech_notes_title'] = ctx.notes_title
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
        if ctx.pbar:
            ctx.pbar.update()


def run(args):
    """
    Main process that:

     * Instantiates processing context,
     * Parallelizes file processing with threads pools,
     * Copies mapfile(s) to the output directory,
     * Evaluate exit status.

    :param ArgumentParser args: Command-line arguments parser

    """
    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        # If dataset ID is submitted for "show" action skip scan
        logging.info('==> Scan started')
        if ctx.use_pool:
            processes = ctx.pool.imap(process, ctx.sources)
        else:
            processes = itertools.imap(process, ctx.sources)
        # Process supplied sources
        results = [x for x in processes]
        # Close progress bar
        if ctx.pbar:
            ctx.pbar.close()
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
                    if ctx.pbar:
                        print(mapfile.replace(WORKING_EXTENSION, ''))
                    logging.info(mapfile.replace(WORKING_EXTENSION, ''))
                elif ctx.action == 'make':
                    # A final mapfile is silently overwritten if already exists
                    os.rename(mapfile, mapfile.replace(WORKING_EXTENSION, ''))
