#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this package.

"""

from datetime import datetime
from hashlib import algorithms as checksum_types


###############################
# Exceptions for NetCDF files #
###############################


class InvalidNetCDFFile(Exception):
    """
    Raised when invalid or corrupted NetCDF file.

    """

    def __init__(self, path):
        self.msg = "Invalid or corrupted NetCDF file."
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFAttribute(Exception):
    """
    Raised when a NetCDF attribute is missing.

    """

    def __init__(self, attribute, path, variable=None):
        self.msg = "Attribute not found"
        self.msg += "\n<attribute: '{}'>".format(attribute)
        if variable:
            self.msg += "\n<variable: '{}'>".format(variable)
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


############################
# Miscellaneous exceptions #
############################


class KeyNotFound(Exception):
    """
    Raised when a class key is not found.

    """

    def __init__(self, key, keys=None):
        self.msg = "Key not found"
        self.msg += "\n<key: '{}'>".format(key)
        if keys:
            self.msg += "\n<found keys: '{}'>".format(', '.join(keys))
        super(self.__class__, self).__init__(self.msg)


class InvalidChecksumType(Exception):
    """
    Raised when checksum type in unknown.

    """

    def __init__(self, client):
        self.msg = "Checksum type not supported or invalid."
        self.msg += "\n<checksum type: '{}'>".format(client)
        self.msg += "\n<allowed algorithms: '{}'>".format(checksum_types)
        super(self.__class__, self).__init__(self.msg)


class ChecksumFail(Exception):
    """
    Raised when a checksum fails.

    """

    def __init__(self, path, checksum_type=None):
        self.msg = "Checksum failed"
        if checksum_type:
            self.msg += "\n<checksum type: '{}'>".format(checksum_type)
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoFileFound(Exception):
    """
    Raised when frequency no file found.

    """

    def __init__(self, paths):
        self.msg = "No file found"
        for path in paths:
            self.msg += "\n<directory: {}>".format(path)
        super(self.__class__, self).__init__(self.msg)


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
        self.msg = "GitHub API rate limit exceeded ; "
        self.msg += "submit GitHub user/password or "
        self.msg += "export GH_USER and GH_PASSWORD variables to release the rate limit."
        self.msg += "\n<time to reset: {} hour(s) {} minute(s) {} second(s)>".format(hours, minutes, seconds)
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
        self.msg += "\n<ref: {}>".format(ref)
        self.msg += "\n<available refs: {}>".format(', '.join(refs))
        super(self.__class__, self).__init__(self.msg)
