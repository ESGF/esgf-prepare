#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import os
import re

from esgprep.utils.github import gh_request_content
from esgprep.utils.custom_print import *
from requests.auth import HTTPBasicAuth
import sys

from constants import *
from esgprep.utils.collectors import FilterCollection
from esgprep.utils.context import GitHubBaseContext


class ProcessingContext(GitHubBaseContext):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: The command-line arguments parser
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        super(self.__class__, self).__init__(args)
        self.tables_dir = os.path.realpath(os.path.normpath(args.tables_dir))
        self.no_ref_folder = args.no_ref_folder
        self.url = GITHUB_CONTENT_API
        self.ref_url = GITHUB_REFS_API
        if args.tag:
            self.ref = args.tag
            self.ref_url += '/tags'
        elif args.branch_regex:
            self.regex = args.branch_regex
            self.ref_url += '/heads'
        elif args.tag_regex:
            self.regex = args.tag_regex
            self.ref_url += '/tags'
        else:
            # args.branch has a default value of 'master'
            # if not set with --branch
            self.ref = args.branch
            self.ref_url += '/heads'
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
        self.progress = 0

    def __enter__(self):
        super(self.__class__, self).__enter__()
        # Init the project list to retrieve
        self.targets = self.target_projects(pattern = '(.+?)-cmor-tables', url_format = GITHUB_REPOS_API)
        # Get number of projects
        self.ntargets = len(self.targets)
        return self
