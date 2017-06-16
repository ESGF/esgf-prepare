#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: ``esgprep`` test suite.

"""

import unittest
from esgprep.checkvocab.main import *
from esgprep.checkvocab.constants import *
from esgprep.checkvocab.exceptions import *
from github3.github import Repository as GitHubRepository


class CheckVocabTest(unittest.TestCase):
    """
    ``esgprep check-vocab`` test cases.

    """

    def setUp(self):
        self.input = {
            1: 'test/test_list1.txt'
        }
        self.excpected_output = {
            1: ['my.dataset.id',
                'my.dataset.id.'
                'my.dataset.id.v1'
                'my.dataset.id.v20140405',
                'my.dataset.id#v20120305']
        }

    def test_yield_datasets_from_file(self):
        """
        Tests dataset ID parsing from an input file.

        """
        args = []
        ctx = ProcessingContext()
        yield_datasets_from_file(self.ctx)

        self.assertIsInstance(repo, GitHubRepository)


def run():
    """
    Run test suite

    """
    testsuite = unittest.TestLoader().discover('.')
    unittest.TextTestRunner().run(testsuite)
