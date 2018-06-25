#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from constants import *
from esgprep.utils.custom_print import *
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
        self.config_dir = os.path.realpath(os.path.normpath(args.i))
        self.url = GITHUB_FILE_API
        if args.devel:
            self.url += '?ref=devel'
        self.error = False

    def __enter__(self):
        super(self.__class__, self).__enter__()
        # Init the project list to retrieve
        self.targets = self.target_projects(pattern='esg\.(.+?)\.ini', url_format=self.url.format(''))
        # Get number of files
        self.nfiles = len(self.targets)
        if not self.nfiles:
            Print.warning('No files found on remote repository')
            sys.exit(3)
        return self
