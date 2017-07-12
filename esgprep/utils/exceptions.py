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

    def __init__(self, config_paths):
        self.msg = "Empty configuration parser."
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigFile(Exception):
    """
    Raised when no configuration file found.

    """

    def __init__(self, config_path):
        self.msg = "No such file"
        self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigSection(Exception):
    """
    Raised when no corresponding section found in configuration file.

    """

    def __init__(self, section, config_paths):
        self.msg = "No section: '{}'".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigOption(Exception):
    """
    Raised when no corresponding option found in a section of the configuration file.

    """

    def __init__(self, option, section, config_paths):
        self.msg = "No option: '{}'".format(option)
        self.msg += "\n<section: '{}'>".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigOptions(Exception):
    """
    Raised when no corresponding options type found in a section of the configuration file.

    """

    def __init__(self, facet, section, config_paths):
        self.msg = "No '{}_options' or '{}_map' or '{}_pattern'".format(facet)
        self.msg += "\n<section: '{}'>".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigValue(Exception):
    """
    Raised when no corresponding value found in option of a section from the configuration file.

    """

    def __init__(self, value, option, section, config_paths):
        self.msg = "No value: '{}'".format(value)
        self.msg += "\n<option: '{}'>".format(option)
        self.msg += "\n<section: '{}'>".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigKey(Exception):
    """
    Raised when no corresponding value found in option of a section from the configuration file.

    """

    def __init__(self, key, option, section, config_paths):
        self.msg = "No key: '{}'".format(key)
        self.msg += "\n<option: '{}'>".format(option)
        self.msg += "\n<section: '{}'>".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class NoConfigVariable(Exception):
    """
    Raised when a ``%(facet)s`` pattern is missing into ``directory_format`` regex.

    """

    def __init__(self, option, directory_format, section, config_paths):
        self.msg = "No pattern: '%({})s'. Should be added or declared through a '{}_map' option.".format(option)
        self.msg += "\n<format: '{}'>".format(directory_format)
        self.msg += "\n<section: '{}'>".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class MisdeclaredOption(Exception):
    """
    Raised when a option is misdeclared of a section from the configuration file.

    """

    def __init__(self, option, section, config_paths, reason=None):
        self.msg = "Inappropriately formulated option: '{}'".format(option)
        if reason:
            self.msg += "\n{}".format(reason)
        self.msg += "\n<section: '{}'>".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFAttribute(Exception):
    """
    Raised when a NetCDF attribute is missing.

    """

    def __init__(self, attribute, path, variable=None):
        if variable:
            self.msg = "No attribute: '{}'".format(attribute)
            self.msg += "\n<variable: '{}'>".format(variable)
        else:
            self.msg = "No global attribute: '{}'".format(attribute)
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFVariable(Exception):
    """
    Raised when a NetCDF variable is missing.

    """

    def __init__(self, variable, path):
        self.msg = "No variable: '{}'".format(variable)
        self.msg += "\n<file: '{}'>".format(path)
        super(self.__class__, self).__init__(self.msg)


class InvalidMapHeader(Exception):
    """
    Raised when invalid map header.

    """

    def __init__(self, pattern, header):
        self.msg = "Invalid map header: '{}'".format(header)
        self.msg += "\n<pattern: '{}'>".format(pattern)
        super(self.__class__, self).__init__(self.msg)


class InvalidMapEntry(Exception):
    """
    Raised when invalid map header.

    """

    def __init__(self, record):
        self.msg = "Map entry does not match header: '{}'".format(record)
        super(self.__class__, self).__init__(self.msg)


class DuplicatedMapEntry(Exception):
    """
    Raised when invalid map header.

    """

    def __init__(self, record):
        self.msg = "Map has duplicated entries: '{}'".format(record)
        super(self.__class__, self).__init__(self.msg)


class MissingPatternKey(Exception):
    """
    Raised when facet cannot be deduce to rebuild the submitted pattern.

    """

    def __init__(self, keys, pattern, section, config_paths):
        self.msg = 'A facet key is missing to deduce the pattern. Try to use "--not-ignored" argument.'
        self.msg += "\n<available keys: '{}'>".format(keys)
        self.msg += "\n<pattern: '{}'>".format(pattern)
        self.msg += "\n<section: '{}'>".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class DirectoryNotMatch(Exception):
    """
    Raised when a directory does not match the regex format.

    """

    def __init__(self, path, directory_format, section, config_paths):
        self.msg = "Matching failed to deduce DRS attributes."
        self.msg += "\n<path: '{}'>".format(path)
        self.msg += "\n<format: '{}'>".format(directory_format)
        self.msg += "\n<section: '{}'>".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class DatasetNotMatch(Exception):
    """
    Raised when a dataset does not match the regex format.

    """

    def __init__(self, dset, dataset_format, section, config_paths):
        self.msg = "Matching failed to deduce DRS attributes."
        self.msg += "\n<dataset: '{}'>".format(dset)
        self.msg += "\n<format: '{}'>".format(dataset_format)
        self.msg += "\n<section: '{}'>".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class FilenameNotMatch(Exception):
    """
    Raised when a filename does not match the regex format.

    """

    def __init__(self, filename, filename_format, section, config_paths):
        self.msg = "Matching failed to deduce DRS attributes."
        self.msg += "\n<filename: '{}'>".format(filename)
        self.msg += "\n<format: '{}'>".format(filename_format)
        self.msg += "\n<section: '{}'>".format(section)
        for config_path in config_paths:
            self.msg += "\n<config file: '{}'>".format(config_path)
        super(self.__class__, self).__init__(self.msg)


class KeyNotFound(Exception):
    """
    Raised when a class key is not found.
    Print list of available keys if submitted.

    """

    def __init__(self, key, keys=None):
        self.msg = "No key: '{}'".format(key)
        if keys:
            self.msg += "\n<Available keys: '{}'>".format(', '.join(keys))
        super(self.__class__, self).__init__(self.msg)


class ChecksumClientNotFound(Exception):
    """
    Raised when a class key is not found.
    Print list of available keys if submitted.

    """

    def __init__(self, client):
        self.msg = "Checksum client not found."
        self.msg += "\n<client: '{}'>".format(client)
        super(self.__class__, self).__init__(self.msg)
