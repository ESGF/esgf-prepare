#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""


class GitHubUnauthorized(Exception):
    """
    Raised when no read access on GitHub repo.

    """

    def __init__(self, uri):
        self.msg = "Unauthorized to read this GitHub repository."
        self.msg += "\n<url: '{}'>".format(uri)
        super(self.__class__, self).__init__(self.msg)


class GitHubAPIRateLimit(Exception):
    """
    Raised when GitHub API rate limit exceeded.

    """

    def __init__(self, uri):
        self.msg = "GitHub access denied: API rate limit exceeded. " \
                   "Please try again in 60 minutes or submit GitHub user/password."
        self.msg += "\n<url: '{}'>".format(uri)
        super(self.__class__, self).__init__(self.msg)


class GitHubFileNotFound(Exception):
    """
    Raised when no file found on GitHub repo.

    """

    def __init__(self, uri):
        self.msg = "File not found on GitHub."
        self.msg += "\n<url: '{}'>".format(uri)
        super(self.__class__, self).__init__(self.msg)


class GitHubConnectionError(Exception):
    """
    Raised when the GitHub request fails.

    """

    def __init__(self, uri):
        self.msg = "GitHub connection error."
        self.msg += "\n<url: '{}'>".format(uri)
        super(self.__class__, self).__init__(self.msg)
