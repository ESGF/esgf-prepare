#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this package.

"""


class EmptyConfigFile(Exception):
    """
    Raised when configuration file is empty.

    """

    def __init__(self, paths):
        self.msg = "Empty configuration parser."
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigFile(Exception):
    """
    Raised when no configuration file found.

    """

    def __init__(self, path):
        self.msg = "No or not a file"
        self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigSection(Exception):
    """
    Raised when no corresponding section found in configuration file.

    """

    def __init__(self, section, paths):
        self.msg = "No section: '{0}'".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigOption(Exception):
    """
    Raised when no corresponding option found in a section of the configuration file.

    """

    def __init__(self, option, section, paths):
        self.msg = "No option: '{0}'".format(option)
        self.msg += "\n<section: '{0}'>".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigOptions(Exception):
    """
    Raised when no corresponding options type found in a section of the configuration file.

    """

    def __init__(self, facet, section, paths):
        self.msg = "No '{0}_options' or '{0}_map' or '{0}_pattern'".format(facet)
        self.msg += "\n<section: '{0}'>".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigValue(Exception):
    """
    Raised when no corresponding value found in option of a section from the configuration file.

    """

    def __init__(self, value, option, section, paths):
        self.msg = "No value: '{0}'".format(value)
        self.msg += "\n<option: '{0}'>".format(option)
        self.msg += "\n<section: '{0}'>".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigKey(Exception):
    """
    Raised when no corresponding value found in option of a section from the configuration file.

    """

    def __init__(self, key, option, section, paths):
        self.msg = "No key: '{0}'".format(key)
        self.msg += "\n<option: '{0}'>".format(option)
        self.msg += "\n<section: '{0}'>".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigVariable(Exception):
    """
    Raised when a ``%(facet)s`` pattern is missing into ``directory_format`` regex.

    """

    def __init__(self, option, directory_format, section, paths):
        self.msg = "No pattern: '%({0})s'. Should be added or declared through an '{0}_map' option.".format(option)
        self.msg += "\n<format: '{0}'>".format(directory_format)
        self.msg += "\n<section: '{0}'>".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class MisdeclaredOption(Exception):
    """
    Raised when a option is misdeclared of a section from the configuration file.

    """

    def __init__(self, option, section, paths, reason=None):
        self.msg = "Inappropriately formulated option: '{0}'".format(option)
        if reason:
            self.msg += "\n{0}".format(reason)
        self.msg += "\n<section: '{0}'>".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFAttribute(Exception):
    """
    Raised when a NetCDF attribute is missing.

    """

    def __init__(self, attribute, path, variable=None):
        if variable:
            self.msg = "No attribute: '{0}'".format(attribute)
            self.msg += "\n<variable: '{0}'>".format(variable)
        else:
            self.msg = "No global attribute: '{0}'".format(attribute)
        self.msg += "\n<file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFVariable(Exception):
    """
    Raised when a NetCDF variable is missing.

    """

    def __init__(self, variable, path):
        self.msg = "No variable: '{0}'".format(variable)
        self.msg += "\n<file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class InvalidMapHeader(Exception):
    """
    Raised when invalid map header.

    """

    def __init__(self, pattern, header):
        self.msg = "Invalid map header: '{0}'".format(header)
        self.msg += "\n<pattern: '{0}'>".format(pattern)
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


class DirectoryNotMatch(Exception):
    """
    Raised when a directory does not math the regex format.

    """

    def __init__(self, path, directory_format, section, paths):
        self.msg = "Matching failed to deduce DRS attributes."
        self.msg += "\n<path: '{0}'>".format(path)
        self.msg += "\n<format: '{0}'>".format(directory_format)
        self.msg += "\n<section: '{0}'>".format(section)
        for path in paths:
            self.msg += "\n<config file: '{0}'>".format(path)
        super(self.__class__, self).__init__(self.msg)
