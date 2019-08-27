# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from esgprep._collectors import FilterCollection
from esgprep._contexts.github import GitHubBaseContext
from esgprep._utils.github import gh_request_content
from esgprep._utils.print import *
from esgprep.fetchtables.constants import *


class ProcessingContext(GitHubBaseContext):
    """
    Processing context class to drive main process.

    """

    def __init__(self, args):
        super(ProcessingContext, self).__init__(args)

        # Set CMOR tables directory.
        self.tables_dir = os.path.realpath(os.path.normpath(args.tables_dir))

        # Enable/disable subfolder tree structure.
        self.no_subfolder = self.set('no_subfolder')

        # Set GitHub API content URL.
        self.url = GITHUB_CONTENT_API

        # Set GitHub API reference URL.
        self.ref_url = GITHUB_REFS_API

        # Set GitHub reference/branch/tag to fetch from & add API suffix.
        if args.tag:
            self.ref = self.set('tag')
            self.ref_url += '/tags'
        elif args.tag_regex:
            self.ref_regex = self.set('tag_regex')
            self.ref_url += '/tags'
        elif args.branch_regex:
            self.ref_regex = self.set('branch_regex')
            self.ref_url += '/heads'
        else:
            # if not set with --branch default is "master"
            self.ref = self.set('branch')
            self.ref_url += '/heads'

        # Instantiate the list of files to fetch.
        self.files = None

        # Filter undesired files.
        self.file_filter = FilterCollection()
        if args.include_file:
            for regex in args.include_file:
                self.file_filter.add(regex=regex, inclusive=True)
        # Default include all files
        else:
            self.file_filter.add(regex='^.*$', inclusive=True)
        if args.exclude_file:
            for regex in args.exclude_file:
                self.file_filter.add(regex=regex, inclusive=False)
        # Default exclude hidden files
        else:
            self.file_filter.add(regex='^\..*$', inclusive=False)

    def __enter__(self):
        super(ProcessingContext, self).__enter__()

        # Get the list of project having available a CMOR tables repository.
        r = gh_request_content(GITHUB_REPOS_API, auth=self.auth)
        repos = [repo['name'] for repo in r.json() if re.search(REPO_NAME_PATTERN, repo['name'])]

        # Extract project identifiers from CMOR tables repositories.
        p_found = set([re.search(REPO_NAME_PATTERN, repo).group(1) for repo in repos])

        # Filter project names depending on submitted identifiers.
        if self.project:
            p = set(self.project)
            p_avail = p_found.intersection(p)
            if p.difference(p_avail):
                msg = 'No such project(s): {} -- '.format(', '.join(p.difference(p_avail)))
                msg += 'Available remote projects are: {}'.format(', '.join(list(p_found)))
                Print.warning(msg)
            self.project = p_avail

        # Get all project INI files.
        else:
            self.project = p_found

        return self
