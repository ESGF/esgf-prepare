#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

"""

import itertools
import sys
import traceback
from multiprocessing import Pool

from constants import *
from context import ProcessingContext
from custom_exceptions import *
from esgprep.utils.misc import load, store, evaluate, checksum, ProcessContext, Print, COLORS
from handler import File, DRSPath


def process(source):
    """
    process(collector_input)

    File process that:

     * Handles files,
     * Deduces facet key, values pairs from file attributes
     * Checks facet values against CV,
     * Applies the versioning
     * Populates the DRS tree crating the appropriate leaves,
     * Stores dataset statistics.


    :param str source: The file full path to process

    """
    # Get process content from process global env
    assert 'pctx' in globals().keys()
    pctx = globals()['pctx']
    # Block to avoid program stop if a thread fails
    try:
        # Instantiate file handler
        fh = File(source)
        # Ignore files from incoming
        if fh.filename in pctx.ignore_from_incoming:
            return False
        # Loads attributes from filename, netCDF attributes, command-line
        fh.load_attributes(root=pctx.root,
                           pattern=pctx.pattern,
                           set_values=pctx.set_values)
        # Checks the facet values provided by the loaded attributes
        fh.check_facets(facets=pctx.facets,
                        config=pctx.cfg,
                        set_keys=pctx.set_keys)
        # Get parts of DRS path
        parts = fh.get_drs_parts(pctx.facets)
        # Instantiate file DRS path handler
        fph = DRSPath(parts)
        # Ensure that the called project section is ALWAYS part of the DRS path elements (case insensitive)
        if not fph.path().lower().startswith(pctx.project.lower()):
            raise InconsistentDRSPath(pctx.project, fph.path())
        # If a latest version already exists make some checks FIRST to stop files to not process
        if fph.v_latest:
            # Latest version should be older than upgrade version
            if int(DRSPath.TREE_VERSION[1:]) <= int(fph.v_latest[1:]):
                raise OlderUpgrade(DRSPath.TREE_VERSION, fph.v_latest)
            # Walk through the latest dataset version to check its uniqueness with file checksums
            if not pctx.no_checksum:
                dset_nid = fph.path(f_part=False, latest=True, root=True)
                if dset_nid not in pctx.tree.hash.keys():
                    pctx.tree.hash[dset_nid] = dict()
                    pctx.tree.hash[dset_nid]['latest'] = dict()
                    for root, _, filenames in os.walk(fph.path(f_part=False, latest=True, root=True)):
                        for filename in filenames:
                            pctx.tree.hash[dset_nid]['latest'][filename] = checksum(os.path.join(root, filename),
                                                                                    pctx.checksum_type)
            # Pickup the latest file version
            latest_file = os.path.join(fph.path(latest=True, root=True), fh.filename)
            # Check latest file if exists
            if os.path.exists(latest_file):
                latest_checksum = checksum(latest_file, pctx.checksum_type)
                current_checksum = checksum(fh.ffp, pctx.checksum_type)
                # Check if processed file is a duplicate in comparison with latest version
                if latest_checksum == current_checksum:
                    fh.is_duplicate = True
        # Start the tree generation
        if not fh.is_duplicate:
            # Add the processed file to the "vYYYYMMDD" node
            src = ['..'] * len(fph.items(d_part=False))
            src.extend(fph.items(d_part=False, file_folder=True))
            src.append(fh.filename)
            pctx.tree.create_leaf(nodes=fph.items(root=True),
                                  leaf=fh.filename,
                                  label='{}{}{}'.format(fh.filename, LINK_SEPARATOR, os.path.join(*src)),
                                  src=os.path.join(*src),
                                  mode='symlink',
                                  origin=fh.ffp)
            # Add the "latest" node for symlink
            pctx.tree.create_leaf(nodes=fph.items(f_part=False, version=False, root=True),
                                  leaf='latest',
                                  label='{}{}{}'.format('latest', LINK_SEPARATOR, fph.v_upgrade),
                                  src=fph.v_upgrade,
                                  mode='symlink')
            # Add the processed file to the "files" node
            pctx.tree.create_leaf(nodes=fph.items(file_folder=True, root=True),
                                  leaf=fh.filename,
                                  label=fh.filename,
                                  src=fh.ffp,
                                  mode=pctx.mode)
            if pctx.upgrade_from_latest:
                # Walk through the latest dataset version and create a symlink for each file with a different
                # filename than the processed one
                for root, _, filenames in os.walk(fph.path(f_part=False, latest=True, root=True)):
                    for filename in filenames:
                        # Add latest files as tree leaves with version to upgrade instead of latest version
                        # i.e., copy latest dataset leaves to Tree
                        # Except if file has be ignored from latest version (i.e., with known issue)
                        if filename != fh.filename and filename not in pctx.ignore_from_latest:
                            src = os.path.join(root, filename)
                            pctx.tree.create_leaf(nodes=fph.items(root=True),
                                                  leaf=filename,
                                                  label='{}{}{}'.format(filename, LINK_SEPARATOR, os.readlink(src)),
                                                  src=os.readlink(src),
                                                  mode='symlink',
                                                  origin=os.path.realpath(src))
        else:
            # Pickup the latest file version
            latest_file = os.path.join(fph.path(latest=True, root=True), fh.filename)
            if pctx.upgrade_from_latest:
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
                pctx.tree.create_leaf(nodes=fph.items(root=True),
                                      leaf=fh.filename,
                                      label='{}{}{}'.format(fh.filename, LINK_SEPARATOR, src),
                                      src=src,
                                      mode='symlink',
                                      origin=fh.ffp)
                if pctx.mode == 'move':
                    pctx.tree.duplicates.append(fh.ffp)
        # Record entry for list()
        incoming = {'src': fh.ffp,
                    'dst': fph.path(root=True),
                    'filename': fh.filename,
                    'latest': fph.v_latest or 'Initial',
                    'size': fh.size}
        if fph.path(f_part=False) in pctx.tree.paths.keys():
            pctx.tree.paths[fph.path(f_part=False)].append(incoming)
        else:
            pctx.tree.paths[fph.path(f_part=False)] = [incoming]
        msg = COLORS.OKGREEN + '\n{}'.format(fph.path(f_part=False)) + COLORS.ENDC
        msg += '<-- ' + COLORS.HEADER + fh.filename + COLORS.ENDC
        with pctx.lock:
            Print.info(msg)
        return True
    except KeyboardInterrupt:
        raise
    except Exception:
        exc = traceback.format_exc().splitlines()
        msg = COLORS.HEADER + source + COLORS.ENDC + '\n'
        msg += '\n'.join(exc)
        with pctx.lock:
            Print.exception(msg, buffer=True)
        return None
    finally:
        with pctx.lock:
            pctx.progress.value += 1
            percentage = int(pctx.progress.value * 100 / pctx.nbsources)
            msg = COLORS.OKBLUE + '\rScanning incoming file(s): ' + COLORS.ENDC
            msg += '{}% | {}/{} file(s)'.format(percentage, pctx.progress.value, pctx.nbsources)
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

     * Instantiates processing context,
     * Loads previous program instance,
     * Parallelizes file processing with threads pools,
     * Apply command-line action to the whole DRS tree,
     * Evaluate exit status.

    :param ArgumentParser args: The command-line arguments parser

    """
    # TODO: Revise multiprocessing output if treelib not thread safe.
    # Init print management
    Print.init(log=args.log, debug=args.debug, cmd=args.prog)
    # Instantiate processing context
    with ProcessingContext(args) as ctx:
        # Print command-line
        Print.command(COLORS.OKBLUE + 'Command: ' + COLORS.ENDC + ' '.join(sys.argv))
        # Init process context
        cctx = {name: getattr(ctx, name) for name in PROCESS_VARS}
        if not ctx.scan:
            msg = COLORS.BOLD + 'Skip incoming files scan (use "--rescan" to force it) -- '
            msg += 'Using cached DRS tree from {}'.format(TREE_FILE) + COLORS.ENDC
            Print.warning(msg)
            reader = load(TREE_FILE)
            _ = reader.next()
            cctx['tree'] = reader.next()
            ctx.scan_err_log = reader.next()
            results = reader.next()
            # Rollback --commands_file value to command-line argument in any case
            cctx['tree'].commands_file = ctx.commands_file
        else:
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
        # Flush buffer
        Print.flush()
        # Get number of files scanned (excluding errors/skipped files)
        ctx.scan_files = len(filter(None, results))
        # Get number of scan errors
        ctx.scan_errors = results.count(None)
        # Backup tree context for later usage with other command lines
        store(TREE_FILE, data=[{key: ctx.__getattribute__(key) for key in CONTROLLED_ARGS},
                               cctx['tree'],
                               ctx.scan_err_log,
                               results])
        Print.warning('DRS tree recorded for next usage onto {}.'.format(TREE_FILE))
        # Evaluates the scan results to trigger the DRS tree action
        if evaluate(results):
            # Check upgrade uniqueness
            if not ctx.no_checksum:
                cctx['tree'].check_uniqueness(ctx.checksum_type)
            # Apply tree action
            cctx['tree'].get_display_lengths()
            getattr(cctx['tree'], ctx.action)()
    # Evaluate errors and exit with appropriated return code
    if not ctx.scan_files and not ctx.scan_errors:
        # Results list is empty = no files scanned/found
        sys.exit(2)
    if ctx.scan_files and ctx.scan_errors:
        # Print number of scan errors in any case
        if ctx.scan_errors == ctx.scan_files:
            # All files have been skipped or failed during the scan
            sys.exit(-1)
        else:
            # Some files have been skipped or failed during the scan
            sys.exit(1)
