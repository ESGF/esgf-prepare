#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

import logging
import os
import sys

from tqdm import tqdm

from constants import *
from esgprep.utils.ctx_base import BaseContext


class ProcessingContext(BaseContext):
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
        self.targets = self.target_projects(
            pattern = 'esg\.(.+?)\.ini',
            url_format = self.url.format('')
            )
        # Init progress bar
        nfiles = len(self.targets)
        if self.pbar and nfiles:
            self.targets = tqdm(self.targets,
                                desc='Fetching project(s) config',
                                total=nfiles,
                                bar_format='{desc}: {percentage:3.0f}% | {n_fmt}/{total_fmt} files',
                                ncols=100,
                                file=sys.stdout)
        elif not nfiles:
            logging.info('No files found on remote repository')
        return self

    def __exit__(self, *exc):
        # Default is sys.exit(0)
        if self.error:
            sys.exit(1)

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
                logging.warning('{} created'.format(self.config_dir))
            except OSError:
                # If default directory does not exists
                self.config_dir = os.path.join(os.getcwd(), 'ini')
                if not os.path.isdir(self.config_dir):
                    os.makedirs(self.config_dir)
                    logging.warning('{} created'.format(self.config_dir))
