#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from constants import *
from esgprep.utils.collectors import FilterCollection
from esgprep.utils.context import GitHubBaseContext
from esgprep.utils.custom_print import *
from esgprep.utils.github import gh_request_content


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
        self.no_subfolder = args.no_subfolder
        self.url = GITHUB_CONTENT_API
        self.ref_url = GITHUB_REFS_API
        if args.tag:
            self.ref = args.tag
            self.ref_url += '/tags'
        else:
            # if not set with --branch default is "master"
            self.ref = args.branch
            self.ref_url += '/heads'
        self.ref = re.compile('^{}$'.format(self.ref))
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

    def __enter__(self):
        super(self.__class__, self).__enter__()
        # Get the project list to retrieve
        r = gh_request_content(GITHUB_REPOS_API, auth=self.auth)
        repos = [repo['name'] for repo in r.json() if re.search(REPO_NAME_PATTERN, repo['name'])]
        # Get the list of project to fetch
        p_found = set([re.search(REPO_NAME_PATTERN, repo).group(1) for repo in repos])
        if self.projects:
            p = set(self.projects)
            p_avail = p_found.intersection(p)
            if p.difference(p_avail):
                msg = 'No such project(s): {} -- '.format(', '.join(p.difference(p_avail)))
                msg += 'Available remote projects are: {}'.format(', '.join(list(p_found)))
                Print.warning(msg)
            self.projects = p_avail
        else:
            self.projects = p_found
        return self
