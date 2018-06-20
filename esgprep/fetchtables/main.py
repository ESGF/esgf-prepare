#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import logging
import os
import sys
import traceback

import requests

from constants import *
from context import ProcessingContext
from esgprep.utils.custom_exceptions import GitHubReferenceNotFound
from esgprep.utils.misc import gh_request_content, backup, write_content, do_fetching, Print, COLORS


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
            msg = COLORS.BOLD + 'Cannot use "{}" (OSError {}: {}) -- '.format(tables_dir, e.errno, e.strerror)
            msg += 'Use "{}" instead.'.format(os.getcwd()) + COLORS.ENDC
            Print.warning(msg)
            outdir = os.path.join(os.getcwd(), repository)
            if reference:
                outdir = os.path.join(outdir, reference)
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
                Print.warning('"{}" created'.format(outdir))
    return outdir


def run(args):
    """
    Main process that:

     * Decide to fetch or not depending on file presence/absence and command-line arguments,
     * Gets the GitHub file content from full API URL,
     * Backups old file if desired,
     * Writes response into table file.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Init print management
    Print.init(log=args.log, debug=args.debug, cmd=args.prog)
    # Instantiate processing context manager
    with ProcessingContext(args) as ctx:
        # Print command-line
        Print.command(COLORS.OKBLUE + 'Command: ' + COLORS.ENDC + ' '.join(sys.argv))
        for project in ctx.targets:
            try:
                # Set repository name
                repo = REPO_PATTERN.format(project)
                # Set refs url
                url = ctx.ref_url.format(repo)
                # Get the list of available refs
                r = gh_request_content(url=url, auth=ctx.auth)
                refs = [os.path.basename(ref['url']) for ref in r.json()]
                if ctx.ref not in refs:
                    raise GitHubReferenceNotFound(ctx.ref, refs)
                # Build output directory
                if not ctx.no_ref_folder:
                    outdir = make_outdir(ctx.tables_dir, repo, ctx.ref)
                else:
                    outdir = make_outdir(ctx.tables_dir, repo)
                # Set repository url
                url = ctx.url.format(repo)
                url += GITHUB_API_PARAMETER.format('ref', ctx.ref)
                # Get the list of files to fetch
                r = gh_request_content(url=url, auth=ctx.auth)
                files = [f['name'] for f in r.json() if ctx.file_filter(f['name'])]
                # Init progress bar
                nfiles = len(files)
                if not nfiles:
                    Print.warning('No files found on remote repository: {}'.format(url))
                # Counter
                progress = 0
                for f in files:
                    try:
                        # Set output file full path
                        outfile = os.path.join(outdir, f)
                        # Set full file url
                        url = ctx.url.format(repo)
                        url += '/{}'.format(f)
                        # Particular case of CMIP6_CV.json file
                        # which has to be fetched from master in any case
                        if f == 'CMIP6_CV.json':
                            url += GITHUB_API_PARAMETER.format('ref', 'master')
                        else:
                            url += GITHUB_API_PARAMETER.format('ref', ctx.ref)
                        # Get GitHub file content
                        r = gh_request_content(url=url, auth=ctx.auth)
                        sha = r.json()['sha']
                        content = requests.get(r.json()['download_url'], auth=ctx.auth).text
                        # Fetching True/False depending on flags and file checksum
                        if do_fetching(outfile, sha, ctx.keep, ctx.overwrite):
                            # Backup old file if exists
                            backup(outfile, mode=ctx.backup_mode)
                            # Write new file
                            write_content(outfile, content)
                            Print.info(':: FETCHED :: {} --> {}'.format(url.ljust(LEN_URL), outfile))
                        else:
                            Print.info(':: SKIPPED :: {}'.format(url.ljust(LEN_URL)))
                    except KeyboardInterrupt:
                        raise
                    except Exception:
                        exc = traceback.format_exc().splitlines()
                        msg = COLORS.HEADER + project + COLORS.ENDC + '\n'
                        msg += '\n'.join(exc)
                        Print.exception(msg, buffer=True)
                        ctx.error = True
                    finally:
                        progress += 1
                        percentage = int(progress.value * 100 / ctx.nfiles)
                        msg = COLORS.OKBLUE + '\rFetching {} tables: '.format(project) + COLORS.ENDC
                        msg += '{}% | {}/{} files'.format(percentage, progress, ctx.nfiles)
                        Print.progress(msg)
            except Exception:
                exc = traceback.format_exc().splitlines()
                msg = COLORS.HEADER + project + COLORS.ENDC + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)
                ctx.error = True
    # Flush buffer
    Print.flush()
    # Evaluate errors and exit with appropriated return code
    if ctx.error:
        sys.exit(1)
