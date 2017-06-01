#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import re
import logging
import sys
from datetime import datetime
from exceptions import *
from hashlib import sha1

from github3 import GitHub
from github3.models import GitHubError
from tqdm import tqdm

from constants import *
from esgprep.fetchini.exceptions import *
from esgprep.utils.parser import *


def github_connector(repository, username=None, password=None, team=None):
    """
    Instantiates the GitHub repository connector if granted.

    :param username: The GitHub login (optional)
    :param password: The GitHub password (optional)
    :param team: The GitHub team to connect (optional)
    :param repository: The GitHub repository to reach
    :returns: The GitHub repository connector
    :rtype: *github3.repos*
    :raises Error: If the GitHub connection fails because of invalid inputs
    :raises Error: If the GitHub connection fails because of API rate limit exceeded

    """

    try:
        return GitHub(username, password).repository(team, repository.lower())
    except GitHubError as e:
        raise GitHubConnectionError(e.msg, repository, username, password, team)


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
            dst = '{0}.bkp'.format(f)
            os.rename(f, dst)
        elif mode == 'keep_versions':
            bkpdir = os.path.join(os.path.dirname(f), 'bkp')
            dst = os.path.join(bkpdir, '{0}.{1}'.format(datetime.now().strftime('%Y%m%d-%H%M%S'),
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
    Write GitHub content into a file using context manager.
    
    :param str outfile: The output file 
    :param *github3.GitHub.repository.contents* content: The GitHub content
    
    """
    with open(outfile, 'w+') as f:
        f.write(content.decoded)


def gh_content(gh, path):
    """
    Gets the GitHub content of a file or a directory.

    :param github3.GitHub.repository gh: A :func:`github_connector` instance
    :param str path: The remote file or directory path
    :returns: The remote file or directory content
    :rtype: *github3.GitHub.repository.contents*
    :raises Error: If the GitHub request returns empty content

    """
    try:
        content = gh.contents(path)
        if not content:
            raise GitHubNoContent(gh.contents_urlt.expand(path=path))
    except GitHubError as e:
        raise GitHubConnectionError(e.msg, repository=gh.name, team=os.path.dirname(gh.full_name))
    return content


def target_projects(gh, projects=None):
    """
    Gets the available projects id from GitHub esg.*.ini files.

    :param github3.GitHub.repository gh: A :func:`github_connector` instance
    :param list projects: Desired project ids
    :returns: The target projects
    :rtype: *list*

    """
    pattern = 'esg\.(.+?)\.ini'
    files = gh_content(gh, path=GITHUB_DIRECTORY)
    p_avail = set([re.search(pattern, x).group(1) for x in files.keys() if re.search(pattern, x)])
    if projects:
        p = set(projects)
        p_avail = p_avail.intersection(p)
        if p.difference(p_avail):
            logging.warning("Unavailable project(s): {0}".format(', '.join(p.difference(p_avail))))
    return list(p_avail)


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
                logging.warning('Local "{0}" does not match version on GitHub. '
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


def fetch(gh, outdir, path, backup_mode, keep=False, overwrite=False):
    """
    Get corresponding file from GitHub
     
    :param *github3.repos* gh: The GitHub repository connector
    :param str outdir: The output directory
    :param str path: The GitHub path of the remote file
    :param str backup_mode: The backup mode
    :param boolean keep: True to keep existing files
    :param boolean overwrite: True to overwrite existing files
    
    """
    # Set output file full path
    outfile = os.path.join(outdir, os.path.basename(path))
    # Get file content
    content = gh_content(gh, path)
    if do_fetching(outfile, content.sha, keep, overwrite):
        # Backup old file if exists
        backup(outfile, mode=backup_mode)
        # Write new file
        write_content(outfile, content)
    logging.info('{0} --> {1}'.format(content.html_url, outfile))


def main(args):
    """
    Main process that:

     * Checks if output directory exists,
     * Checks if configuration already exists in output directory,
     * Tests the corresponding GitHub URL,
     * Gets the GitHub URL,
     * Writes response into INI file.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # If ESGF node and args.i = /esg/config/esgcet -> exists
    # If not ESGF node and args.i = /esg/config/esgcet -> doesn't exist -> use $PWD/ini instead
    # If ESGF node and args.i = other -> if not exists make it
    # If not ESGF node and args.i = other -> if not exists make it
    outdir = os.path.realpath(os.path.normpath(args.i))
    if not os.path.isdir(outdir):
        try:
            os.makedirs(outdir)
            logging.warning('{0} created'.format(outdir))
        except OSError:
            outdir = '{0}/ini'.format(os.getcwd())
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
                logging.warning('{0} created'.format(outdir))
    # Instantiate Github session
    gh = github_connector(repository=GITHUB_REPO, team=GITHUB_TEAM, username=args.gh_user, password=args.gh_password)
    logging.info('Connected to "{0}" GitHub repository '.format(GITHUB_REPO.lower()))

    # Get "remote" project targeted from the command-line
    projects = target_projects(gh, args.project)
    if args.pbar:
        for project in tqdm(projects,
                            desc='Fetching "esg.<project>.ini"',
                            total=len(projects),
                            bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} files',
                            ncols=100,
                            unit='files',
                            file=sys.stdout):
            path = os.path.join(GITHUB_DIRECTORY, 'esg.{0}.ini'.format(project))
            fetch(gh, outdir, path, args.b, args.k, args.o)
    else:
        for project in projects:
            path = os.path.join(GITHUB_DIRECTORY, 'esg.{0}.ini'.format(project))
            fetch(gh, outdir, path, args.b, args.k, args.o)
