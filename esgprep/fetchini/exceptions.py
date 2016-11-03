#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""


class GitHubConnectionError(Exception):
    """
    Raised when the GitHub connection fails.

    """

    def __init__(self, error_msg, repository, username=None, password=None, team=None):
        print type(error_msg)
        if "API rate limit exceeded" in error_msg:
            error_msg = "API rate limit exceeded. Please try again in 60 minutes or submit GitHub user/password."
        self.msg = "GitHub access denied: {0}".format(error_msg)
        self.msg += "\n<username: '{0}'>".format(username)
        self.msg += "\n<password: '{0}'>".format(password)
        self.msg += "\n<team: '{0}'>".format(team)
        self.msg += "\n<repository: '{0}'>".format(repository.lower())
        super(self.__class__, self).__init__(self.msg)


class GitHubNoContent(Exception):
    """
    Raised when the GitHub request returns empty content.

    """

    def __init__(self, uri):
        self.msg = "No content from '{0}'".format(uri)
        super(self.__class__, self).__init__(self.msg)


class MissingArgument(Exception):
    """
    Raised when a command-line argument is missing.

    """

    def __init__(self, arg):
        self.msg = "'{0}' argument is missing".format(arg)
        super(self.__class__, self).__init__(self.msg)


class WrongArgument(Exception):
    """
    Raised when a command-line argument is missing.

    """

    def __init__(self, arg, reason=None):
        self.msg = "Inappropriate argument: '{0}'".format(arg)
        if reason:
            self.msg += "\n{0}".format(reason)
        super(self.__class__, self).__init__(self.msg)
