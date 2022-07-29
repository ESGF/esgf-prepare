# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.github.py
   :platform: Unix
   :synopsis: Utilities for GitHub interaction.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import hashlib
from base64 import b64decode

import requests
from esgprep._utils.print import *


def fetch(url, outfile, auth, sha, keep, overwrite, backup_mode, blob=False):
    """
    Fetches a file from a GitHub repository.

    """
    # Evaluate if fetching required.
    if do_fetching(outfile, sha, keep, overwrite):

        # Backup existing file.
        backup(outfile, mode=backup_mode)

        # Fetch GitHub file content.
        if blob:
            content = b64decode(requests.get(url, auth=auth).json()['content']).decode()
        else:
            content = requests.get(url, auth=auth).text

        # Write content into file.
        write_content(outfile, content)

        Print.success(f'Fetched: {url} --> {outfile}')

    else:

        Print.error(f'Skipped: {url}')


def gh_request_content(url, auth=None):
    """
    Gets content from a GitHub URL.

    """
    # Set URL in GitHub Exception
    GitHubException.URI = url

    # URL get.
    r = requests.get(url, auth=auth)

    # Manage HTTP returned codes.
    # Success.
    if r.status_code == 200:
        return r

    # Unauthorized.
    elif r.status_code == 401:
        raise GitHubUnauthorized()

    # GitHub API rate limit.
    elif r.status_code == 403:
        raise GitHubAPIRateLimit(int(r.headers['X-RateLimit-Reset']))

    # File not found.
    elif r.status_code == 404:
        raise GitHubFileNotFound()

    # Other connection error.
    else:
        raise GitHubConnectionError()


def backup(f, mode=None):
    """
    Backup a local file following different modes:

     * "one_version" renames the existing file in its source directory adding a ".bkp" extension to the filename.
     * "keep_versions" moves the existing file in a child directory called "bkp" and add a timestamp to the filename.

    """
    if os.path.isfile(f):

        # "one_version" mode.
        if mode == 'one_version':

            # Add ".bkp" suffix.
            dst = f'{f}.bkp'

            # Rename existing file.
            os.rename(f, dst)

            Print.debug(f'Old "{f}" saved under "{dst}"')

        # "keep_versions" mode.
        elif mode == 'keep_versions':

            # Build backup directory.
            bkpdir = os.path.join(os.path.dirname(f), 'bkp')

            # Build destination file.
            dst = os.path.join(bkpdir, f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.{os.path.basename(f)}")

            # Make backup directory.
            try:
                os.makedirs(bkpdir)
            except OSError:
                pass
            finally:

                # Move/overwrite destination file.
                os.rename(f, dst)
                Print.debug(f'Old "{f}" saved under "{dst}"')

        else:

            # Default is no backup.
            pass


def write_content(outfile, content):
    """
    Write GitHub content into a file.

    """

    tmpfile = outfile + ".tmp"

    with open(tmpfile, 'w+') as f:
        f.write(content)

    try:
        os.rename(tmpfile, outfile)

    except OSError:
        os.remove(tmpfile)
        raise


def do_fetching(f, remote_checksum, keep, overwrite):
    """
    Returns True or False evaluating a decision schema to fetch a file.

    """
    # Fetch if overwrite set to True
    if overwrite:
        return True

    else:

        # Fetch if file does not exist.
        if not os.path.isfile(f):
            return True

        else:

            # Do not fetch if unchanged checksum.
            if githash(f) == remote_checksum:
                return False

            else:

                msg = f'Local "{os.path.basename(f)}" does not match version on GitHub -- '
                msg += 'The file is either outdated or was modified.'
                Print.debug(msg)

                # Fetch outdated/modified files is "keep" set to False.
                if keep:
                    return False
                else:
                    return True


def githash(outfile):
    """
    Computes SHA1 checksum in the same way as Git checksum (as called by "git hash-object").

    """
    with open(outfile) as f:
        data = f.read()
    s = hashlib.sha1()
    s.update(f"blob {len(data).encode('utf-8')}\0")
    s.update(data.encode('utf-8'))
    return s.hexdigest()
