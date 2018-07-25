#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Tests to fetch ESGF configuration files from GitHub repository.

"""

from esgprep.esgfetchini import main
from subprocess import call
import os
import sys
from shutil import rmtree
import unittest
from nose.plugins.attrib import attr
import logging
logging.getLogger("urllib3").setLevel(logging.WARNING)

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
INI_TEST_DIR = os.path.join(TEST_DIR, 'ini')
TEST_AUDITS = os.path.join(TEST_DIR, 'audits')


class TestFetchINI(object):

    def teardown(self):
        if os.path.exists(INI_TEST_DIR):
            rmtree(INI_TEST_DIR)

    # def test_fetch_one_project(self):
    #     func_name = sys._getframe().f_code.co_name.replace('test_', '')
    #     args = '--project cmip5 -i {}'.format(INI_TEST_DIR).split(' ')
    #     main(args)
    #     audit = os.path.join(TEST_AUDITS, func_name)
    #     returncode = call('md5deep -x {} -r {}'.format(audit, INI_TEST_DIR), shell=True)
    #     assert returncode == 0
    #
    # def test_fetch_list_of_projects(self):
    #     func_name = sys._getframe().f_code.co_name.replace('test_', '')
    #     args = '--project cmip5 cordex cmip6 -i tests/ini'.split(' ')
    #     main(args)
    #     audit = os.path.join(TEST_AUDITS, func_name)
    #     returncode = call('md5deep -x {} -r {}'.format(audit, INI_TEST_DIR), shell=True)
    #     assert returncode == 0
    #
    # def test_fetch_all_projects(self):
    #     func_name = sys._getframe().f_code.co_name.replace('test_', '')
    #     args = '-i tests/ini'.split(' ')
    #     main(args)
    #     audit = os.path.join(TEST_AUDITS, func_name)
    #     returncode = call('md5deep -x {} -r {}'.format(audit, INI_TEST_DIR), shell=True)
    #     assert returncode == 0

    def test_fetch_projects(self):
        args = {'fetch_one_project': '-p cmip5',
                'fetch_list_of_projects': '-p cmip5 cordex cmip6',
                'fetch_all_projects': ''}
        for name, arg in args.iteritems():
            fetch_projects.description = name
            yield fetch_projects, name, '-i {} '.format(INI_TEST_DIR) + arg



def fetch_projects(name, arg):
    args = arg.strip().split(' ')
    main(args)
    audit = os.path.join(TEST_AUDITS, name)
    returncode = call('md5deep -x {} -r {}'.format(audit, INI_TEST_DIR), shell=True)
    assert returncode == 0
