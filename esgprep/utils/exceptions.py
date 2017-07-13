#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Custom exceptions used in this package.

"""


#######################################
# Exceptions for configuration parser #
#######################################

class NoConfigFile(Exception):
    """
    Raised when no configuration file found.

    """

    def __init__(self, config_file):
        self.msg = "File not found"
        self.msg += "\n<config file: '{}'>".format(config_file)
        super(self.__class__, self).__init__(self.msg)


class ConfigException(Exception):
    """
    Basic exception for configuration parsing errors.

    """
    # Constants initialized with configuration parser instantiation
    # Configuration files to read
    FILES = []
    # Section to parse
    SECTION = None

    def __init__(self, msg):
        self.config_files = ConfigException.FILES
        self.section = ConfigException.SECTION
        self.msg = msg
        if self.section:
            self.msg += "\n<section: '{}'>".format(self.section)
        for config_file in self.config_files:
            self.msg += "\n<config file: '{}'>".format(config_file)
        super(ConfigException, self).__init__(self.msg)


class EmptyConfigFile(ConfigException):
    """
    Raised when configuration file is empty.

    """

    def __init__(self):
        self.msg = "Empty configuration parser"
        super(self.__class__, self).__init__(self.msg)


class NoConfigSection(ConfigException):
    """
    Raised when no corresponding section found in configuration file.

    """

    def __init__(self):
        self.msg = "Section not found"
        super(self.__class__, self).__init__(self.msg)


class NoConfigOption(ConfigException):
    """
    Raised when no corresponding option found in a section of the configuration file.

    """

    def __init__(self, option):
        self.msg = "Option not found"
        self.msg += "\n<option: '{}'>".format(option)
        super(self.__class__, self).__init__(self.msg)


class NoConfigOptions(ConfigException):
    """
    Raised when no corresponding options type found in a section of the configuration file.

    """

    def __init__(self, option):
        self.msg = "None options not found"
        self.msg += "\n<options: '{}_{{options|map|pattern}}'>".format(option)
        super(self.__class__, self).__init__(self.msg)


class NoConfigValue(ConfigException):
    """
    Raised when no corresponding value found in option of a section from the configuration file.

    """

    def __init__(self, value, option):
        self.msg = "Value not found".format(value)
        self.msg += "\n<value: '{}'>".format(value)
        self.msg += "\n<option: '{}'>".format(option)
        super(self.__class__, self).__init__(self.msg)


class NoConfigKey(ConfigException):
    """
    Raised when no corresponding key found in option of a section from the configuration file.

    """

    def __init__(self, key, option):
        self.msg = "Key not found"
        self.msg += "\n<key: '{}'>".format(key)
        self.msg += "\n<option: '{}'>".format(option)
        super(self.__class__, self).__init__(self.msg)


class NoConfigVariable(ConfigException):
    """
    Raised when a ``%(facet)s`` pattern is missing into ``directory_format`` regex.

    """

    def __init__(self, option, pattern):
        self.msg = "Pattern not found in regular expression (try to add a maptable)"
        self.msg += "\n<pattern: '%({})s'>".format(option)
        self.msg += "\n<format: '{}'>".format(pattern)
        super(self.__class__, self).__init__(self.msg)


class MisdeclaredOption(ConfigException):
    """
    Raised when a option is misdeclared of a section from the configuration file.

    """

    def __init__(self, option, details="Wrong syntax"):
        self.msg = "Misdiclared option. {}".format(details)
        self.msg += "\n<option: '{}'>".format(option)
        super(self.__class__, self).__init__(self.msg)


class InvalidMapHeader(ConfigException):
    """
    Raised when invalid map header.

    """

    def __init__(self, pattern, header):
        self.msg = "Invalid map header"
        self.msg += "\n<header: '{}'>".format(header)
        self.msg += "\n<expected pattern: '{}'>".format(pattern)
        super(self.__class__, self).__init__(self.msg)


class InvalidMapEntry(ConfigException):
    """
    Raised when invalid map header.

    """

    def __init__(self, record, header, option):
        self.msg = "Map entry not match header"
        self.msg += "\n<entry: '{}'>".format(record)
        self.msg += "\n<header: '{}'>".format(header)
        self.msg += "\n<option: '{}'>".format(option)
        super(self.__class__, self).__init__(self.msg)


class DuplicatedMapEntry(ConfigException):
    """
    Raised when invalid map header.

    """

    def __init__(self, record, option):
        self.msg = "Duplicated entry"
        self.msg += "\n<entry: '{}'>".format(record)
        self.msg += "\n<option: '{}'>".format(option)
        super(self.__class__, self).__init__(self.msg)


class MissingPatternKey(ConfigException):
    """
    Raised when facet cannot be deduce to rebuild the submitted pattern.

    """

    def __init__(self, keys, pattern):
        self.msg = 'Missing facet key(s) for pattern resolution (try to use "--not-ignored" argument)'
        self.msg += "\n<found keys: '{}'>".format(keys)
        self.msg += "\n<pattern: '{}'>".format(pattern)
        super(self.__class__, self).__init__(self.msg)


class ExpressionNotMatch(ConfigException):
    """
    Raised when a regular expression resolution failed.

    """

    def __init__(self, string, pattern):
        self.msg = "Pattern resolution failed"
        self.msg += "\n<value: '{}'>".format(string)
        self.msg += "\n<pattern: '{}'>".format(pattern)
        super(self.__class__, self).__init__(self.msg)


###############################
# Exceptions for NetCDF files #
###############################


class InvalidNetCDFFile(Exception):
    """
    Raised when NetCDF valid is corrupted.

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


class ChecksumClientNotFound(Exception):
    """
    Raised when checksum client not found on operating system.

    """

    def __init__(self, client):
        self.msg = "Checksum client not found."
        self.msg += "\n<client: '{}'>".format(client)
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
