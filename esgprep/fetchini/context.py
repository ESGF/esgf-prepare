#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from constants import *
from esgprep.utils.github import *
from esgprep.utils.custom_print import *
from requests.auth import HTTPBasicAuth


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: The command-line arguments parser
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.projects = args.project
        self.keep = args.k
        self.overwrite = args.o
        self.backup_mode = args.b
        self.gh_user = args.gh_user
        self.gh_password = args.gh_password
        self.config_dir = os.path.realpath(os.path.normpath(args.i))
        self.url = GITHUB_FILE_API
        if args.devel:
            self.url += '?ref=devel'
        self.error = False

    def __enter__(self):
        # Init GitHub authentication
        self.auth = self.authenticate()
        # Init output directory
        self.make_ini_dir()
        # Init the project list to retrieve
        self.targets = self.target_projects()
        # Get number of files
        self.nfiles = len(self.targets)
        if not self.nfiles:
            Print.warning('No files found on remote repository')
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        # Print log path if exists
        Print.log()

    def authenticate(self):
        """
        Builds GitHub HTTP authenticator

        :returns: The HTTP authenticator
        :rtype: *requests.auth.HTTPBasicAuth*

        """
        return HTTPBasicAuth(self.gh_user, self.gh_password) if self.gh_user and self.gh_password else None

    def make_ini_dir(self):
        """
        Build the output directory as follows:
         - If ESGF node and args.i = /esg/config/esgcet -> exists
         - If not ESGF node and args.i = /esg/config/esgcet -> doesn't exist -> use $PWD/ini instead
         - If ESGF node and args.i = other -> if not exists make it
         - If not ESGF node and args.i = other -> if not exists make it

        """
        # If directory does not already exist
        if not os.path.isdir(self.config_dir):
            try:
                os.makedirs(self.config_dir)
                Print.warning('{} created'.format(self.config_dir))
            except OSError:
                # If default directory does not exists
                self.config_dir = os.path.join(os.getcwd(), 'ini')
                if not os.path.isdir(self.config_dir):
                    os.makedirs(self.config_dir)
                    Print.warning('{} created'.format(self.config_dir))

    def target_projects(self):
        """
        Gets the available projects ids from GitHub esg.*.ini files.
        Make the intersection with the desired projects to fetch.

        :returns: The target projects
        :rtype: *list*

        """
        pattern = 'esg\.(.+?)\.ini'
        r = gh_request_content(self.url.format(''), auth=self.auth)
        files = [content['name'] for content in r.json()]
        p_found = set([re.search(pattern, x).group(1) for x in files if re.search(pattern, x)])
        if self.projects:
            p = set(self.projects)
            p_avail = p_found.intersection(p)
            if p.difference(p_avail):
                msg = 'No such project(s): {} -- '.format(', '.join(p.difference(p_avail)))
                msg += 'Available remote projects are: {}'.format(', '.join(list(p_found)))
                Print.warning(msg)
        else:
            p_avail = p_found
        return list(p_avail)
