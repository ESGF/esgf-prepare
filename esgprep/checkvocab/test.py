#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: ``esgprep`` test suite.

"""

import unittest


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
                'my.dataset.id.',
                'my.dataset.id.v1',
                'my.dataset.id.v20140405',
                'my.dataset.id#v20120305']
        }

    def test_remove(self):
        pass

    def test_yield_datasets_from_file(self):
        """
        Tests dataset ID parsing from an input file.

        """
        # input = os.path.join(os.path.dirname(esgprep.checkvocab.__file__), self.input[1])
        # dsets = yield_datasets_from_file(input)
        # self.assertEqual(list(dsets).sort(), list(self.excpected_output[1]).sort())
        pass


def run():
    """
    Run test suite

    """
    testsuite = unittest.TestLoader().discover('.')
    unittest.TextTestRunner().run(testsuite)
