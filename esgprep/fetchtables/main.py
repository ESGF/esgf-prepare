#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import os
import sys
import traceback
import re

import requests
from constants import *
from context import ProcessingContext
from esgprep.utils.custom_exceptions import GitHubReferenceNotFound
from esgprep.utils.github import *
from esgprep.utils.custom_print import *
from esgprep.utils.misc import make_outdir


def fetch(project, url, root, repo, ref, auth, keep, overwrite, backup_mode, filter=None, no_ref_folder=True, special_cases=None):
    """
    Fetch all files for a single reference (e.g. tag or branch) of a GitHub repository

    """
    # Set repository url
    url = url.format(repo)
    url += GITHUB_API_PARAMETER.format('ref', ref)

    # Build output directory and output file
    if not no_ref_folder:
        outdir = make_outdir(root, repo)
    else:
        outdir = make_outdir(root, repo, ref)

    # Get GitHub file content
    r = gh_request_content(url=url, auth=auth)
    infos = dict([(f['name'], f) for f in r.json() if filter(f['name'])])
    files = infos.keys()
    progress = 0
    for f in files:
        try:
            if f in special_cases:
                info = special_cases[f]
            else:
                info = infos[f]
            outfile = os.path.join(outdir, f)
            sha = info['sha']
            download_url = info['download_url']
            # Fetching True/False depending on flags and file checksum
            if do_fetching(outfile, sha, keep, overwrite):
                # Backup old file if exists
                backup(outfile, mode=backup_mode)
                # Get content
                content = requests.get(download_url, auth=auth).text
                # Write new file
                write_content(outfile, content)
                Print.info(TAGS.FETCH + '{} --> {}'.format(url, outfile))
            else:
                Print.info(TAGS.SKIP + url)
            return 0
        except KeyboardInterrupt:
            raise
        except Exception:
            exc = traceback.format_exc().splitlines()
            msg = TAGS.FAIL
            msg += 'Fetching {}'.format(COLORS.HEADER(url)) + '\n'
            msg += '\n'.join(exc)
            Print.exception(msg, buffer=True)
            return 1
        finally:
            progress += 1
            percentage = int(progress * 100 / nfiles)
            msg = COLORS.OKBLUE('\rFetching {} tables: '.format(project))
            msg += '{}% | {}/{} files'.format(percentage, progress, nfiles)
            Print.progress(msg)
    Print.progress('\n')


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
    # Get number of files
    nfiles = len(files)
    if not nfiles:
        Print.warning('No files found on remote repository: {}'.format(url))
    # Get the files
    for f in files:
        try:
            # Set output file full path
            outfile = os.path.join(outdir, f)
            if f in special_cases:
                file_info = special_cases[f]
            else:
                file_info = files_info[f]

            # Fetching True/False depending on flags and file checksum
            sha = file_info['sha']
            url = file_info['download_url']
            # Fetching True/False depending on flags and file checksum
            if do_fetching(outfile, sha, ctx.keep, ctx.overwrite):
                # Backup old file if exists
                backup(outfile, mode=ctx.backup_mode)
                # fetch content
                content = requests.get(url, auth=ctx.auth).text
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
                    fetch_refs = [ctx.ref]
                else:
<<<<<<< HEAD
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
=======
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



>>>>>>> devel
