#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""


class GitHubConnectError(Exception):
    """
    Raised when the GitHub connection fails.

    """

    def __init__(self, repository, username=None, password=None, team=None):
        self.msg = "Access denied"
        self.msg += "\n<username: '{0}'>".format(username)
        self.msg += "\n<password: '{0}'>".format(password)
        self.msg += "\n<team: '{0}'>".format(team)
        self.msg += "\n<repository: '{0}'>".format(repository.lower())
        super(self.__class__, self).__init__(self.msg)
