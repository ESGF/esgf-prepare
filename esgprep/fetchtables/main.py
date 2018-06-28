#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import traceback

from constants import *
from context import ProcessingContext
from esgprep.utils.constants import GITHUB_API_PARAMETER
from esgprep.utils.github import *


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
            msg = 'Cannot use "{}" (OSError {}: {}) -- '.format(outdir, e.errno, e.strerror)
            msg += 'Use "{}" instead.'.format(os.getcwd())
            Print.warning(msg)
            outdir = os.path.join(os.getcwd(), repository)
            if reference:
                outdir = os.path.join(outdir, reference)
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
                Print.warning('"{}" created'.format(outdir))
    return outdir


def get_special_case(f, url, repo, ref, auth):
    """
    Get a dictionary of (filename -> file_info) pairs to be used for 
    named files in place of the file info from the general API call
    done for the directory.  file_info should contain at least
    the elements 'sha' and 'download_url'
    """
    url = url.format(repo)
    url += '/{}'.format(f)
    url += GITHUB_API_PARAMETER.format('ref', ref)
    r = gh_request_content(url=url, auth=auth)
    Print.debug('Set special GitHub reference -- "{}": "{}"'.format(f, ref))
    return {f: r.json()}


def fetch_gh_ref(url, outdir, auth, keep, overwrite, backup_mode, filter, special_cases=None):
    """
    Fetch all files for a single reference (e.g. tag or branch) of a GitHub repository

    """
    # Get GitHub file content
    r = gh_request_content(url=url, auth=auth)
    files = dict([(f['name'], f) for f in r.json() if filter(f['name'])])
    # Get number of files
    nfiles = len(files)
    if not nfiles:
        Print.warning('No files found on remote repository: {}'.format(url))
    # Counter
    progress = 0
    for f, info in files.items():
        try:
            # Overwrite info by special cases ones
            if special_cases and f in special_cases.keys():
                info = special_cases[f]
            # Set output file full path
            outfile = os.path.join(outdir, f)
            # Get checksum
            download_url = info['download_url']
            sha = info['sha']
            # Get GitHub file
            fetch(url=download_url,
                  outfile=outfile,
                  auth=auth,
                  sha=sha,
                  keep=keep,
                  overwrite=overwrite,
                  backup_mode=backup_mode)
        except KeyboardInterrupt:
            raise
        except Exception:
            download_url = info['download_url']
            exc = traceback.format_exc().splitlines()
            msg = TAGS.FAIL + COLORS.HEADER(download_url) + '\n'
            msg += '\n'.join(exc)
            Print.exception(msg, buffer=True)
        finally:
            project = re.search(REPO_NAME_PATTERN, url).group(1).split('/')[-1]
            ref = url.split('=')[-1]
            progress += 1
            percentage = int(progress * 100 / nfiles)
            msg = COLORS.OKBLUE('\rFetching {} tables from {} reference: '.format(project, ref))
            msg += '{}% | {}/{} files'.format(percentage, progress, nfiles)
            Print.progress(msg)
    Print.progress('\n')


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
        for project in ctx.project:
            try:
                # Set repository name
                repo = REPO_PATTERN.format(project)
                # Get the list of available refs for that repository
                r = gh_request_content(url=ctx.ref_url.format(repo), auth=ctx.auth)
                refs = [os.path.basename(ref['url']) for ref in r.json()]
                # Get refs to fetch
                if hasattr(ctx, 'ref'):
                    if ctx.ref not in refs:
                        raise GitHubReferenceNotFound(ctx.ref, refs)
                    fetch_refs = [ctx.ref]
                else:
                    fetch_refs = filter(re.compile(ctx.ref_regex).match, refs)
                    if not fetch_refs:
                        raise GitHubReferenceNotFound(ctx.ref_regex.pattern, refs)
                Print.debug('GitHub Available reference(s): {}'.format(', '.join(sorted(refs))))
                Print.info('Selected GitHub reference(s): {}'.format(', '.join(sorted(fetch_refs))))
                # Get special case for CMIP6_CV.json file
                special_cases = get_special_case(f='CMIP6_CV.json', url=ctx.url, repo=repo, ref='master', auth=ctx.auth)
                # Fetch each ref
                for ref in fetch_refs:
                    try:
                        # Set reference url
                        url = ctx.url.format(repo)
                        if ref:
                            url += GITHUB_API_PARAMETER.format('ref', ref)
                        Print.debug('Fetch {} tables from "{}" GitHub reference'.format(project, ref))
                        # Build output directory
                        if ctx.no_subfolder:
                            outdir = make_outdir(ctx.tables_dir, repo)
                        else:
                            outdir = make_outdir(ctx.tables_dir, repo, ref)
                        # Fetch GitHub reference
                        fetch_gh_ref(url=url,
                                     outdir=outdir,
                                     auth=ctx.auth,
                                     keep=ctx.keep,
                                     overwrite=ctx.overwrite,
                                     backup_mode=ctx.backup_mode,
                                     filter=ctx.file_filter,
                                     special_cases=special_cases)
                    except Exception:
                        exc = traceback.format_exc().splitlines()
                        msg = TAGS.FAIL
                        msg += 'Fetching {} tables from {} GitHub reference'.format(COLORS.HEADER(project),
                                                                                    COLORS.HEADER(ref)) + '\n'
                        msg += '\n'.join(exc)
                        Print.exception(msg, buffer=True)
                        ctx.error = True
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
