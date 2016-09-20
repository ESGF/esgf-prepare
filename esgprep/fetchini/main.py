#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import ConfigParser
import logging
import os
import re
import sys
from datetime import datetime

from esgprep.utils import parser
from github3 import GitHub
from github3.models import GitHubError
from esgprep.utils.exceptions import *
from constants import *
from exceptions import *


def query_yes_no(question, default='no'):
    """
    Asks a yes/no question via raw_input() and return their answer.

    :param str question: The question string that is presented to the user
    :param str default: The default answer is the string if the user just hits the carriage return.
        If None an answer is required.
    :returns: The answer True or False
    :rtype: *boolean*

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
        choice = raw_input().lower()
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

    """

    try:
        # TODO: uncomment
        return GitHub('glevava', '4{B3,3GJ2>8$hF').repository(team, repository.lower())
#        return GitHub(username, password).repository(team, repository.lower())
    except GitHubError, e:
        raise GitHubConnectionError(e, repository, username, password, team)


def backup(filename, srcdir):
    """
    Backup a local file by copying the file into a child directory of the source directory.
    The filename of the backup file includes a timestamp.

    :param str filename: The filename to backup
    :param str srcdir: The source directory

    """
    bkpdir = '{0}/bkp'.format(srcdir)
    src = '{0}/{1}'.format(srcdir, filename)
    dst = '{0}/{1}.{2}'.format(bkpdir, datetime.now().strftime('%Y%m%d-%H%M%S'), filename)
    if os.path.isfile(src):
        try:
            os.makedirs(bkpdir)
        except OSError:
            pass
        finally:
            # Overwritten silently if destination file already exists
            os.rename(src, dst)


def get_content(gh, path):
    """
    Gets the GitHub content of a file or a directory.

    :param github3.GitHub.repository gh: A :func:`github_connector` instance
    :param str path: The remote file or directory path
    :returns: The remote file or directory content
    :rtype: *github3.GitHub.repository.contents*
    :raises Error: If the GitHub request returns empty content

    """
    content = gh.contents(path)
    if not content:
        raise GitHubNoContent(gh.contents_urlt.expand(path=path))
    return content


def get_property(key, path='esgf.properties'):
# TODO: uncomment
#def get_property(key, path='/esg/config/esgf.properties'):
    """
    Gets value corresponding to key from a key: value pairs file.

    :param str key: The requested key
    :param str path: The file path
    :returns: The value
    :rtype: *str*
    :raises Error: If the key doesn't exist

    """
    values = dict()
    with open(path) as f:
        for line in f:
            k, v = line.partition('=')[::2]
            values[str(k).strip()] = str(v).strip()
    return values[key]


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
    outdir = os.path.normpath(os.path.abspath(args.i))
    # If output directory doesn't exist, create it.
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
        logging.warning('{0} created'.format(outdir))
    # Instantiate Github session
    gh = github_connector(repository=GITHUB_REPO, team=GITHUB_TEAM)
    if args.v:
        logging.info('Connected to "{0}" GitHub repository '.format(GITHUB_REPO.lower()))

    ####################################
    # Fetch and deploy esg.project.ini #
    ####################################

    # If not specified, get all files from GitHub repository
    if isinstance(args.project, list):
        args.project = '|'.join(args.project)
    projects = list()
    files = get_content(gh, path='{0}/{1}'.format(GITHUB_DIRECTORY, 'ini'))
    # Loop over esg.*.ini files
    for filename in files.keys():
        if re.search(r'esg\.(:?{0})\.ini'.format(args.project), filename):
            projects.append(re.search(r'esg\.(.+?)\.ini', filename).group(1))
            outfile = '{0}/{1}'.format(outdir, filename)
            # Fetch file only:
            # If the file doesn't exists or
            # If the file exists and '-k' is set to False and if '-f' is set to True or prompt answer is Yes
            # '-f' can be set to True only if '-k' is set to False.
            # If not ask to user instead
            if (not os.path.isfile(outfile) or
               (os.path.isfile(outfile) and not args.k and
               (args.o or query_yes_no('Overwrite existing "{0}"?'.format(filename))))):
                # Get file content
                content = get_content(gh, path=files[filename].path)
                # Backup old file if exists
                backup(filename, outdir)
                # Write the file
                with open('{0}/{1}'.format(outdir, filename), 'w+') as f:
                    f.write(content.decoded)
                logging.info('{0} --> {1}/{2} '.format(content.html_url, outdir, filename))

    ############################
    # Fetch and deploy esg.ini #
    ############################

    filename = 'esg.ini'
    outfile = '{0}/{1}'.format(outdir, filename)
    # Fetch file only:
    # If the file doesn't exists or
    # If the file exists but '-k' is set to False and whether '-f' is set to True or prompt answer is Yes
    # '-f' can be set to True only if '-k' is set to False.
    # If not ask to user instead
    if (not os.path.isfile(outfile) or
       (os.path.isfile(outfile) and not args.k and
       (args.o or query_yes_no('Overwrite existing "esg.ini"?')))):
        # Get file content
        content = get_content(gh, path=files[filename].path)
        # Configure ESGF properties
        if not args.db_password:
            raise MissingArgument('--db-password')
        content.decoded = re.sub('<DB_PASSWORD>', args.db_password, content.decoded)
        if not args.tds_password:
            raise MissingArgument('--tds-password')
        content.decoded = re.sub('<TDS_PASSWORD>', args.tds_password, content.decoded)
        if not args.data_root_path:
            raise MissingArgument('--data-root-path')
        content.decoded = re.sub('<DATA_ROOT_PATH>', args.data_root_path, content.decoded)
        content.decoded = re.sub('<DB_HOST>', get_property('db.host'), content.decoded)
        content.decoded = re.sub('<DB_PORT>', get_property('db.port'), content.decoded)
        content.decoded = re.sub('<INDEX_NODE_HOSTNAME>', get_property('esgf.index.peer'), content.decoded)
        content.decoded = re.sub('<DATA_NODE_HOSTNAME>', get_property('esgf.host'), content.decoded)
        content.decoded = re.sub('<INSTITUTE>', get_property('esg.root.id'), content.decoded)
        # Backup old file if exists
        backup(filename, outdir)
        # Write esg.ini file
        with open('{0}/{1}'.format(outdir, filename), 'w+') as f:
            f.write(content.decoded)
        logging.info('{0} --> {1}/{2} '.format(content.html_url, outdir, filename))
        # Update thredds dataset roots
        # Get configuration parser
        cfg = ConfigParser.ConfigParser()
        cfg.read('{0}/esg.ini'.format(outdir))
        # Get project options
        thredds_options = parser.get_thredds_roots(cfg)
        # Build project id as last project of the project_options
        for project in projects:
            project_section = 'project:{0}'.format(project)
            project_cfg = parser.config_parse(outdir, project_section)
            project_name = parser.get_default_value(project_cfg, project_section, 'project')
            if project not in [thredds_option[0] for thredds_option in thredds_options]:
                thredds_options.append((project.lower(), '{0}/{1}'.format(args.data_root_path, project_name)))
                new_thredds_options = tuple([parser.build_line(thredds_option) for thredds_option in thredds_options])
                cfg.set('DEFAULT', 'thredds_dataset_roots', '\n' + parser.build_line(new_thredds_options, sep='\n'))
        # Write new esg.ini file
        with open('{0}/esg.ini'.format(outdir), 'wb') as f:
            cfg.write(f)
    # Update esg.ini project options in any case
    # Get configuration parser
    cfg = ConfigParser.ConfigParser()
    cfg.read('{0}/esg.ini'.format(outdir))
    # Get project options
    project_options = parser.get_project_options(cfg)
    # Build project id as last project of the project_options
    project_id = str(1)
    if len(project_options) != 0:
        project_id = str(max([int(project_option[2]) for project_option in project_options]) + 1)
    for project in projects:
        project_section = 'project:{0}'.format(project)
        project_cfg = parser.config_parse(outdir, project_section)
        project_name = parser.get_default_value(project_cfg, project_section, 'project')
        if project not in [project_option[0] for project_option in project_options]:
            project_options.append((project.lower(), project_name, project_id))
            new_project_options = tuple([parser.build_line(project_option) for project_option in project_options])
            cfg.set('DEFAULT', 'project_options', '\n' + parser.build_line(new_project_options, sep='\n'))
    # Write new esg.ini file
    with open('{0}/esg.ini'.format(outdir), 'wb') as f:
        cfg.write(f)
    logging.info('"{0}/esg.ini" updated'.format(outdir))

    #############################################
    # Fetch and deploy esgcet_models_tables.txt #
    #############################################

    files = get_content(gh, path=GITHUB_DIRECTORY)
    filename = 'esgcet_models_tables.txt'
    outfile = '{0}/{1}'.format(outdir, filename)
    # Fetch file only:
    # If the file doesn't exists or
    # If the file exists and '-k' is set to False and if '-f' is set to True or prompt answer is Yes
    # '-f' can be set to True only if '-k' is set to False.
    # If not ask to user instead
    if (not os.path.isfile(outfile) or
       (os.path.isfile(outfile) and not args.k and
       (args.o or query_yes_no('Overwrite existing "{0}"?'.format(filename))))):
        # Get file content
        content = get_content(gh, path=files[filename].path)
        # Backup old file if exists
        backup(filename, outdir)
        # Write the file
        with open('{0}/{1}'.format(outdir, filename), 'w+') as f:
            f.write(content.decoded)
        logging.info('{0} --> {1}/{2} '.format(content.html_url, outdir, filename))

    #######################################
    # Fetch and deploy project_handler.py #
    #######################################

    h_outdir = os.path.normpath(os.path.abspath(HANDLERS_OUTDIR))
    # If not specified, get all files from GitHub repository
    files = get_content(gh, path='{0}/{1}'.format(GITHUB_DIRECTORY, 'handlers'))
    for project in projects:
        project_section = 'project:{0}'.format(project)
        project_cfg = parser.config_parse(outdir, project_section)
        if project_cfg.has_option(project_section, 'handler'):
            filename = '{0}.py'.format(re.search('.*\.(.+?):.*', project_cfg.get(project_section, 'handler')).group(1))
            outfile = '{0}/{1}'.format(outdir, filename)
            # Fetch file only:
            # If the file doesn't exists or
            # If the file exists and '-k' is set to False and if '-f' is set to True or prompt answer is Yes
            # '-f' can be set to True only if '-k' is set to False.
            # If not ask to user instead
            if (not os.path.isfile(outfile) or
               (os.path.isfile(outfile) and not args.k and
               (args.o or query_yes_no('Overwrite existing "{0}"?'.format(filename))))):
                # Get file content
                content = get_content(gh, path=files[filename].path)
                # Backup old file if exists
                backup(filename, h_outdir)
                # Write the file
                with open('{0}/{1}'.format(h_outdir, filename), 'w+') as f:
                    f.write(content.decoded)
                logging.info('{0} --> {1}/{2} '.format(content.html_url, h_outdir, filename))
        else:
            logging.warning('No "handler" option found into "esg.{0}.ini"'.format(project))
