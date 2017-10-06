#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Generates ESGF mapfiles upon a local ESGF node or not.

"""

import logging
import os
import re
from datetime import datetime

from ESGConfigParser import interpolate
from lockfile import LockFile

from constants import *
from context import ProcessingContext
from esgprep.utils.misc import as_pbar, evaluate
from handler import File


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


def mapfile_entry(dataset_id, dataset_version, ffp, size, **kwargs):
    """
    Builds the mapfile entry corresponding to a processed file.

    :param str dataset_id: The dataset id
    :param str dataset_version: The dataset version
    :param str ffp: The file full path
    :param str size: The file size
    :returns: The mapfile line/entry
    :rtype: *str*

    """
    line = [dataset_id]
    # Add version number to dataset identifier if --no-version flag is disabled
    if dataset_version:
        line = ['{}#{}'.format(dataset_id, dataset_version[1:])]
    line.append(ffp)
    line.append(str(size))
    for k, v in kwargs.items():
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
    ffp, ctx = collector_input
    # Block to avoid program stop if a thread fails
    try:
        # Instantiate file handler
        fh = File(ffp)
        # Matching between directory_format and file full path
        fh.load_attributes(project=ctx.project,
                           pattern=ctx.pattern)
        # Deduce dataset_id
        dataset_id = ctx.dataset
        if not ctx.dataset:
            fh.check_facets(facets=ctx.facets,
                            config=ctx.cfg)
            dataset_id = fh.get_dataset_id(ctx.cfg.get('dataset_id', raw=True))
        # Deduce dataset_version
        dataset_version = fh.get_dataset_version(ctx.no_version)
        # Build mapfile name depending on the --mapfile flag and appropriate tokens
        outfile = get_output_mapfile(outdir=ctx.outdir,
                                     attributes=fh.attributes,
                                     mapfile_name=ctx.mapfile_name,
                                     dataset_id=dataset_id,
                                     dataset_version=dataset_version,
                                     mapfile_drs=ctx.mapfile_drs)
        # Generate the corresponding mapfile entry/line
        line = mapfile_entry(dataset_id,
                             dataset_version,
                             ffp,
                             fh.size,
                             mod_time=fh.mtime,
                             checksum=fh.checksum(ctx.checksum_type, ctx.checksum_client),
                             checksum_type=ctx.checksum_type,
                             dataset_tech_notes=ctx.notes_url,
                             dataset_tech_notes_title=ctx.notes_title)
        write(outfile, line)
        logging.info('{} <-- {}'.format(os.path.splitext(os.path.basename(outfile))[0], ffp))
        # Return mapfile name
        return outfile
    # Catch any exception into error log instead of stop the run
    except Exception as e:
        logging.error('{} skipped\n{}: {}'.format(ffp, e.__class__.__name__, e.message))
        return None


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
        logging.info('==> Scan started')
        processes = ctx.pool.imap(process, ctx.sources)
        if ctx.pbar:
            processes = as_pbar(processes, desc='Mapfile(s) generation', units='files', total=len(ctx.sources))
        # Process supplied files
        results = [x for x in processes]
        # Get number of files scanned (including skipped files)
        ctx.scan_files = len(results)
        # Get number of scan errors
        ctx.scan_errors = results.count(None)
        # Get number of generated mapfiles
        ctx.nb_map = len(filter(None, set(results)))
        # Evaluates the scan results to finalize mapfiles writing
        if evaluate(results):
            # Remove mapfile working extension
            # A final mapfile is silently overwritten if already exists
            for mapfile in filter(None, set(results)):
                os.rename(mapfile, mapfile.replace(WORKING_EXTENSION, ''))
