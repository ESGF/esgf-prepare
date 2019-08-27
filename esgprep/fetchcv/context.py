# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Processing context used in this module.

"""

from multiprocessing import Lock
from multiprocessing.managers import SyncManager

from esgprep._contexts.github import GitHubBaseContext
from esgprep._utils.github import *
from esgprep.fetchcv.constants import *
from ctypes import c_bool
from multiprocessing.sharedctypes import Value

class ProcessingContext(GitHubBaseContext):
    """
    Processing context class to drive main process.

    """

    def __init__(self, args):
        super(ProcessingContext, self).__init__(args)

        # Set pyessv-archive directory.
        self.outdir = self.set('i')

        # Set GitHub API content URL.
        self.url = GITHUB_CONTENT_API

        # Instantiate the list of files to fetch.
        self.files = list()

        # Set authority.
        self.authority = self.set('authority')

        # Set multiprocessing configuration. Processes number is caped by cpu_count().
        self.processes = self.set('max_processes')

        # Sequential processing disables multiprocessing pool usage.
        self.use_pool = (self.processes != 1)

        # Instantiate multiprocessing manager & set progress counter.
        if self.use_pool:
            # Multiprocessing manager starts within a multiprocessing pool only.
            self.manager = SyncManager()
            self.manager.start()

            # Instantiate print buffer.
            Print.BUFFER = self.manager.Value(c_wchar_p, '')

            # Instantiate error boolean.
            self.error = self.manager.Value(c_bool, False)

            # Instantiate progress counter.
            self.progress = self.manager.Value('i', 0)

        else:
            self.error = Value(c_bool, False)
            self.progress = Value('i', 0)

        # Instantiate stdout lock
        self.lock = Lock()

    def __enter__(self):
        super(ProcessingContext, self).__enter__()

        # Get available authorities with corresponding download URL.
        r = gh_request_content(url=self.url, auth=self.auth)
        infos = {f['name']: f for f in r.json() if f['type'] == 'dir'}

        # Filter authorities names depending on submitted identifiers.
        a_found = set(infos.keys())
        if self.authority:
            a = set(self.authority)
            a_avail = a_found.intersection(a)
            if a.difference(a_avail):
                msg = 'No such authority(ies): {} -- '.format(', '.join(a.difference(a_avail)))
                msg += 'Available remote authorities are: {}'.format(', '.join(list(a_found)))
                Print.warning(msg)
            self.authority = a_avail

        # Iterates over authorities.
        for authority in self.authority:

            # Get available authorities with corresponding download URL.
            r = gh_request_content(url=infos[authority]['url'], auth=self.auth)
            a_infos = {f['name']: f for f in r.json()}

            # Filter project names depending on submitted identifiers.
            p_found = set([k for k, v in a_infos.items() if v['type'] == 'dir'])
            if self.project:
                p = set(self.project)
                p_avail = p_found.intersection(p)
                if p.difference(p_avail):
                    msg = 'No such project(s) for authority "{}": {} -- '.format(authority,
                                                                                 ', '.join(p.difference(p_avail)))
                    msg += 'Available remote projects are: {}'.format(', '.join(list(p_found)))
                    Print.warning(msg)
                self.project = p_avail

            # Assert MANIFEST file exists.
            assert 'MANIFEST' in a_infos.keys(), 'Remove MANIFEST file not found.'
            self.files.append(a_infos['MANIFEST'])

            # Iterates over projects.
            for project in self.project:
                r = gh_request_content(url=GITHUB_TREE_API.format(a_infos[project]['sha']), auth=self.auth).json()
                assert not r['truncated'], 'Exceed GitHub API content limit -- ' \
                                           'Response truncated -- ' \
                                           'Please use "git clone" instead.'
                # Add authority and project to file path.
                for i in range(len(r['tree'])):
                    r['tree'][i]['path'] = os.path.join(authority, project, r['tree'][i]['path'])
                self.files += [f for f in r['tree'] if f['type'] == 'blob']

        print([f['path'] for f in self.files])
        # Get number of files to fetch.
        self.nfiles = len(self.files)

        # Exit if no pending files.
        if not self.nfiles:
            Print.warning('No files found on remote repository')
            sys.exit(2)

        # Make outdir.
        self.make_outdir()

        return self

    def make_outdir(self):
        """
        Builds the INI output directory.

        """
        # Normalize output directory from command-line.
        self.outdir = os.path.realpath(os.path.normpath(self.outdir))

        # If directory does not exist.
        if not os.path.isdir(self.outdir):

            # Try to make it.
            try:
                os.makedirs(self.outdir)
                Print.warning('{} created'.format(self.outdir))

            # Error rollbacks to the current working directory (default).
            except OSError as e:
                msg = 'Cannot use "{}" (OSError {}: {}) -- '.format(self.outdir, e.errno, e.strerror)
                msg += 'Use "{}" instead.'.format(os.getcwd())
                Print.warning(msg)
                self.outdir = os.path.join(os.getcwd(), 'pyessv-archive')
                if not os.path.isdir(self.outdir):
                    os.makedirs(self.outdir)
                    Print.warning('{} created'.format(self.outdir))
