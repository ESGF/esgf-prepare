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
from custom_exceptions import GitHubException
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


def run(args):
    """
    Main process that:

     * Decide to fetch or not depending on file presence/absence and command-line arguments,
     * Gets the GitHub file content from full API URL,
     * Backups old file if desired,
     * Writes response into INI file.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Instantiate processing context manager
    with ProcessingContext(args) as ctx:
        try:
            for project in ctx.targets:
                # Set full url
                url = ctx.url.format(INI_FILE.format(project))
                # Set output file full path
                outfile = os.path.join(ctx.config_dir, INI_FILE.format(project))
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
