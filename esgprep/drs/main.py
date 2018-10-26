#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

"""

import itertools
import traceback
from multiprocessing import Pool

from constants import *
from context import ProcessingContext
from custom_exceptions import *
from esgprep.utils.custom_print import *
from esgprep.utils.misc import load, store, evaluate, checksum, ProcessContext, get_tracking_id
from handler import File, DRSPath, DRSTree


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
            msg = TAGS.SKIP + COLORS.HEADER(source)
            with pctx.lock:
                Print.exception(msg, buffer=True)
            return None
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
        fh.drs = DRSPath(parts)
        # Ensure that the called project section is ALWAYS part of the DRS path elements (case insensitive)
        if not fh.drs.path().lower().startswith(pctx.project.lower()):
            raise InconsistentDRSPath(pctx.project, fh.drs.path())
        # Compute file checksum
        if fh.drs.v_latest and not pctx.no_checksum:
            fh.checksum = checksum(fh.ffp, pctx.checksum_type)
        # Get file tracking id
        fh.tracking_id = get_tracking_id(fh.ffp, pctx.project)
        if fh.drs.v_latest:
            latest_file = os.path.join(fh.drs.path(latest=True, root=True), fh.filename)
            # Compute checksum of latest file version if exists
            if os.path.exists(latest_file) and not pctx.no_checksum:
                fh.latest_checksum = checksum(latest_file, pctx.checksum_type)
            # Get tracking_id of latest file version if exists
            if os.path.exists(latest_file):
                fh.latest_tracking_id = get_tracking_id(latest_file, pctx.project)
        msg = TAGS.SUCCESS + 'Processing {}'.format(COLORS.HEADER(fh.ffp))
        Print.info(msg)
        return fh
    except KeyboardInterrupt:
        raise
    except Exception:
        exc = traceback.format_exc().splitlines()
        msg = TAGS.SKIP + COLORS.HEADER(source) + '\n'
        msg += '\n'.join(exc)
        with pctx.lock:
            Print.exception(msg, buffer=True)
        return None
    finally:
        with pctx.lock:
            pctx.progress.value += 1
            percentage = int(pctx.progress.value * 100 / pctx.nbsources)
            msg = COLORS.OKBLUE('\rScanning incoming file(s): ')
            msg += '{}% | {}/{} file(s)'.format(percentage, pctx.progress.value, pctx.nbsources)
            Print.progress(msg)


def tree_builder(fh):
    """
    Builds the DRS tree accord to a source

    :param esgprep.drs.handler.File fh: The file handler object

    """
    # Get process content from process global env
    assert 'pctx' in globals().keys()
    pctx = globals()['pctx']
    try:
        # If a latest version already exists make some checks FIRST to stop file process
        if fh.drs.v_latest:
            # Latest version should be older than upgrade version
            if int(DRSPath.TREE_VERSION[1:]) <= int(fh.drs.v_latest[1:]):
                raise OlderUpgrade(DRSPath.TREE_VERSION, fh.drs.v_latest)
            # Walk through the latest dataset version to check its uniqueness with file checksums
            if not pctx.no_checksum:
                dset_nid = fh.drs.path(f_part=False, latest=True, root=True)
                if dset_nid not in tree.hash.keys():
                    tree.hash[dset_nid] = dict()
                    tree.hash[dset_nid]['latest'] = dict()
                    for root, _, filenames in os.walk(fh.drs.path(f_part=False, latest=True, root=True)):
                        for filename in filenames:
                            tree.hash[dset_nid]['latest'][filename] = checksum(os.path.join(root, filename),
                                                                               pctx.checksum_type)
            # Pickup the latest file version
            latest_file = os.path.join(fh.drs.path(latest=True, root=True), fh.filename)
            # Check latest file if exists
            if os.path.exists(latest_file):
                if not pctx.no_checksum:
                    # If checksumming disabled duplicated files cannot be detected
                    # In this case, incoming files are assumed to be different in any cases
                    # Duplicated files should not exist.
                    # Check if processed file is a duplicate in comparison with latest version
                    if fh.latest_checksum == fh.checksum:
                        fh.is_duplicate = True
                if not fh.is_duplicate:
                    # If files are different check that PID/tracking_id is different from latest version
                    if fh.latest_tracking_id == fh.tracking_id:
                        raise UnchangedTrackingID(latest_file, fh.latest_tracking_id, fh.ffp, fh.tracking_id)

        # Start the tree generation
        if not fh.is_duplicate:
            # Add the processed file to the "vYYYYMMDD" node
            src = ['..'] * len(fh.drs.items(d_part=False))
            src.extend(fh.drs.items(d_part=False, file_folder=True))
            src.append(fh.filename)
            tree.create_leaf(nodes=fh.drs.items(root=True),
                             leaf=fh.filename,
                             label='{}{}{}'.format(fh.filename, LINK_SEPARATOR, os.path.join(*src)),
                             src=os.path.join(*src),
                             mode='symlink',
                             origin=fh.ffp,
                             force=True)
            # Add the "latest" node for symlink
            tree.create_leaf(nodes=fh.drs.items(f_part=False, version=False, root=True),
                             leaf='latest',
                             label='{}{}{}'.format('latest', LINK_SEPARATOR, fh.drs.v_upgrade),
                             src=fh.drs.v_upgrade,
                             mode='symlink')
            # Add the processed file to the "files" node
            tree.create_leaf(nodes=fh.drs.items(file_folder=True, root=True),
                             leaf=fh.filename,
                             label=fh.filename,
                             src=fh.ffp,
                             mode=pctx.mode)
            if fh.drs.v_latest and pctx.upgrade_from_latest:
                # Walk through the latest dataset version and create a symlink for each file with a different
                # filename than the processed one
                for root, _, filenames in os.walk(fh.drs.path(f_part=False, latest=True, root=True)):
                    for filename in filenames:
                        # Add latest files as tree leaves with version to upgrade instead of latest version
                        # i.e., copy latest dataset leaves to Tree
                        # Except if file has be ignored from latest version (i.e., with known issue)
                        # Except if file leaf has already been created to avoid overwriting new version
                        # leaf will be not create if already exists
                        if filename != fh.filename and filename not in pctx.ignore_from_latest:
                            src = os.path.join(root, filename)
                            tree.create_leaf(nodes=fh.drs.items(root=True),
                                             leaf=filename,
                                             label='{}{}{}'.format(filename, LINK_SEPARATOR, os.readlink(src)),
                                             src=os.readlink(src),
                                             mode='symlink',
                                             origin=os.path.realpath(src))

        else:
            # Pickup the latest file version
            latest_file = os.path.join(fh.drs.path(latest=True, root=True), fh.filename)
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
                tree.create_leaf(nodes=fh.drs.items(root=True),
                                 leaf=fh.filename,
                                 label='{}{}{}'.format(fh.filename, LINK_SEPARATOR, src),
                                 src=src,
                                 mode='symlink',
                                 origin=fh.ffp)
                if pctx.mode == 'move':
                    tree.duplicates.append(fh.ffp)
        # Record entry for list()
        record = {'src': fh.ffp,
                  'dst': fh.drs.path(root=True),
                  'filename': fh.filename,
                  'latest': fh.drs.v_latest or 'Initial',
                  'size': fh.size}
        if fh.drs.path(f_part=False) in tree.paths.keys():
            tree.paths[fh.drs.path(f_part=False)].append(record)
        else:
            tree.paths[fh.drs.path(f_part=False)] = [record]
        msg = TAGS.SUCCESS + 'DRS Path = {}'.format(COLORS.HEADER(fh.drs.path(f_part=False)))
        msg += ' <-- ' + fh.filename
        Print.info(msg)
        return True
    except KeyboardInterrupt:
        raise
    except Exception:
        exc = traceback.format_exc().splitlines()
        msg = TAGS.FAIL + 'Build {}'.format(COLORS.HEADER(fh.drs.path())) + '\n'
        msg += '\n'.join(exc)
        Print.exception(msg, buffer=True)
        return None
    finally:
        pctx.progress.value += 1
        percentage = int(pctx.progress.value * 100 / pctx.nbsources)
        msg = COLORS.OKBLUE('\rBuilding DRS tree: ')
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


def do_scanning(ctx):
    """
    Returns True if file scanning is necessary regarding command-line arguments

    :param esgprep.drs.context.ProcessingContext ctx: New processing context to evaluate
    :returns: True if file scanning is necessary
    :rtype: *boolean*
    """
    if ctx.rescan:
        return True
    elif ctx.action == 'list':
        return True
    elif os.path.isfile(TREE_FILE):
        reader = load(TREE_FILE)
        old_args = reader.next()
        # Ensure that processing context is similar to previous step
        for k in CONTROLLED_ARGS:
            if getattr(ctx, k) != old_args[k]:
                msg = '"{}" argument has changed: "{}" instead of "{}" -- '.format(k,
                                                                                   getattr(ctx, k),
                                                                                   old_args[k])
                msg += 'Rescanning files.'
                Print.warning(msg)
                return True
        return False
    else:
        return True


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
        # Init global variable
        global tree
        # Init DRS tree
        tree = DRSTree(ctx.root, ctx.version, ctx.mode, ctx.commands_file)
        # Init process context
        cctx = {name: getattr(ctx, name) for name in PROCESS_VARS}
        # Disable file scan if a previous DRS tree have generated using same context and no "list" action
        if do_scanning(ctx):
            if ctx.use_pool:
                # Init processes pool
                pool = Pool(processes=ctx.processes, initializer=initializer, initargs=(cctx.keys(), cctx.values()))
                processes = pool.imap(process, ctx.sources)
            else:
                initializer(cctx.keys(), cctx.values())
                processes = itertools.imap(process, ctx.sources)
            # Process supplied sources
            handlers = [x for x in processes]
            # Close pool of workers if exists
            if 'pool' in locals().keys():
                locals()['pool'].close()
                locals()['pool'].join()
            Print.progress('\n')
            # Build DRS tree
            cctx['progress'].value = 0
            initializer(cctx.keys(), cctx.values())
            handlers = [h for h in handlers if h is not None]
            results = [x for x in itertools.imap(tree_builder, handlers)]
            Print.progress('\n')
        else:
            reader = load(TREE_FILE)
            msg = 'Skip incoming files scan (use "--rescan" to force it) -- '
            msg += 'Using cached DRS tree from {}'.format(TREE_FILE)
            Print.warning(msg)
            _ = reader.next()
            tree = reader.next()
            handlers = reader.next()
            results = reader.next()
        # Flush buffer
        Print.flush()
        # Rollback --commands-file value to command-line argument in any case
        tree.commands_file = ctx.commands_file
        # Get number of files scanned (including errors/skipped files)
        ctx.scan_data = len(results)
        # Get number of scan errors
        ctx.scan_errors = results.count(None)
        # Backup tree context for later usage with other command lines
        store(TREE_FILE, data=[{key: ctx.__getattribute__(key) for key in CONTROLLED_ARGS},
                               tree,
                               handlers,
                               results])
        Print.info(TAGS.INFO + 'DRS tree recorded for next usage onto {}.'.format(COLORS.HEADER(TREE_FILE)))
        # Evaluates the scan results to trigger the DRS tree action
        if evaluate(results):
            # Check upgrade uniqueness
            if not ctx.no_checksum:
                tree.check_uniqueness(ctx.checksum_type)
            # Apply tree action
            tree.get_display_lengths()
            getattr(tree, ctx.action)()
    # Evaluate errors and exit with appropriated return code
    if ctx.scan_errors > 0:
        sys.exit(ctx.scan_errors)
