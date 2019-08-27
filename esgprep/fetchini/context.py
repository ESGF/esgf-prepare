# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from esgprep.constants import GITHUB_API_PARAMETER
from esgprep._contexts.github import GitHubBaseContext
from esgprep._utils.github import *
from esgprep.fetchini.constants import *


class ProcessingContext(GitHubBaseContext):
    """
    Processing context class to drive main process.

    """

    def __init__(self, args):
        super(ProcessingContext, self).__init__(args)

        # Set INI file directory.
        self.config_dir = os.path.realpath(os.path.normpath(args.i))

        # Set GitHub reference/branch to fetch from.
        self.ref = 'devel' if args.devel else 'master'

        # Set GitHub API content URL.
        self.url = GITHUB_CONTENT_API
        self.url += GITHUB_API_PARAMETER.format('ref', self.ref)

        # Instantiate the list of files to fetch.
        self.files = None

    def __enter__(self):
        super(ProcessingContext, self).__enter__()

        Print.debug('Fetch from "{}" GitHub reference'.format(self.ref))

        # Get available INI files with corresponding download URL.
        r = gh_request_content(url=self.url, auth=self.auth)
        infos = {f['name']: f for f in r.json() if re.search(INI_PATTERN, f['name'])}

        # Extract project identifiers from INI filenames.
        p_found = set([re.search(INI_PATTERN, x).group(1) for x in infos.keys()])

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

        # Remove undesired files from the pending list.
        self.files = {k: v for k, v in infos.items() if k in ['esg.{}.ini'.format(p) for p in self.project]}

        # Get number of files to fetch.
        self.nfiles = len(self.files)

        # Exit if no pending files.
        if not self.nfiles:
            Print.warning('No files found on remote repository')
            sys.exit(2)

        return self
