#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to use with this package.

"""

import hashlib
import os
import re

import requests
from custom_exceptions import *


def get_checksum_pattern(checksum_type):
    """
    Build the checksum pattern depending on the checksum type.

    :param str checksum_type: The checksum type
    :return: The checksum pattern
    :rtype: *re.Object*

    """
    hash_algo = getattr(hashlib, checksum_type)()
    checksum_length = len(hash_algo.hexdigest())
    return re.compile('^[0-9a-f]{{{}}}$'.format(checksum_length))


def gh_request_content(url, auth=None):
    """
    Gets the GitHub content of a file or a directory.

    :param str url: The GitHub url to request
    :param *requests.auth.HTTPBasicAuth* auth: The authenticator object
    :returns: The GitHub request content
    :rtype: *requests.models.Response*
    :raises Error: If user not authorized to read GitHub repository
    :raises Error: If user exceed the GitHub API rate limit
    :raises Error: If the queried content does not exist
    :raises Error: If the GitHub request fails for other reasons

    """
    GitHubException.URI = url
    r = requests.get(url, auth=auth)
    if r.status_code == 200:
        return r
    elif r.status_code == 401:
        raise GitHubUnauthorized()
    elif r.status_code == 403:
        raise GitHubAPIRateLimit(int(r.headers['X-RateLimit-Reset']))
    elif r.status_code == 404:
        raise GitHubFileNotFound()
    else:
        raise GitHubConnectionError()


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
            msg = COLORS.BOLD + 'Old "{}" saved under "{}"'.format(f, dst) + COLORS.ENDC
            Print.debug(msg)
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
                msg = COLORS.BOLD + 'Old "{}" saved under "{}"'.format(f, dst) + COLORS.ENDC
                Print.debug(msg)
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
                msg = COLORS.BOLD + 'Local "{}" does not match version on GitHub -- '.format((os.path.basename(f)))
                msg += 'The file is either outdated or was modified.' + COLORS.ENDC
                Print.debug(msg)
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
    s = hashlib.sha1()
    s.update("blob %u\0" % len(data))
    s.update(data)
    return unicode(s.hexdigest())
