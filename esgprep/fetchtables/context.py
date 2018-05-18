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
from esgprep.utils.collectors import FilterCollection
from esgprep.utils.misc import gh_request_content


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
        self.tables_dir = os.path.realpath(os.path.normpath(args.tables_dir))
        self.no_ref_folder = args.no_ref_folder
        self.url = GITHUB_CONTENT_API
        self.ref_url = GITHUB_REFS_API
        if args.branch:
            self.ref = args.branch
            self.ref_url += '/heads'
        if args.tag:
            self.ref = args.tag
            self.ref_url += '/tags'
        self.file_filter = FilterCollection()
        if args.include_file:
            for regex in args.include_file:
                self.file_filter.add(regex=regex, inclusive=True)
        else:
            # Default include all files
            self.file_filter.add(regex='^.*$', inclusive=True)
        if args.exclude_file:
            for regex in args.exclude_file:
                self.file_filter.add(regex=regex, inclusive=False)
        else:
            # Default exclude hidden files
            self.file_filter.add(regex='^\..*$', inclusive=False)
        self.error = False

    def __enter__(self):
        # Init GitHub authentication
        self.auth = self.authenticate()
        # Init the project list to retrieve
        self.targets = self.target_projects()
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

    def target_projects(self):
        """
        Gets the available projects ids from GitHub esg.*.ini files.
        Make the intersection with the desired projects to fetch.

        :returns: The target projects
        :rtype: *list*

        """
        pattern = '(.+?)-cmor-tables'
        r = gh_request_content(GITHUB_REPOS_API, auth=self.auth)
        repos = [repo['name'] for repo in r.json()]
        p_avail = set([re.search(pattern, x).group(1) for x in repos if re.search(pattern, x)])
        if self.projects:
            p = set(self.projects)
            p_avail = p_avail.intersection(p)
            if p.difference(p_avail):
                logging.warning("Unavailable project(s): {}".format(', '.join(p.difference(p_avail))))
        return list(p_avail)
