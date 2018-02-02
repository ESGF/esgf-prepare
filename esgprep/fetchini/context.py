#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import logging
import os
import re
import sys

from requests.auth import HTTPBasicAuth

from constants import *
from esgprep.utils.misc import as_pbar
from misc import gh_request_content


class ProcessingContext(object):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: The command-line arguments parser
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        self.pbar = args.pbar
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
        # Init progress bar
        if self.pbar:
            self.targets = as_pbar(self.targets, desc='Fetching "esg.<project>.ini"', units='files')
        return self

    def __exit__(self, *exc):
        # Default is sys.exit(0)
        if self.error:
            sys.exit(1)

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
        if not os.path.isdir(self.config_dir):
            try:
                os.makedirs(self.config_dir)
                logging.warning('{} created'.format(self.config_dir))
            except OSError:
                self.config_dir = '{}/ini'.format(os.getcwd())
                if not os.path.isdir(self.config_dir):
                    os.makedirs(self.config_dir)
                    logging.warning('{} created'.format(self.config_dir))

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
        p_avail = set([re.search(pattern, x).group(1) for x in files if re.search(pattern, x)])
        if self.projects:
            p = set(self.projects)
            p_avail = p_avail.intersection(p)
            if p.difference(p_avail):
                logging.warning("Unavailable project(s): {}".format(', '.join(p.difference(p_avail))))
        return list(p_avail)
