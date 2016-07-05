#!/usr/bin/env python

import re
import sys
import os
import logging
import ConfigParser
import requests
from esgprep.utils import parser


# GitHub configuration
__GITHUB_API__ = 'https://api.github.com'
__GITHUB_BASE__ = 'https://raw.github.com'
__GITHUB_REPO__ = 'ESGF/config'
__GITHUB_BRANCH__ = 'devel'
__GITHUB_DIRECTORY__ = 'publisher-configs/ini'


def build_http(project):
    """
    Builds the HTTP URL to get esg.<project>.ini file

    :param str project: The lower-cased project name
    :returns: The HTTP URL to request
    :rtype: *str*

    """
    return '/'.join([__GITHUB_BASE__,
                     __GITHUB_REPO__,
                     __GITHUB_BRANCH__,
                     __GITHUB_DIRECTORY__,
                     'esg.{0}.ini'.format(project)])


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
             'no': False, 'n': False, 'NO': False, 'N': False, 'No': False}
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
            # Print again the question
            pass


def get_github_files_list():
    """
    Returns the list of esg.*.ini files from the GitHub repository.

    :return: The filenames
    :rtype: *list*

    """
    files = []
    try:
        # Get last commit SHA on the corresponding branch
        r = requests.get('/'.join([__GITHUB_API__, 'repos', __GITHUB_REPO__, 'commits', __GITHUB_BRANCH__]))
        commit = r.json()['sha']
        # Get GitHub tree SHA
        r = requests.get('/'.join([__GITHUB_API__, 'repos', __GITHUB_REPO__, 'git', 'commits', commit]))
        tree = r.json()['tree']['sha']
        # Get tree elements recursively
        r = requests.get('/'.join([__GITHUB_API__, 'repos', __GITHUB_REPO__, 'git', 'trees', tree + '?recursive=1']))
        # Extract INI filenames from whole repository tree
        for element in r.json()['tree']:
            if element['type'] == 'blob' and re.search(r'/esg\..*\.ini$', element['path']):
                files.append(os.path.basename(element['path']))
        return files
    except:
        logging.exception('Cannot get filenames from GitHub repository')


def fetch(url, outdir, project):
    """
    Downloads an esg.<project>.ini file from GitHub URL to local file system.

    :param str url: The URL to fetch
    :param outdir: The output directory to write
    :param project: The lower-cased project name

    """
    try:
        logging.info('Fetching {0}...'.format(url))
        # Get GitHub URL response
        r = requests.get(url)
        # Write response to file
        with open('{0}/esg.{1}.ini'.format(outdir, project), 'w+') as f:
            f.write(r.text)
        logging.info('Result: SUCCESSFUL')
    except:
        logging.exception('Result: FAILED')


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
    # If not specified project name, get all files from repository
    if not args.project:
        if args.v:
            logging.info('Get filenames from GitHub repository: {0}'.format(__GITHUB_REPO__))
        projects = [re.search(r'esg\.(.+?)\.ini', f).group(1) for f in get_github_files_list()]
    else:
        projects = args.project
    # Loop over wanted projects
    for project in projects:
        # Build the GitHub HTTP to request
        url = build_http(project)
        outfile = '{0}/esg.{1}.ini'.format(outdir, project)
        # Check if file already exists
        if os.path.isfile(outfile):
            logging.warning('"esg.{0}.ini" already exists in {1}'.format(project, outdir))
            # If not force mode = keep existing file
            if not args.k:
                # If force mode = overwrite existing file
                # '-f' can be set to True only if '-k' is set to False.
                # If not ask to user instead
                if args.o or query_yes_no('\nOverwrite existing "esg.{0}.ini"?'.format(project)):
                    fetch(url, outdir, project)
        else:
            fetch(url, outdir, project)
        # Test if esg.ini exists in output directory
        if not os.path.isfile('{0}/esg.ini'.format(outdir)):
            logging.warning('"esg.ini not found in {0}. Cannot append "{1}" to project options'.format(outdir, project))
        else:
            # Get configuration parser
            cfg = ConfigParser.ConfigParser()
            cfg.read('{0}/esg.ini'.format(outdir))
            # Get project options
            project_options = parser.get_project_options(cfg)
            if project not in [project_option[0] for project_option in project_options]:
                # Build project id as last project of the project_options
                project_id = str(1)
                if len(project_options) != 0:
                    project_id = str(max([int(project_option[2]) for project_option in project_options]) + 1)
                # Append new option
                project_options.append((project, project.upper(), project_id))
                new_project_options = tuple([parser.build_line(project_option) for project_option in project_options])
                # Write the updated parser
                cfg.set('DEFAULT', 'project_options', '\n' + parser.build_line(new_project_options, sep='\n'))
                # Write new esg.ini file
                with open('{0}/esg.ini'.format(outdir), 'wb') as f:
                    cfg.write(f)
                logging.info('"{0}" added to "project_options" of {1}/esg.ini'.format(project, outdir))
