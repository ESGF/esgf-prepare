#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import logging
import sys
from datetime import datetime
from hashlib import sha1
from os.path import *

from exceptions import *
from github3 import GitHub
from github3.models import GitHubError
from tqdm import tqdm

from constants import *
from esgprep.fetchini.exceptions import *
from esgprep.utils.parser import *


def query_yes_no(question, default='no'):
    """
    Asks a yes/no question via raw_input() and return their answer.

    :param str question: The question string that is presented to the user
    :param str default: The default answer is the string if the user just hits the carriage return.
        If None an answer is required.
    :returns: The answer True or False
    :rtype: *boolean*
    :raises Error: If invalid default answer

    """
    # Dictionary of valid answers
    valid = {'yes': True, 'y': True, 'YES': True, 'Y': True, 'Yes': True,
             'no':  False, 'n': False, 'NO': False, 'N': False, 'No': False}
    # Modify prompt depending on the default value
    if default is None:
        prompt = '[y/n]'
    elif default == 'yes':
        prompt = '[Y/n]'
    elif default == 'no':
        prompt = '[y/N]'
    else:
        raise Exception('Invalid default answer: {0}'.format(default))
    while True:
        sys.stdout.write('{0} {1} '.format(question, prompt))
        choice = raw_input().lower().strip()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            # Ask again
            pass


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
    if isfile(f):
        if mode == 'one_version':
            dst = '{0}.bkp'.format(f)
            os.rename(f, dst)
        elif mode == 'keep_versions':
            bkpdir = join(dirname(f), 'bkp')
            dst = join(bkpdir, '{0}.{1}'.format(datetime.now().strftime('%Y%m%d-%H%M%S'), basename(f)))
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
        raise GitHubConnectionError(e.msg, repository=gh.name, team=dirname(gh.full_name))
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
    files = gh_content(gh, path='{0}/{1}'.format(GITHUB_DIRECTORY, 'ini'))
    p_avail = set([re.search(pattern, x).group(1) for x in files.keys() if re.search(pattern, x)])
    if projects:
        p = set(projects)
        p_avail = p_avail.intersection(p)
        if p.difference(p_avail):
            logging.warning("Unavailable project(s): {0}".format(', '.join(p.difference(p_avail))))
    return list(p_avail)


def target_handlers(gh, projects=None):
    """
    Gets the available handlers id from GitHub esg.*.ini files.

    :param github3.GitHub.repository gh: A :func:`github_connector` instance
    :param list projects: Desired project ids
    :returns: The target projects
    :rtype: *list*

    """
    pattern = '(.+?)_handler.py'
    files = gh_content(gh, path='{0}/{1}'.format(GITHUB_DIRECTORY, 'handlers'))
    h_avail = set([re.search(pattern, x).group(1) for x in files.keys() if re.search(pattern, x)])
    if projects:
        h = set(projects)
        h_avail = h_avail.intersection(h)
        if h.difference(h_avail):
            logging.warning("Unavailable project(s): {0}".format(', '.join(h.difference(h_avail))))
    return list(h_avail)


def fetch(f, remote_checksum, keep, overwrite):
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
        if not isfile(f):
            return True
        else:
            if githash(f) == remote_checksum:
                return False
            else:
                logging.warning('Local "{0}" does not match version on GitHub. '
                                'The file is either outdated or was modified.'.format((basename(f))))
                if keep:
                    return False
                else:
                    return query_yes_no('Overwrite?')


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


def main(args):
    """
    Main process that:

     * Checks if output directory exists,
     * Checks if configuration already exists in output directory,
     * Asks confirmation if necessary,
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
    if not isdir(outdir):
        try:
            os.makedirs(outdir)
            logging.warning('{0} created'.format(outdir))
        except OSError:
            outdir = '{0}/ini'.format(os.getcwd())
            if not isdir(outdir):
                os.makedirs(outdir)
                logging.warning('{0} created'.format(outdir))
    # Instantiate Github session
    gh = github_connector(repository=GITHUB_REPO, team=GITHUB_TEAM, username=args.gh_user, password=args.gh_password)
    logging.info('Connected to "{0}" GitHub repository '.format(GITHUB_REPO.lower()))

    ####################################
    # Fetch and deploy esg.project.ini #
    ####################################

    # Get "remote" project targeted from the command-line
    projects = target_projects(gh, args.project)
    for project in tqdm(projects,
                        desc='Fetching "esg.<project>.ini"'.ljust(LEN_MSG),
                        total=len(projects),
                        bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} files',
                        ncols=100,
                        unit='files',
                        file=sys.stdout):
        outfile = join(outdir, 'esg.{0}.ini'.format(project))
        # Get file content
        content = gh_content(gh, path=join(GITHUB_DIRECTORY, 'ini', 'esg.{0}.ini'.format(project)))
        if fetch(outfile, content.sha, args.k, args.o):
            # Backup old file if exists
            backup(outfile, mode=args.b)
            # Write new file
            with open(outfile, 'w+') as f:
                f.write(content.decoded)

    # Check if esgprep is run on an ESGF node
    try:
        import esgcet
    #############################################
    # Fetch and deploy esgcet_models_tables.txt #
    #############################################
        outdir = '/esg/config/esgcet'
        if not exists(outdir):
            logging.warning('"{0}" does not exist. Fetching "esgcet_models_table.txt" aborted.'.format(outdir))
        outfile = join(outdir, 'esgcet_models_table.txt')
        # Get file content
        content = gh_content(gh, path=join(GITHUB_DIRECTORY, 'esgcet_models_table.txt'))
        if fetch(outfile, content.sha, args.k, args.o):
            # Backup old file if exists
            backup(outfile)
            # Write new file
            with open(outfile, 'w+') as f:
                f.write(content.decoded)
        # Just for homogeneous display
        print '{0}: 100% |█████████████████████████████████████████████| 1/1 files'.format(
            'Fetching "esgcet_models_table.txt"'.ljust(LEN_MSG))

    #######################################
    # Fetch and deploy project_handler.py #
    #######################################

        outdir = join(dirname(esgcet.__file__), 'config')
        if not exists(outdir):
            logging.warning('"{0}" does not exist. Fetching handlers aborted.'.format(outdir))
        projects = target_handlers(gh, args.project)
        for project in tqdm(projects,
                            desc='Fetching "<project>_handler.py"'.ljust(LEN_MSG),
                            total=len(projects),
                            bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} files',
                            ncols=100,
                            unit='files',
                            file=sys.stdout):
            outfile = join(outdir, '{0}_handler.py'.format(project))
            # Get file content
            content = gh_content(gh, path=join(GITHUB_DIRECTORY, 'handlers', '{0}_handler.py'.format(project)))
            if fetch(outfile, content.sha, args.k, args.o):
                # Backup old file if exists
                backup(outfile, mode=args.b)
                # Write new file
                with open(outfile, 'w+') as f:
                    f.write(content.decoded)

    except ImportError:
        logging.warning('No module named "esgcet". Not on an ESGF node? Fetching aborted.')
