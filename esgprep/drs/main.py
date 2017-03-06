#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Manages the filesystem tree according to the project the Data Reference Syntax and versioning.

"""

import fnmatch
import logging
import os
import sys
from multiprocessing.dummy import Pool as ThreadPool

from esgprep.drs.constants import *
from esgprep.drs.exceptions import *
from esgprep.utils import parser, utils
from handler import File, DRSTree, DRSPath


class ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +------------------------+-------------+----------------------------------------------+
    | Attribute              | Type        | Description                                  |
    +========================+=============+==============================================+
    | *self*.directory       | *list*      | Paths to scan                                |
    +------------------------+-------------+----------------------------------------------+
    | *self*.root            | *str*       | The DRS root directory                       |
    +------------------------+-------------+----------------------------------------------+
    | *self*.filter          | *re object* | File filter as regex pattern                 |
    +------------------------+-------------+----------------------------------------------+
    | *self*.set_facets      | *re object* | Facets pairs to set                          |
    +------------------------+-------------+----------------------------------------------+
    | *self*.action          | *str*       | DRS action                                   |
    +------------------------+-------------+----------------------------------------------+
    | *self*.mode            | *str*       | File migration mode                          |
    +------------------------+-------------+----------------------------------------------+
    | *self*.version         | *str*       | Set upgrade version                          |
    +------------------------+-------------+----------------------------------------------+
    | *self*.verbose         | *boolean*   | True if verbose mode                         |
    +------------------------+-------------+----------------------------------------------+
    | *self*.project         | *str*       | Project                                      |
    +------------------------+-------------+----------------------------------------------+
    | *self*.project_section | *str*       | Project section name in configuration file   |
    +------------------------+-------------+----------------------------------------------+
    | *self*.checksum_client | *str*       | Checksum client as shell command-line to use |
    +------------------------+-------------+----------------------------------------------+
    | *self*.checksum_type   | *str*       | Checksum type                                |
    +------------------------+-------------+----------------------------------------------+
    | *self*.threads         | *int*       | Maximum threads number                       |
    +------------------------+-------------+----------------------------------------------+
    | *self*.cfg             | *callable*  | Configuration file parser                    |
    +------------------------+-------------+----------------------------------------------+
    | *self*.pattern         | *re object* | DRS regex pattern                            |
    +------------------------+-------------+----------------------------------------------+
    | *self*.facets          | *list*      | List of the DRS facets                       |
    +------------------------+-------------+----------------------------------------------+

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.directory = args.directory
        self.root = os.path.normpath(args.root)
        self.filter = args.filter
        self.set_facets = {}
        if args.set:
            self.set_facets = dict(args.set)
        self.threads = args.max_threads
        self.project = args.project
        self.action = args.action
        if args.copy:
            self.mode = 'copy'
        elif args.link:
            self.mode = 'link'
        else:
            self.mode = 'move'
        self.version = args.version
        DRSPath.VERSION = 'v{0}'.format(args.version)
        self.project_section = 'project:{0}'.format(args.project)
        self.cfg = parser.CfgParser(args.i, self.project_section)
        if args.no_checksum:
            self.checksum_client, self.checksum_type = None, None
        elif self.cfg.has_option('DEFAULT', 'checksum'):
            self.checksum_client, self.checksum_type = self.cfg.get_options_from_table('DEFAULT', 'checksum')[0]
        else:  # Use SHA256 as default because esg.ini not mandatory in configuration directory
            self.checksum_client, self.checksum_type = 'sha256sum', 'SHA256'
        self.facets = self.cfg.get_facets(self.project_section, 'directory_format')
        self.pattern = self.cfg.translate_filename_format(self.project_section)
        self.verbose = args.v
        self.tree = DRSTree(self.root)


def yield_inputs(ctx):
    """
    Yields all files to process within tuples with the processing context. The file walking
    through the DRS tree follows the symlinks.

    :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
    :returns: Attach the processing context to a file to process as an iterator of tuples
    :rtype: *iter*

    """
    for directory in ctx.directory:
        # Walk trough the submitted tree
        for root, _, filenames in utils.walk(directory, followlinks=True):
            for filename in filenames:
                ffp = os.path.join(root, filename)
                if os.path.isfile(ffp) and fnmatch.fnmatchcase(filename, ctx.filter):
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
    # Instanciate dataset DRS path handler
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
        for root, _, filenames in utils.walk(os.path.join(fph.path(f_part=False, latest=True, root=True))):
            for filename in filenames:
                # Add latest files as tree leaves with version to upgrade instead of latest version
                # i.e., copy latest dataset leaves to Tree
                if filename != fh.filename:
                    src = os.readlink(os.path.join(root, filename))
                    ctx.tree.create_leaf(nodes=fph.items(root=True),
                                         leaf='{0}{1}{2}'.format(filename, LINK_SEPARATOR, src),
                                         src=src,
                                         mode='symlink')
    else:
        fph.v_latest = 'Initial'
    # Add file DRS path to Tree
    src = ['..'] * len(fph.items(d_part=False, file=False))
    src.extend(fph.items(d_part=False, latest=True, file=True))
    src.append(fh.filename)
    ctx.tree.create_leaf(nodes=fph.items(root=True),
                         leaf='{0}{1}{2}'.format(fh.filename, LINK_SEPARATOR, os.path.join(*src)),
                         src=os.path.join(*src),
                         mode='symlink')
    # Add "latest" node for symlink
    ctx.tree.create_leaf(nodes=fph.items(f_part=False, version=False, root=True),
                         leaf='{0}{1}{2}'.format('latest', LINK_SEPARATOR, fph.v_upgrade),
                         src=fph.v_upgrade,
                         mode='symlink')
    # Add "files" node to Tree
    ctx.tree.create_leaf(nodes=fph.items(file=True, root=True),
                         leaf=fh.filename,
                         src=fh.ffp,
                         mode=ctx.mode)
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
    # Process supplied files
    outfiles = [x for x in pool.imap(wrapper, yield_inputs(ctx))]
    # Raises exception when all processed files failed (i.e., filtered list empty)
    if not all(outfiles):
        logging.warning('==> All files have been ignored or have failed leading to no tree.')
        sys.exit(1)
    else:
        if outfiles:
            # Save current directory
            cwd = os.getcwd()
            # Change current directory -> DRS root directory
            os.chdir(ctx.root)
            # Apply tree action
            ctx.tree.get_display_lengths()
            getattr(ctx.tree, ctx.action)()
            # Back to initial working directory
            os.chdir(cwd)
        else:
            logging.info('==> No files found.')
