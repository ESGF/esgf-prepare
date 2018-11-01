#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from constants import *
from esgprep.utils.constants import GITHUB_API_PARAMETER
from esgprep.utils.context import GitHubBaseContext
from esgprep.utils.github import *


class ProcessingContext(GitHubBaseContext):
    """
    Encapsulates the processing context/information for main process.

    :param ArgumentParser args: The command-line arguments parser
    :returns: The processing context
    :rtype: *ProcessingContext*

    """

    def __init__(self, args):
        super(ProcessingContext, self).__init__(args)
        self.config_dir = os.path.realpath(os.path.normpath(args.i))
        self.ref = 'devel' if args.devel else 'master'
        self.url = GITHUB_CONTENT_API
        self.url += GITHUB_API_PARAMETER.format('ref', self.ref)
        self.files = None

    def __enter__(self):
        super(ProcessingContext, self).__enter__()
        Print.debug('Fetch from "{}" GitHub reference'.format(self.ref))
        # Get files infos from repository content
        r = gh_request_content(url=self.url, auth=self.auth)
        infos = {f['name']: f for f in r.json() if re.search(INI_PATTERN, f['name'])}
        # Get the list of project to fetch
        p_found = set([re.search(INI_PATTERN, x).group(1) for x in infos.keys()])
        # Control specified project names
        if self.project:
            p = set(self.project)
            p_avail = p_found.intersection(p)
            if p.difference(p_avail):
                msg = 'No such project(s): {} -- '.format(', '.join(p.difference(p_avail)))
                msg += 'Available remote projects are: {}'.format(', '.join(list(p_found)))
                Print.warning(msg)
            self.project = p_avail
        else:
            # Get all projects
            self.project = p_found
        # Remove undesired files
        self.files = {k: v for k, v in infos.items() if k in ['esg.{}.ini'.format(p) for p in self.project]}
        # Get number of files to fetch
        self.nfiles = len(self.files)
        if not self.nfiles:
            Print.warning('No files found on remote repository')
            sys.exit(2)
        return self
