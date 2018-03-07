#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

"""

import itertools
import logging

from ESGConfigParser.custom_exceptions import NoConfigKey

from constants import *
from context import ProcessingContext
from custom_exceptions import *
from esgprep.utils.misc import load, store, evaluate, checksum
from handler import File, DRSPath


def process(collector_input):
    """
    process(collector_input)

    File process that:

     * Handles files,
     * Deduces facet key, values pairs from file attributes
     * Checks facet values against CV,
     * Applies the versioning
     * Populates the DRS tree crating the appropriate leaves,
     * Stores dataset statistics.

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
        # Loads attributes from filename, netCDF attributes, command-line
        fh.load_attributes(root=ctx.root,
                           pattern=ctx.pattern,
                           set_values=ctx.set_values)
        # Apply proper case to each attribute
        for key in fh.attributes:
            # Try to get the appropriate facet case for "category_default"
            try:
                fh.attributes[key] = ctx.cfg.get_options_from_pairs('category_defaults', key)
            except NoConfigKey:
                # If not specified keep facet case from local path, do nothing
                pass
        fh.check_facets(facets=ctx.facets,
                        config=ctx.cfg,
                        set_keys=ctx.set_keys)
        # Get parts of DRS path
        parts = fh.get_drs_parts(ctx.facets)
        # Instantiate file DRS path handler
        fph = DRSPath(parts)
        # If a latest version already exists make some checks FIRST to stop files to not process
        if fph.v_latest:
            # Latest version should be older than upgrade version
            if int(DRSPath.TREE_VERSION[1:]) <= int(fph.v_latest[1:]):
                raise OlderUpgrade(DRSPath.TREE_VERSION, fph.v_latest)
            # Walk through the latest dataset version to check its uniqueness with file checksums
            dset_nid = fph.path(f_part=False, latest=True, root=True)
            if dset_nid not in ctx.tree.hash.keys():
                ctx.tree.hash[dset_nid] = dict()
                ctx.tree.hash[dset_nid]['latest'] = dict()
                for root, _, filenames in os.walk(fph.path(f_part=False, latest=True, root=True)):
                    for filename in filenames:
                        ctx.tree.hash[dset_nid]['latest'][filename] = checksum(os.path.join(root, filename),
                                                                               ctx.checksum_type)
            # Pickup the latest file version
            latest_file = os.path.join(fph.path(latest=True, root=True), fh.filename)
            # Check latest file if exists
            if os.path.exists(latest_file):
                latest_checksum = checksum(latest_file, ctx.checksum_type)
                current_checksum = checksum(fh.ffp, ctx.checksum_type)
                # Check if processed file is a duplicate in comparison with latest version
                if latest_checksum == current_checksum:
                    fh.is_duplicate = True
        # Start the tree generation
        if not fh.is_duplicate:
            # Add the processed file to the "vYYYYMMDD" node
            src = ['..'] * len(fph.items(d_part=False))
            src.extend(fph.items(d_part=False, file_folder=True))
            src.append(fh.filename)
            ctx.tree.create_leaf(nodes=fph.items(root=True),
                                 leaf=fh.filename,
                                 label='{}{}{}'.format(fh.filename, LINK_SEPARATOR, os.path.join(*src)),
                                 src=os.path.join(*src),
                                 mode='symlink',
                                 origin=fh.ffp)
            # Add the "latest" node for symlink
            ctx.tree.create_leaf(nodes=fph.items(f_part=False, version=False, root=True),
                                 leaf='latest',
                                 label='{}{}{}'.format('latest', LINK_SEPARATOR, fph.v_upgrade),
                                 src=fph.v_upgrade,
                                 mode='symlink')
            # Add the processed file to the "files" node
            ctx.tree.create_leaf(nodes=fph.items(file_folder=True, root=True),
                                 leaf=fh.filename,
                                 label=fh.filename,
                                 src=fh.ffp,
                                 mode=ctx.mode)
            if ctx.upgrade_from_latest:
                # Walk through the latest dataset version and create a symlink for each file with a different
                # filename than the processed one
                for root, _, filenames in os.walk(fph.path(f_part=False, latest=True, root=True)):
                    for filename in filenames:
                        # Add latest files as tree leaves with version to upgrade instead of latest version
                        # i.e., copy latest dataset leaves to Tree
                        # Except if file has be ignored from latest version (i.e., with known issue)
                        if filename != fh.filename and filename not in ctx.ignore_from_latest:
                            src = os.path.join(root, filename)
                            ctx.tree.create_leaf(nodes=fph.items(root=True),
                                                 leaf=filename,
                                                 label='{}{}{}'.format(filename, LINK_SEPARATOR, os.readlink(src)),
                                                 src=os.readlink(src),
                                                 mode='symlink',
                                                 origin=os.path.realpath(src))
        else:
            # Pickup the latest file version
            latest_file = os.path.join(fph.path(latest=True, root=True), fh.filename)
            if ctx.upgrade_from_latest:
                # If upgrade from latest is activated, raise the error, no duplicated files allowed
                # Because incoming must only contain modifed/corrected files
                raise DuplicatedFile(latest_file, fh.ffp)
            else:
                # If default behavior, the incoming contains all data for a new version
                # In the case of a duplicated file, just pass to the expected symlink creation
                # and records duplicated file for further removal only if migration mode is the
                # default (i.e., moving files). In the case of --copy or --link, keep duplicates
                # in place into the incoming directory
                src = os.readlink(latest_file)
                ctx.tree.create_leaf(nodes=fph.items(root=True),
                                     leaf=fh.filename,
                                     label='{}{}{}'.format(fh.filename, LINK_SEPARATOR, src),
                                     src=src,
                                     mode='symlink',
                                     origin=fh.ffp)
                if ctx.mode == 'move':
                    ctx.tree.duplicates.append(fh.ffp)
        # Record entry for list()
        incoming = {'src': fh.ffp,
                    'dst': fph.path(root=True),
                    'filename': fh.filename,
                    'latest': fph.v_latest or 'Initial',
                    'size': fh.size}
        if fph.path(f_part=False) in ctx.tree.paths.keys():
            ctx.tree.paths[fph.path(f_part=False)].append(incoming)
        else:
            ctx.tree.paths[fph.path(f_part=False)] = [incoming]
        logging.info('{} <-- {}'.format(fph.path(f_part=False), fh.filename))
        return True
    except Exception as e:
        logging.error('{} skipped\n{}: {}'.format(ffp, e.__class__.__name__, e.message))
        return None
    finally:
        if ctx.pbar:
            ctx.pbar.update()


def run(args):
    """
    Main process that:

     * Instantiates processing context,
     * Loads previous program instance,
     * Parallelizes file processing with threads pools,
     * Apply command-line action to the whole DRS tree,
     * Evaluate exit status.

    :param ArgumentParser args: The command-line arguments parser

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
            # Rollback --commands_file value to command-line argument in any case
            ctx.tree.commands_file = ctx.commands_file
        else:
            if ctx.use_pool:
                processes = ctx.pool.imap(process, ctx.sources)
            else:
                processes = itertools.imap(process, ctx.sources)
            # Process supplied files
            results = [x for x in processes]
            # Close progress bar
            if ctx.pbar:
                ctx.pbar.close()
        # Get number of files scanned (including skipped files)
        ctx.scan_files = len(results)
        # Get number of scan errors
        ctx.scan_errors = results.count(None)
        # Backup tree context for later usage with other command lines
        store(TREE_FILE, data=[{key: ctx.__getattribute__(key) for key in CONTROLLED_ARGS},
                               ctx.tree,
                               ctx.scan_err_log,
                               results])
        logging.warning('DRS tree recorded for next usage onto {}.'.format(TREE_FILE))
        # Evaluates the scan results to trigger the DRS tree action
        if evaluate(results):
            # Check upgrade uniqueness
            ctx.tree.check_uniqueness(ctx.checksum_type)
            # Apply tree action
            ctx.tree.get_display_lengths()
            getattr(ctx.tree, ctx.action)()
