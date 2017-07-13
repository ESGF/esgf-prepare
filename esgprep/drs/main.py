#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

"""

import logging
import os

from context import ProcessingContext
from esgprep.drs.constants import *
from esgprep.drs.exceptions import *
from esgprep.utils.exceptions import *
from esgprep.utils.utils import load, store, as_pbar
from handler import File, DRSPath


def checksum(ffp, checksum_type, checksum_client):
    """
    Does the checksum by the Shell avoiding Python memory limits.

    :param str ffp: The file full path
    :param str checksum_client: Shell command line for checksum
    :param str checksum_type: Checksum type
    :returns: The checksum
    :rtype: *str*
    :raises Error: If the checksum fails

    """
    if not checksum_client:
        return None
    try:
        shell = os.popen("{} {} | awk -F ' ' '{{ print $1 }}'".format(checksum_client, ffp))
        return shell.readline()[:-1]
    except:
        raise ChecksumFail(ffp, checksum_type)


def process(collector_input):
    """
    process(ffp, ctx)

    File process that:

     * Deduce facet key, values pairs from file attributes
     * Build the DRS of the file
     * Build the DRS of the corresponding dataset
     * Apply the versioning
     * Build the whole DRS tree
     * Store dataset statistics into a dict.

    :param tuple collector_input: A tuple with the file path and the processing context
    :return: True on success
    :rtype: *boolean*

    """
    # Deserialize inputs from collector
    ffp, ctx = collector_input
    # Block to avoid program stop if a thread fails
    try:
        # Instantiate file handler
        fh = File(ffp)
        # Matching between filename_format and filename
        fh.load_attributes(ctx)
        # Get parts of DRS path
        parts = fh.get_drs_parts(ctx)
        # Instantiate file DRS path handler
        fph = DRSPath(parts)
        # If a latest version already exists make some checks FIRST to stop files to not process
        if fph.v_latest:
            # Latest version should be older than upgrade version
            if int(DRSPath.TREE_VERSION[1:]) <= int(fph.v_latest[1:]):
                raise OlderUpgrade(DRSPath.TREE_VERSION, fph.v_latest)
            # Check latest files
            if ctx.checksum_client:
                # Pickup the latest file version
                latest_file = os.path.join(fph.path(latest=True, root=True), fh.filename)
                # Compute checksums and compare between latest (if exists) and upgrade file versions
                if os.path.exists(latest_file):
                    latest_checksum = checksum(latest_file, ctx.checksum_type, ctx.checksum_client)
                    current_checksum = checksum(fh.ffp, ctx.checksum_type, ctx.checksum_client)
                    if latest_checksum == current_checksum:
                        raise DuplicatedFile(latest_file, fh.ffp)
        # Start the tree generation
        # Add file DRS path to Tree
        src = ['..'] * len(fph.items(d_part=False))
        src.extend(fph.items(d_part=False, latest=True, file_folder=True))
        src.append(fh.filename)
        ctx.tree.create_leaf(nodes=fph.items(root=True),
                             leaf=fh.filename,
                             label='{}{}{}'.format(fh.filename, LINK_SEPARATOR, os.path.join(*src)),
                             src=os.path.join(*src),
                             mode='symlink')
        # Add "latest" node for symlink
        ctx.tree.create_leaf(nodes=fph.items(f_part=False, version=False, root=True),
                             leaf='latest',
                             label='{}{}{}'.format('latest', LINK_SEPARATOR, fph.v_upgrade),
                             src=fph.v_upgrade,
                             mode='symlink')
        # Add "files" node to Tree
        ctx.tree.create_leaf(nodes=fph.items(file_folder=True, root=True),
                             leaf=fh.filename,
                             label=fh.filename,
                             src=fh.ffp,
                             mode=ctx.mode)
        # Walk through the latest dataset version
        if fph.v_latest:
            for root, _, filenames in os.walk(os.path.join(fph.path(f_part=False, latest=True, root=True))):
                for filename in filenames:
                    # Add latest files as tree leaves with version to upgrade instead of latest version
                    # i.e., copy latest dataset leaves to Tree
                    if filename != fh.filename:
                        src = os.readlink(os.path.join(root, filename))
                        ctx.tree.create_leaf(nodes=fph.items(root=True),
                                             leaf=filename,
                                             label='{}{}{}'.format(filename, LINK_SEPARATOR, src),
                                             src=src,
                                             mode='symlink')
        else:
            fph.v_latest = 'Initial'
        # Record entry for list()
        incoming = {'src': ffp,
                    'dst': fph.path(root=True),
                    'filename': fh.filename,
                    'variable': fh.get('variable'),
                    'latest': fph.v_latest,
                    'size': fh.size}
        if fph.path(f_part=False) in ctx.tree.paths.keys():
            ctx.tree.paths[fph.path(f_part=False)].append(incoming)
        else:
            ctx.tree.paths[fph.path(f_part=False)] = [incoming]
        logging.info('{} <-- {}'.format(fph.path(f_part=False), fh.filename))
        return True
    # Catch any exception into error log instead of stop the run
    except Exception as e:
        logging.error('{} skipped\n{}: {}'.format(ffp, e.__class__.__name__, e.message))
        return None


def main(args):
    """
    Main process that:

     * Instantiates processing context
     * Parses the configuration files options and values,
     * Deduces facets and values from files,
     * Gets the DRS directory for each file,
     * Apply DRS action to each file.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        logging.info('==> Scan started')
        if not ctx.scan:
            reader = load(TREE_FILE)
            _ = reader.next()
            ctx.tree = reader.next()
            ctx.scan_err_log = reader.next()
            results = reader.next()
            logging.warning('Previous DRS tree found and recovered <-- {}.'.format(TREE_FILE))
        else:
            processes = ctx.pool.imap(process, ctx.sources)
            if ctx.pbar:
                processes = as_pbar(processes, desc='Scanning incoming files', units='files', total=len(ctx.sources))
            # Process supplied files
            results = [x for x in processes]
        # Get number of files scanned
        ctx.scan_files = len(results)
        # Get number of scan errors
        ctx.scan_errors = results.count(None)
        # Backup tree context for later usage with other command lines
        store(TREE_FILE, data=[{key: ctx.__getattribute__(key) for key in CONTROLLED_ARGS},
                               ctx.tree,
                               ctx.scan_err_log,
                               results])
        logging.warning('DRS tree recorded for next usage --> {}.'.format(TREE_FILE))
        # Decline outputs depending on the scan results
        # Raise errors when one or several files have been skipped or failed
        if all(results) and any(results):
            # Results list contains only True value = all files have been successfully scanned
            # Apply tree action
            ctx.tree.get_display_lengths()
            getattr(ctx.tree, ctx.action)()
        elif not all(results) and any(results):
            # Results list contains some None values = some files have been skipped or failed during the scan
            # Apply tree action
            # Apply tree action
            ctx.tree.get_display_lengths()
            getattr(ctx.tree, ctx.action)()
