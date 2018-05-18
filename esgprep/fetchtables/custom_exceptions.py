#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""

from datetime import datetime


###################################
# Exceptions for GitHub connexion #
###################################


class GitHubException(Exception):
    """
    Basic exception for GitHub errors.

    """
    # API call url
    URI = []

    def __init__(self, msg):
        self.uri = GitHubException.URI
        self.msg = msg
        self.msg += "\n<url: '{}'>".format(self.uri)
        super(GitHubException, self).__init__(self.msg)


class GitHubUnauthorized(GitHubException):
    """
    Raised when no read access on GitHub repo.

    """

    def __init__(self):
        self.msg = "GitHub permission denied"
        super(self.__class__, self).__init__(self.msg)


class GitHubAPIRateLimit(GitHubException):
    """
    Raised when GitHub API rate limit exceeded.

    """

    def __init__(self, reset_time):
        reset_delta = datetime.fromtimestamp(reset_time) - datetime.now()
        hours, remainder = divmod(reset_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.msg = "GitHub API rate limit exceeded ; submit GitHub user/password to release the rate limit."
        self.msg += "<time_to_reset: {}hour(s) {} minute(s) {}second(s)>".format(hours, minutes, seconds)
        super(self.__class__, self).__init__(self.msg)


class GitHubFileNotFound(GitHubException):
    """
    Raised when no file found on GitHub repo.

    """

    def __init__(self):
        self.msg = "GitHub file not found"
        super(self.__class__, self).__init__(self.msg)


class GitHubConnectionError(GitHubException):
    """
    Raised when the GitHub request fails.

    """

    def __init__(self):
        self.msg = "GitHub connection error"
        super(self.__class__, self).__init__(self.msg)


class GitHubReferenceNotFound(GitHubException):
    """
    Raised when invalid GitHub reference requested.

    """

    def __init__(self, ref, refs):
        self.msg = "GitHub reference (tag or branch) not found"
        self.msg += "<ref: {}>".format(ref)
        self.msg += "<available refs: {}".format(refs)
        super(self.__class__, self).__init__(self.msg)
