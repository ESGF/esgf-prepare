#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Downloads ESGF configuration files from GitHub repository.

"""

import sys
import os
import logging
import requests

# GitHub configuration
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

    :param ArgumentParser args: Parsed command-line arguments (as a :func:`argparse.ArgumentParser` class instance)

    """
    outdir = os.path.normpath(os.path.abspath(args.outdir))
    # If output directory doesn't exist, create it.
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
        logging.warning('{0} created'.format(outdir))
    # Loop over wanted projects
    for project in args.project:
        # Build the GitHub HTTP to request
        url = build_http(project)
        outfile = '{0}/esg.{1}.ini'.format(outdir, project)
        # Check if file already exists
        if os.path.isfile(outfile):
            sys.stdout.write('"esg.{0}.ini" already exists in {1}\n'.format(project, outdir))
            # Ignore if force mode or ask to user instead
            if args.f or query_yes_no("Overwrite existing file?"):
                fetch(url, outdir, project)
        else:
            fetch(url, outdir, project)
