# -*- coding: utf-8 -*-

"""
.. module:: esgprep._contexts.github.py
   :platform: Unix
   :synopsis: GitHub processing context.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import getpass

from requests.auth import HTTPBasicAuth

from esgprep._contexts import BaseContext
from esgprep._utils.print import *


class GitHubBaseContext(BaseContext):
    """
    Base class for GitHub context manager.

    """

    def __init__(self, args):
        super(GitHubBaseContext, self).__init__(args)

        # Set fetching behavior.
        self.keep = self.set('k')
        self.overwrite = self.set('o')
        self.backup_mode = self.set('b')

        # Set GitHub credentials.
        self.gh_user = self.set('gh_user')
        self.gh_password = self.set('gh_password')
        self.auth = None

        # Instantiate error boolean.
        self.error = False

    def __enter__(self):
        super(GitHubBaseContext, self).__enter__()

        # Interactive prompt if username is set but not the password.
        if self.gh_user and not self.gh_password and sys.stdout.isatty():
            msg = COLOR().bold('Github password for user {}: '.format(self.gh_user))
            self.gh_password = getpass.getpass(msg)

        # GitHub authentication.
        self.auth = self.authenticate()

        return self

    def authenticate(self):
        """
        Builds GitHub HTTP authenticator

        """
        return HTTPBasicAuth(self.gh_user, self.gh_password) if self.gh_user and self.gh_password else None
