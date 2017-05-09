#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: ``esgprep`` test suite.

"""

import unittest
from esgprep.fetchini.main import *
from esgprep.fetchini.constants import *
from esgprep.fetchini.exceptions import *
from github3.github import Repository as GitHubRepository


class FetchiniTest(unittest.TestCase):
    """
    ``esgprep fetch-ini`` test cases.
    
    """

    def setUp(self):
        self.repo = None

    def test_get_github_repository(self):
        """
        Tests GitHub connector to remote repository.
        
        """
        repo = github_connector(GITHUB_REPO, team=GITHUB_TEAM)
        self.assertIsInstance(repo, GitHubRepository)


def run():
    testsuite = unittest.TestLoader().discover('.')
    unittest.TextTestRunner().run(testsuite)
