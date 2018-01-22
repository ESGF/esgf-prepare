#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this package.

"""

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


class NoNetCDFVariable(Exception):
    """
    Raised when a NetCDF variable is missing.

    """

    def __init__(self, variable, path):
        self.msg = "Variable not found"
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
