#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import logging
import os
import sys
import re

import requests
from tqdm import tqdm

from constants import *
from context import ProcessingContext
from esgprep.utils.custom_exceptions import GitHubException, GitHubReferenceNotFound
from esgprep.utils.misc import gh_request_content, backup, write_content, do_fetching


def make_outdir(tables_dir, repository, reference=None):
    """
    Build the output directory.

    :param str tables_dir: The CMOR tables directory submitted
    :param str repository: The GitHub repository name
    :param str reference: The GitHub reference name (tag or branch)

    """

    outdir = os.path.join(tables_dir, repository)
    if reference:
        outdir = os.path.join(outdir, reference)
    # If directory does not already exist
    if not os.path.isdir(outdir):
        try:
            os.makedirs(outdir)
            logging.warning('{} created'.format(outdir))
        except OSError as e:
            # If default tables directory does not exists and without write access
            print 'WARNING :: Cannot use "{}" because of OSError ({}: {}) -- ' \
                  'Use "{}" instead.'.format(tables_dir,
                                             e.errno,
                                             e.strerror,
                                             os.getcwd())
            outdir = os.path.join(os.getcwd(), repository)
            if reference:
                outdir = os.path.join(outdir, reference)
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
                logging.warning('{} created'.format(outdir))
    return outdir


def fetch_tables(ctx, project, repo, ref, special_cases={}):
    """
    Fetch all tables for a single reference (e.g. tag or branch)
    """

    # Build output directory
    if not ctx.no_ref_folder:
        outdir = make_outdir(ctx.tables_dir, repo, ref)
    else:
        outdir = make_outdir(ctx.tables_dir, repo)
    # Set repository url
    url = ctx.url.format(repo)
    url += GITHUB_API_PARAMETER.format('ref', ref)
    # Get the list of files to fetch
    r = gh_request_content(url=url, auth=ctx.auth)

    files_info = dict([(f['name'], f) for f in r.json() if ctx.file_filter(f['name'])])
    files = files_info.keys()
    files.sort()

    # Init progress bar
    nfiles = len(files)
    if ctx.pbar and nfiles:
        files = tqdm(files,
                     desc='Fetching {} tables'.format(project),
                     total=nfiles,
                     bar_format='{desc}: {percentage:3.0f}% | {n_fmt}/{total_fmt} files',
                     ncols=100,
                     file=sys.stdout)
    elif not nfiles:
        logging.info('No files found on remote repository')
    # Get the files

    for f in files:
        # Set output file full path
        outfile = os.path.join(outdir, f)

        if f in special_cases:
            file_info = special_cases[f]
        else:
            file_info = files_info[f]

        # Fetching True/False depending on flags and file checksum
        sha = file_info['sha']
        url = file_info['download_url']
        if do_fetching(outfile, sha, ctx.keep, ctx.overwrite):
            # Backup old file if exists
            backup(outfile, mode=ctx.backup_mode)
            # fetch content
            content = requests.get(url, auth=ctx.auth).text
            # Write new file
            write_content(outfile, content)
            logging.info('{} :: FETCHED (in {})'.format(url.ljust(LEN_URL), outfile))
        else:
            logging.info('{} :: SKIPPED'.format(url.ljust(LEN_URL)))


def get_special_cases(ctx, repo):

    """
    Get a dictionary of (filename -> file_info) pairs to be used for 
    named files in place of the file info from the general API call
    done for the directory.  file_info should contain at least
    the elements 'sha' and 'download_url'
    """

    # in fact there is one special case: 
    # the CMIP6_CV.json file is obtained from master

    f = 'CMIP6_CV.json'    
    url = ctx.url.format(repo)
    url += '/{}'.format(f)
    url += GITHUB_API_PARAMETER.format('ref', 'master')
    r = gh_request_content(url=url, auth=ctx.auth)

    return { f: r.json() }


def run(args):
    """
    Main process that:

     * Decide to fetch or not depending on file presence/absence and command-line arguments,
     * Gets the GitHub file content from full API URL,
     * Backups old file if desired,
     * Writes response into table file.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Instantiate processing context manager
    with ProcessingContext(args) as ctx:
        try:
            for project in ctx.targets:
                # Set repository name
                repo = REPO_PATTERN.format(project)
                # Set refs url
                url = ctx.ref_url.format(repo)
                # Get the list of available refs
                r = gh_request_content(url=url, auth=ctx.auth)
                all_refs = [os.path.basename(ref['url']) for ref in r.json()]
                if hasattr(ctx, 'ref'):
                    if ctx.ref not in all_refs:
                        raise GitHubReferenceNotFound(ctx.ref, all_refs)
                    fetch_refs = [ctx.ref]
                else:
                    fetch_refs = filter(re.compile(ctx.regex).match, all_refs)
                    logging.info('Available refs: %s' % sorted(all_refs))
                    logging.info('Selected refs: %s' % sorted(fetch_refs))
                    if not fetch_refs:
                        raise GitHubReferenceNotFound('(regex: %s)' % ctx.regex,
                                                      all_refs)
                for ref in fetch_refs:
                    logging.info('Fetching ref: %s' % ref)
                    fetch_tables(ctx, project, repo, ref,
                                 special_cases=get_special_cases(ctx, repo))

        except GitHubException as exc:
            ctx.error = exc.msg



