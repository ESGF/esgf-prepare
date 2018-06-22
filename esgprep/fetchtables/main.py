#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import os
import sys
import traceback

import requests
from constants import *
from context import ProcessingContext
from esgprep.utils.custom_exceptions import GitHubReferenceNotFound
from esgprep.utils.github import *
from esgprep.utils.custom_print import *


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
            Print.warning('{} created'.format(outdir))
        except OSError as e:
            # If default tables directory does not exists and without write access
            msg = 'Cannot use "{}" (OSError {}: {}) -- '.format(tables_dir, e.errno, e.strerror)
            msg += 'Use "{}" instead.'.format(os.getcwd())
            Print.warning(msg)
            outdir = os.path.join(os.getcwd(), repository)
            if reference:
                outdir = os.path.join(outdir, reference)
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
                Print.warning('{} created'.format(outdir))
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
        Print.command(' '.join(sys.argv))
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
                            msg = TAGS.FETCH
                            msg += '{} --> {}'.format(url, outfile)
                            Print.info(msg)
                        else:
                            msg = TAGS.SKIP
                            msg += '{}'.format(url)
                            Print.info(msg)
                    except KeyboardInterrupt:
                        raise
                    except Exception:
                        exc = traceback.format_exc().splitlines()
                        msg = TAGS.FAIL
                        msg += 'Fetching {}'.format(COLORS.HEADER(url)) + '\n'
                        msg += '\n'.join(exc)
                        Print.exception(msg, buffer=True)
                        ctx.error = True
                    finally:
                        progress += 1
                        percentage = int(progress * 100 / nfiles)
                        msg = COLORS.OKBLUE('\rFetching {} tables: '.format(project))
                        msg += '{}% | {}/{} files'.format(percentage, progress, nfiles)
                        Print.progress(msg)
                Print.progress('\n')
            except Exception:
                exc = traceback.format_exc().splitlines()
                msg = TAGS.FAIL
                msg += 'Fetching {} tables'.format(COLORS.HEADER(project)) + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)
                ctx.error = True
    # Flush buffer
    Print.flush()
    # Evaluate errors and exit with appropriated return code
    if ctx.error:
        sys.exit(1)
