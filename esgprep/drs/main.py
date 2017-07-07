#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

"""

import logging
import os
import pickle
import sys
from multiprocessing.dummy import Pool as ThreadPool

from tqdm import tqdm

from esgprep.drs.constants import *
from esgprep.drs.exceptions import *
from esgprep.utils.collectors import Collector
from esgprep.utils.config import CfgParser
from handler import File, DRSTree, DRSPath


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.directory = args.directory
        self.root = os.path.normpath(args.root)
        self.set_values = {}
        if args.set_value:
            self.set_values = dict(args.set_value)
        self.set_keys = {}
        if args.set_key:
            self.set_keys = dict(args.set_key)
        self.threads = args.max_threads
        self.project = args.project
        self.action = args.action
        if args.copy:
            self.mode = 'copy'
        elif args.link:
            self.mode = 'link'
        elif args.symlink:
            self.mode = 'symlink'
        else:
            self.mode = 'move'
        self.version = args.version
        DRSPath.VERSION = 'v{0}'.format(args.version)
        self.project_section = 'project:{0}'.format(args.project)
        self.cfg = CfgParser(args.i, self.project_section)
        if args.no_checksum:
            self.checksum_client, self.checksum_type = None, None
        elif self.cfg.has_option('DEFAULT', 'checksum'):
            self.checksum_client, self.checksum_type = self.cfg.get_options_from_table('DEFAULT', 'checksum')[0]
        else:  # Use SHA256 as default because esg.ini not mandatory in configuration directory
            self.checksum_client, self.checksum_type = 'sha256sum', 'SHA256'
        self.facets = self.cfg.get_facets(self.project_section, 'directory_format')
        self.pattern = self.cfg.translate_filename_format(self.project_section)
        self.verbose = args.v
        self.tree = DRSTree(self.root, self.version, self.mode)


def yield_inputs(ctx, collector):
    """
    Yields all files to process within tuples with the processing context. The file walking
    through the DRS tree follows the symlinks.

    :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
    :param esgprep.utils.collector.Collector collector: The file collector
    :returns: Attach the processing context to a file to process as an iterator of tuples
    :rtype: *iter*

    """
    for ffp in collector:
        yield ffp, ctx


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
        shell = os.popen("{0} {1} | awk -F ' ' '{{ print $1 }}'".format(checksum_client, ffp))
        return shell.readline()[:-1]
    except:
        raise ChecksumFail(ffp, checksum_type)


def wrapper(inputs):
    """
    Transparent wrapper for pool map.

    :param tuple inputs: A tuple with the file path and the processing context
    :returns: The :func:`process` call
    :rtype: *callable*

    """
    # Extract file full path (ffp) and processing context (ctx) from inputs
    ffp, ctx = inputs
    try:
        return process(ffp, ctx)
    except Exception as e:
        # Use verbosity to raise the whole threads traceback errors
        if not ctx.verbose:
            logging.error('{0} skipped\n{1}: {2}'.format(ffp, e.__class__.__name__, e.message))
        else:
            logging.exception('{0} failed'.format(ffp))
        return None


def process(ffp, ctx):
    """
    process(ffp, ctx)

    File process that:

     * Deduce facet key, values pairs from file attributes
     * Build the DRS of the file
     * Build the DRS of the corresponding dataset
     * Apply the versioning
     * Build the whole DRS tree
     * Store dataset statistics into a dict.

    :param str ffp: The file full path
    :param esgprep.drs.main.ProcessingContext ctx: The processing context
    :return: True on success
    :rtype: *boolean*

    """
    # Instantiate file handler
    fh = File(ffp)
    # Matching between filename_format and filename
    fh.load_attributes(ctx)
    # Get parts of DRS path
    parts = fh.get_drs_parts(ctx)
    # Instanciate file DRS path handler
    fph = DRSPath(parts)
    # Add file DRS path to Tree
    src = ['..'] * len(fph.items(d_part=False))
    src.extend(fph.items(d_part=False, latest=True, file=True))
    src.append(fh.filename)
    ctx.tree.create_leaf(nodes=fph.items(root=True),
                         leaf=fh.filename,
                         label='{0}{1}{2}'.format(fh.filename, LINK_SEPARATOR, os.path.join(*src)),
                         src=os.path.join(*src),
                         mode='symlink')
    # Add "latest" node for symlink
    ctx.tree.create_leaf(nodes=fph.items(f_part=False, version=False, root=True),
                         leaf='latest',
                         label='{0}{1}{2}'.format('latest', LINK_SEPARATOR, fph.v_upgrade),
                         src=fph.v_upgrade,
                         mode='symlink')
    # Add "files" node to Tree
    ctx.tree.create_leaf(nodes=fph.items(file=True, root=True),
                         leaf=fh.filename,
                         label=fh.filename,
                         src=fh.ffp,
                         mode=ctx.mode)
    # If a latest version already exists
    if fph.v_latest:
        # Latest version should be older than upgrade version
        if int(DRSPath.VERSION[1:]) <= int(fph.v_latest[1:]):
            raise OlderUpgrade(DRSPath.VERSION, fph.v_latest, fph.path(f_part=False, version=False))
        # Check latest files
        if ctx.checksum_client:
            # Pickup the latest file version
            latest_file = os.path.join(fph.path(latest=True, root=True), fh.filename)
            # Compute checksums and compare between latest and upgrade versions
            latest_checksum = checksum(latest_file, ctx.checksum_type, ctx.checksum_client)
            current_checksum = checksum(fh.ffp, ctx.checksum_type, ctx.checksum_client)
            if latest_checksum == current_checksum:
                raise DuplicatedFile(latest_file, fh.ffp)
        # Walk through the latest dataset version
        for root, _, filenames in os.walk(os.path.join(fph.path(f_part=False, latest=True, root=True))):
            for filename in filenames:
                # Add latest files as tree leaves with version to upgrade instead of latest version
                # i.e., copy latest dataset leaves to Tree
                if filename != fh.filename:
                    src = os.readlink(os.path.join(root, filename))
                    ctx.tree.create_leaf(nodes=fph.items(root=True),
                                         leaf=filename,
                                         label='{0}{1}{2}'.format(filename, LINK_SEPARATOR, src),
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
    logging.info('{0} <-- {1}'.format(fph.path(f_part=False), fh.filename))
    return True


def check_args(args, old_args):
    """
    Checks command-line argument to avoid discrepancies between ``esgprep drs`` steps.
    
    :param argparse.Namespace args: The submitted arguments 
    :param argparse.Namespace old_args: The recorded arguments 
    :raises Error: If one argument differs
    
    """
    for k in set(args.__dict__) - set(IGNORED_ARGS):
        if args.__dict__[k] != old_args.__dict__[k]:
            logging.warning('Submitted value of "{0}" argument is different from recorded one:'
                            ' "{1}" instead of "{2}". File scan re-run...'.format(k,
                                                                                  args.__dict__[k],
                                                                                  old_args.__dict__[k]))
            return False
    return True


def load_context():
    """
    Loads a tree context backed up from previous ``esgprep drs list``run.

    :returns: The tree context
    :rtype: *tuple*
    """
    with open('/tmp/DRSTree.pkl', 'rb') as f:
        logging.warning('Load previous tree context')
        return pickle.load(f), pickle.load(f), pickle.load(f)


def backup_context(args, tree, results):
    """
    Records a tree context for later usage with other command lines.

    :param ArgumentParser args: Parsed command-line arguments
    :param esgprep.drs.handler.DRSTree tree: The DRS tree recorded
    :param list results: The file scan result

    """
    # Backup DRS Tree for later usage with other command lines
    with open(TREE_CTX, 'wb') as f:
        pickle.dump(args, f)
        pickle.dump(tree, f)
        pickle.dump(results, f)
        logging.warning('Tree context recorded for next usage')


def run(ctx, pool, progress_bar):
    """
    Runs the file scan and tree building.

    :param esgprep.drs.main.ProcessingContext ctx: The processing context
    :param multiprocessing.Pool pool: The pool of workers to run
    :param boolean progress_bar: True to display the progress bar
    :returns: The file scan result
    :rtype: *list*

    """
    # Instanciate file collector to walk through the tree
    collector = Collector(ctx.directory)
    if progress_bar:
        print('Collecting files...\r'),
        return [x for x in tqdm(pool.imap(wrapper, yield_inputs(ctx, collector)),
                                desc='Scanning incoming files'.ljust(LEN_MSG),
                                total=len(collector),
                                bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} files',
                                ncols=100,
                                file=sys.stdout)]
    else:
        return [x for x in pool.imap(wrapper, yield_inputs(ctx, collector))]


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
    # Instantiate processing context from command-line arguments or SYNDA job dictionary
    ctx = ProcessingContext(args)
    logging.info('==> Scan started')
    # Start threads pool over files list in supplied directory
    pool = ThreadPool(int(ctx.threads))
    # Load tree context if already exists
    if ctx.action != 'list' and os.path.isfile(TREE_CTX):
        old_args, old_tree, old_results = load_context()
        # Ensure that processing context is similar to previous step
        if not check_args(args, old_args):
            # If the tree context is different, silently redo the supplied files processing.
            results = run(ctx, pool, args.pbar)
        else:
            args, ctx.tree, results = old_args, old_tree, old_results
    else:
        # Process supplied files
        results = run(ctx, pool, args.pbar)
    # Backup tree context for later usage with other command lines
    backup_context(args, ctx.tree, results)
    # Close threads pool
    pool.close()
    pool.join()
    # Decline outputs depending on the scan results
    # Raise errors when one or several files have been skipped or failed
    if all(results) and any(results):
        # Results list contains only True value = all files have been successfully scanned
        logging.info('==> Scan completed ({0} file(s) scanned)'.format(len(results)))
        # Apply tree action
        ctx.tree.get_display_lengths()
        getattr(ctx.tree, ctx.action)()
        sys.exit(0)
    elif all(results) and not any(results):
        # Results list is empty = no files scanned/found
        logging.warning('==> No files found')
        sys.exit(1)
    elif not all(results) and any(results):
        # Results list contains some None values = some files have been skipped or failed during the scan
        # Print number of scan errors
        if args.pbar:
            print('{0}: {1} (see {2})'.format('Scan errors'.ljust(23),
                                              results.count(None),
                                              logging.getLogger().handlers[0].baseFilename))
        logging.warning('{0} file(s) have been skipped'.format(results.count(None)))
        logging.info('==> Scan completed ({0} file(s) scanned)'.format(len(results)))
        # Apply tree action
        ctx.tree.get_display_lengths()
        getattr(ctx.tree, ctx.action)()
        sys.exit(2)
    elif not all(results) and not any(results):
        # Results list contains only None values = all files have been skipped or failed during the scan
        # Print number of scan errors
        if args.pbar:
            print('{0}: {1} (see {2})'.format('Scan errors'.ljust(23),
                                              len(results),
                                              logging.getLogger().handlers[0].baseFilename))
        logging.warning('==> All files have been ignored or have failed leading to no DRS tree.')
        sys.exit(3)
