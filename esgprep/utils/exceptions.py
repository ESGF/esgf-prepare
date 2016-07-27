#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this module.

"""


class EmptyConfigFile(Exception):
    """
    Raised when configuration file is empty.

    """

    def __init__(self, paths):
        self.msg = "Empty configuration parser."
        for path in paths:
            self.msg += "\n<file: {0}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigFile(Exception):
    """
    Raised when no configuration file found.

    """

    def __init__(self, paths):
        self.msg = "No or not a file"
        for path in paths:
            self.msg += "\n<file: {0}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigSection(Exception):
    """
    Raised when no corresponding section found in configuration file.

    """

    def __init__(self, section, paths):
        self.msg = "No section: '{0}'".format(section)
        for path in paths:
            self.msg += "\n<file: {0}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigOption(Exception):
    """
    Raised when no corresponding option found in section of the configuration file.

    """

    def __init__(self, option, section, paths):
        self.msg = "No option: '{0}'".format(option)
        self.msg += "\n<section: {0}".format(section)
        for path in paths:
            self.msg += "\n<file: {0}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigOptions(Exception):
    """
    Raised when no corresponding options type found in section of the configuration file.

    """

    def __init__(self, option, section, paths):
        self.msg = "No '{0}_options' or '{0}_map' or '{0}_pattern'".format(option)
        self.msg += "\n<section: {0}".format(section)
        for path in paths:
            self.msg += "\n<file: {0}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigValue(Exception):
    """
    Raised when no corresponding value found in option of the section from the configuration file.

    """

    def __init__(self, value, option, section, paths):
        self.msg = "No value: {0}'".format(value)
        self.msg += "\n<option: {0}".format(option)
        self.msg += "\n<section: {0}".format(section)
        for path in paths:
            self.msg += "\n<file: {0}>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFAttribute(Exception):
    """
    Raised when a NetCDF global attribute is missing.

    """

    def __init__(self, attribute, path):
        self.msg = "No attribute: '{0}'\n" \
                   "<file: {1}>".format(attribute, path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFVariable(Exception):
    """
    Raised when a NetCDF variable is missing.

    """

    def __init__(self, variable, path):
        self.msg = "No variable: '{0}'\n" \
                   "<file: {1}>".format(variable, path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFVariableAttribute(Exception):
    """
    Raised when a NetCDF variable attribute is missing.

    """

    def __init__(self, attribute, variable, path):
        self.msg = "No attribute: '{0}'\n" \
                   "<variable: {1}>\n" \
                   "<file: {2}>".format(attribute, variable, path)
        super(self.__class__, self).__init__(self.msg)


class InvalidMapHeader(Exception):
    """
    Raised when invalid map header.

    """

    def __init__(self, pattern, header):
        self.msg = "Invalid map header: '{0}'\n" \
                   "<pattern: {1}>".format(header, pattern)
        super(self.__class__, self).__init__(self.msg)


class InvalidMapEntry(Exception):
    """
    Raised when invalid map header.

    """

    def __init__(self, record):
        self.msg = "Map entry does not match header: '{0}'".format(record)
        super(self.__class__, self).__init__(self.msg)


class DuplicatedMapEntry(Exception):
    """
    Raised when invalid map header.

    """

    def __init__(self, record):
        self.msg = "Map has duplicated entries: '{0}'".format(record)
        super(self.__class__, self).__init__(self.msg)
