#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import logging
import os
from datetime import datetime
from hashlib import sha1

import requests

from constants import *
from context import ProcessingContext
from custom_exceptions import GitHubException, GitHubReferenceNotFound
from misc import gh_request_content


def backup(f, mode=None):
    """
    Backup a local file following different modes:

     * "one_version" renames the existing file in its source directory adding a ".bkp" extension to the filename.
     * "keep_versions" moves the existing file in a child directory called "bkp" and add a timestamp to the filename.

    :param str f: The file to backup
    :param str mode: The backup mode to follow

    """
    if os.path.isfile(f):
        if mode == 'one_version':
            dst = '{}.bkp'.format(f)
            os.rename(f, dst)
        elif mode == 'keep_versions':
            bkpdir = os.path.join(os.path.dirname(f), 'bkp')
            dst = os.path.join(bkpdir, '{}.{}'.format(datetime.now().strftime('%Y%m%d-%H%M%S'),
                                                      os.path.basename(f)))
            try:
                os.makedirs(bkpdir)
            except OSError:
                pass
            finally:
                # Overwritten silently if destination file already exists
                os.rename(f, dst)
        else:
            # No backup = default
            pass


def write_content(outfile, content):
    """
    Write GitHub content into a file.
    
    :param str outfile: The output file 
    :param str content: The file content to write
    
    """
    with open(outfile, 'w+') as f:
        f.write(content.encode('utf-8'))


def do_fetching(f, remote_checksum, keep, overwrite):
    """
    Returns True or False depending on decision schema

    :param str f: The file to test
    :param str remote_checksum: The remote file checksum
    :param boolean overwrite: True if overwrite existing files
    :param boolean keep: True if keep existing files
    :returns: True depending on the conditions
    :rtype: *boolean*

    """
    if overwrite:
        return True
    else:
        if not os.path.isfile(f):
            return True
        else:
            if githash(f) == remote_checksum:
                return False
            else:
                logging.warning('Local "{}" does not match version on GitHub. '
                                'The file is either outdated or was modified.'.format((os.path.basename(f))))
                if keep:
                    return False
                else:
                    return True


def githash(outfile):
    """
    Makes Git checksum (as called by "git hash-object") of a file

    :param outfile:
    :returns: The SHA1 sum

    """
    with open(outfile) as f:
        data = f.read()
    s = sha1()
    s.update("blob %u\0" % len(data))
    s.update(data)
    return unicode(s.hexdigest())


def make_outdir(outdir=None):
    """
    Build the output directory as follows:
     - If ESGF node and args.outdir = /usr/local/ -> exists
     - If not ESGF node and args.outdir = /esg/config/esgcet -> doesn't exist -> use $PWD/ini instead
     - If ESGF node and args.outdir = other -> if not exists make it
     - If not ESGF node and args.out = other -> if not exists make it

    :param str repo: The GitHub repository name
    :param str ref: The GitHub reference name
    :param str outdir: The local output directory submitted

    """
    # If directory does not already exist
    if not os.path.isdir(outdir):
        try:
            os.makedirs(outdir)
            logging.warning('{} created'.format(outdir))
        except OSError:
            raise OSError
            # outdir = '{}/ini'.format(os.getcwd())
            # if not os.path.isdir(self.config_dir):
            #     os.makedirs(self.config_dir)
            #     logging.warning('{} created'.format(self.config_dir))


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
                refs = [os.path.basename(ref['url']) for ref in r.json()]
                if ctx.ref not in refs:
                    raise GitHubReferenceNotFound(ctx.ref, refs)
                # Build output directory
                ctx.outdir = os.path.join(ctx.outdir, repo)
                if not ctx.no_ref_folder:
                    ctx.outdir = os.path.join(ctx.outdir, ctx.ref)
                make_outdir(ctx.outdir)
                # Set repository url
                url = ctx.url.format(repo)
                url += GITHUB_API_PARAMETER.format('ref', ctx.ref)
                # Get the list of files to fetch
                r = gh_request_content(url=url, auth=ctx.auth)
                files = [f['name'] for f in r.json() if ctx.file_filter(f)]
                # Get the files
                for f in files:
                    # Set output file full path
                    outfile = os.path.join(ctx.outdir, f)
                    # Set full file url
                    url = ctx.url.format(repo)
                    url += '/{}'.format(f)
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
                        logging.info('{} :: FETCHED (in {})'.format(url.ljust(LEN_URL), outfile))
                    else:
                        logging.info('{} :: SKIPPED'.format(url.ljust(LEN_URL)))
        except GitHubException:
            ctx.error = True
