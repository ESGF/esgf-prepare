#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import logging
import sys
from datetime import datetime
from os.path import *

from github3 import GitHub
from github3.models import GitHubError

from constants import *
from esgprep.utils.parser import *
from exceptions import *


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
        raise ValueError('Invalid default answer: {0}'.format(default))
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


def query_thredds_root(project):
    """
    Asks project data root path via raw_input() and return their answer.

    :param str project: The project name
    :return: The data root path
    :rtype: *str*

    """
    while True:
        path = raw_input('Root path for "{0}" data: '.format(project)).strip()
        path = normpath(abspath(path))
        if project.lower() not in path.lower():
            if not query_yes_no('"{0}" does not include the project. Are you sure?'.format(path), default='no'):
                # Ask again
                continue
        if not exists(path):
            if not query_yes_no('"{0}" does not exist. Are you sure?'.format(path), default='no'):
                # Ask again
                continue
        return path


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
    except GitHubError, e:
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
    except GitHubError, e:
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


def get_property(key, path, sep='='):
    """
    Gets value corresponding to key from a key: value pairs file.

    :param str key: The requested key
    :param str path: The file path to parse
    :param str sep: The fields separator
    :returns: The value
    :rtype: *str*
    :raises Error: If the key doesn't exist

    """
    values = dict()
    with open(path) as f:
        for line in f:
            k, v = line.partition(sep)[::2]
            values[str(k).strip()] = str(v).strip()
    return values[key]


def get_project_name(project, path):
    """
    Gets the project name from the configuration file defaults option
    :param str project: The project id
    :param str path: Directory path of configuration files
    :return: The project name
    :rtype: *str*

    """
    section = 'project:{0}'.format(project)
    cfg = CfgParser(path, section)
    try:
        return cfg.get_options_from_pairs(section, 'category_defaults', 'project')
    except NoConfigKey:
        return project


def fetch(f, keep, overwrite):
    """
    Returns True if

    - the file doesn't exists

    OR

    - if the file exists AND 'keep mode' is set disable
                         AND 'overwrite mode' is enable OR the prompt answer is YES.

    :param str f: The file to test
    :param boolean overwrite: True if overwrite existing files
    :param boolean keep: True if keep existing files
    :return: True depending on the conditions
    :rtype: *boolean*

    """
    return True if (not isfile(f) or
                    (isfile(f) and not keep and
                     (overwrite or query_yes_no('Overwrite existing "{0}"?'.format(basename(f)))))) else False


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
    outdir = normpath(abspath(args.i))
    # If output directory doesn't exist, create it.
    if not isdir(outdir):
        os.makedirs(outdir)
        logging.warning('{0} created'.format(outdir))
    # Instantiate Github session
    gh = github_connector(repository=GITHUB_REPO, team=GITHUB_TEAM, username=args.gh_user, password=args.gh_password)
    if args.v:
        logging.info('Connected to "{0}" GitHub repository '.format(GITHUB_REPO.lower()))

    ####################################
    # Fetch and deploy esg.project.ini #
    ####################################

    # Target projects depending on the command-line
    projects = target_projects(gh, args.project)
    for project in projects:
        outfile = join(outdir, 'esg.{0}.ini'.format(project))
        if fetch(outfile, args.k, args.o):
            # Get file content
            content = gh_content(gh, path=join(GITHUB_DIRECTORY, 'ini', 'esg.{0}.ini'.format(project)))
            # Backup old file if exists
            backup(outfile, mode=args.b)
            # Write new file
            with open(outfile, 'w+') as f:
                f.write(content.decoded)
            logging.info('{0} --> {1}'.format(content.html_url, outfile))

    ############################
    # Fetch and deploy esg.ini #
    ############################

    outfile = join(outdir, 'esg.ini')
    if fetch(outfile, args.k, args.o):
        # Get file content
        content = gh_content(gh, path=join(GITHUB_DIRECTORY, 'ini', 'esg.ini'))
        # Configure ESGF properties
        for key in list(set(re.findall(r'<(?!PROJECT|DATA_ROOT_PATH.*)(.+?)>', content.decoded))):
            try:
                value = get_property(key.replace('_', '.').lower(), path=ESGF_PROPERTIES)
            except (KeyError, IOError):
                value = vars(args)[key.lower()]
                if value is None:
                    raise MissingArgument('--{0}'.format(key.replace('_', '-').lower()))
            content.decoded = re.sub('<{0}>'.format(key), value, content.decoded)
        # Backup old file if exists
        backup(outfile)
        # Write new file
        with open(outfile, 'w+') as f:
            f.write(content.decoded)
        logging.info('{0} --> {1}'.format(content.html_url, outfile))

    # Target projects depending on the "project sections" locally found
    cfg = CfgParser(outdir)
    projects = [s.split('project:')[1] for s in cfg.sections() if re.search(r'project:.*', s)]

    # Update thredds dataset roots
    cfg = CfgParser(outdir, section='DEFAULT')
    thredds_options = cfg.get_options_from_table('DEFAULT', 'thredds_dataset_roots')
    for project in projects:
        if project not in [t[0] for t in thredds_options]:
            project_name = get_project_name(project, outdir)
            if args.data_root_path and os.path.exists(args.data_root_path):
                data_root_path = get_property(project, path=args.data_root_path, sep='|')
            else:
                data_root_path = query_thredds_root(project_name)
            thredds_options.append((project.lower(), data_root_path))
    new_thredds_options = tuple([build_line(t, length=align(thredds_options)) for t in thredds_options])
    cfg.set('DEFAULT', 'thredds_dataset_roots', '\n' + build_line(new_thredds_options, sep='\n'))
    # Write new file
    with open(outfile, 'wb') as f:
        cfg.write(f)
    logging.info('"thredds_dataset_roots" in "{0}" successfully updated'.format(outfile))

    # Update esg.ini project options
    cfg = CfgParser(outdir, section='DEFAULT')
    project_options = cfg.get_options_from_table('DEFAULT', 'project_options')
    # Build project id as last project of the project_options
    project_id = 1
    if len(project_options) != 0:
        project_id = max([int(p[2]) for p in project_options]) + 1
    for project in projects:
        if project not in [p[0] for p in project_options]:
            project_name = get_project_name(project, outdir)
            project_options.append((project.lower(), project_name, str(project_id)))
            project_id += 1
    new_project_options = tuple([build_line(p, length=align(project_options)) for p in project_options])
    cfg.set('DEFAULT', 'project_options', '\n' + build_line(new_project_options, sep='\n'))
    # Write new file
    with open(outfile, 'wb') as f:
        cfg.write(f)
    logging.info('"project_options" in "{0}" successfully updated'.format(outfile))

    # Apply pipe alignment to aggregation/file services
    cfg = CfgParser(outdir, section='DEFAULT')
    options = cfg.get_options_from_table('DEFAULT', 'thredds_aggregation_services')
    new_options = tuple([build_line(o, length=align(options)) for o in options])
    cfg.set('DEFAULT', 'thredds_aggregation_services', '\n' + build_line(new_options, sep='\n'))
    options = cfg.get_options_from_table('DEFAULT', 'thredds_file_services')
    new_options = tuple([build_line(o, length=align(options)) for o in options])
    cfg.set('DEFAULT', 'thredds_file_services', '\n' + build_line(new_options, sep='\n'))
    # Write new file
    with open(outfile, 'wb') as f:
        cfg.write(f)
    logging.info('"thredds_aggregation/file_services" in "{0}" successfully formatted'.format(outfile))

    #############################################
    # Fetch and deploy esgcet_models_tables.txt #
    #############################################

    outfile = join(outdir, 'esgcet_models_table.txt')
    if fetch(outfile, args.k, args.o):
        # Get file content
        content = gh_content(gh, path=join(GITHUB_DIRECTORY, 'esgcet_models_table.txt'))
        # Backup old file if exists
        backup(outfile)
        # Write new file
        with open(outfile, 'w+') as f:
            f.write(content.decoded)
        logging.info('{0} --> {1}'.format(content.html_url, outfile))

    #######################################
    # Fetch and deploy project_handler.py #
    #######################################

    try:
        import esgcet
        handler_outdir = join(dirname(esgcet.__file__), 'config')
        if not exists(handler_outdir):
            logging.warning('"{0}" does not exist. Use "{1}" instead.'.format(handler_outdir, outdir))
            handler_outdir = outdir
    except ImportError:
        handler_outdir = outdir
    for project in projects:
        section = 'project:{0}'.format(project)
        cfg = CfgParser(outdir, section=section)
        if cfg.has_option(section, 'handler'):
            filename = '{0}.py'.format(re.search('.*\.(.+?):.*', cfg.get(section, 'handler')).group(1))
            outfile = join(normpath(abspath(handler_outdir)), filename)
            if fetch(outfile, args.k, args.o):
                # Get file content
                content = gh_content(gh, path=join(GITHUB_DIRECTORY, 'handlers', filename))
                # Backup old file if exists
                backup(outfile)
                # Write new file
                with open(outfile, 'w+') as f:
                    f.write(content.decoded)
                logging.info('{0} --> {1}'.format(content.html_url, outfile))
        else:
            logging.info('No "handler" option found into "esg.{0}.ini"'.format(project))
