#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Class and methods used to parse command-line arguments.

"""

import argparse
import os
import re
import sys
from argparse import RawTextHelpFormatter, ArgumentTypeError, Action, ArgumentParser
from datetime import datetime
from gettext import gettext


class MultilineFormatter(RawTextHelpFormatter):
    """
    Custom formatter class for argument parser to use with the Python
    `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

    """

    def __init__(self, prog, default_columns=120):
        # Overload the HelpFormatter class.

        # stty fails if stdin is not a terminal.
        # But also check stdout, so that when writing to a file 
        # behaviour is independent of terminal device.
        if sys.stdin.isatty() and sys.stdout.isatty():
            try:
                _, columns = os.popen('stty size', 'r').read().split()
            except ValueError:
                columns = default_columns
        else:
            columns = default_columns
        super(MultilineFormatter, self).__init__(prog, max_help_position=100, width=int(columns))


class DirectoryChecker(Action):
    """
    Custom action class for argument parser to use with the Python
    `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

    """

    def __call__(self, parser, namespace, values, option_string=None):
        if isinstance(values, list):
            checked_vals = [self.directory_checker(x) for x in values]
        else:
            checked_vals = self.directory_checker(values)
        setattr(namespace, self.dest, checked_vals)

    @staticmethod
    def directory_checker(path):
        """
        Checks if the supplied directory exists. The path is normalized without trailing slash.

        :param str path: The path list to check
        :returns: The same path list
        :rtype: *str*
        :raises Error: If one of the directory does not exist

        """
        path = os.path.abspath(os.path.normpath(path))
        if not os.path.isdir(path):
            msg = 'No such directory: {}'.format(path)
            raise ArgumentTypeError(msg)
        return path


class VersionChecker(Action):
    """
    Custom action class for argument parser to use with the Python
    `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

    """

    def __call__(self, parser, namespace, value, option_string=None):
        checked_val = self.version_checker(value)
        setattr(namespace, self.dest, checked_val)

    @staticmethod
    def version_checker(version):
        """
        Checks the version format from command-line.

        :type version: The version string from command-line
        :returns: The version if allowed
        :rtype: *str*
        :raises Error: If invalid version format

        """
        if re.compile(r'^[\d]{1,8}$').search(str(version)):
            if len(version) == 8:
                try:
                    datetime.strptime(version, '%Y%m%d')
                except ValueError:
                    msg = 'Invalid version date: {}.'.format(str(version))
                    raise ArgumentTypeError(msg)
            return version
        else:
            msg = 'Invalid version type: {}.\nAvailable format is YYYYMMDD or an integer.'.format(str(version))
            raise ArgumentTypeError(msg)


def keyval_converter(pair):
    """
    Checks the key value syntax.

    :param str pair: The key/value pair to check
    :returns: The key/value pair
    :rtype: *list*
    :raises Error: If invalid pair syntax

    """
    pattern = re.compile(r'([^=]+)=([^=]+)(?:,|$)')
    if not pattern.search(pair):
        msg = 'Bad argument syntax: {}'.format(pair)
        raise ArgumentTypeError(msg)
    return pattern.search(pair).groups()


def regex_validator(string):
    """
    Validates a Python regular expression syntax.

    :param str string: The string to check
    :returns: The Python regex
    :rtype: *re.compile*
    :raises Error: If invalid regular expression

    """
    try:
        return re.compile(string)
    except re.error:
        msg = 'Bad regex syntax: {}'.format(string)
        raise ArgumentTypeError(msg)


def processes_validator(value):
    """
    Validates the max processes number.

    :param str value: The max processes number submitted
    :return:
    """
    pnum = int(value)
    if pnum < 1 and pnum != -1:
        msg = 'Invalid processes number. Should be a positive integer or "-1".'
        raise ArgumentTypeError(msg)
    if pnum == -1:
        # Max processes = None corresponds to cpu.count() in Pool creation
        return None
    else:
        return pnum


class CustomArgumentParser(ArgumentParser):
    def error(self, message):
        """
        Overwrite the original method to change exist status.

        """
        self.print_usage(sys.stderr)
        self.exit(-1, gettext('%s: error: %s\n') % (self.prog, message))

    def set_default_subparser(self, name, args=None):
        """
        Set default sub-parser. Call after setup, just before parse_args().

        """
        subparser_found = False
        for arg in sys.argv[1:]:
            # Breaks if global option without sub-parser
            if arg in ['-h', '--help', '-v', '--version']:
                break
        else:
            for x in self._subparsers._actions:
                if not isinstance(x, argparse._SubParsersAction):
                    continue
                for sp_name in x._name_parser_map.keys():
                    if sp_name in sys.argv[1:]:
                        subparser_found = True
            if not subparser_found:
                # If no subparser found insert the default one in first position
                # This implies no global options without a sub_parsers specified
                if args is None:
                    sys.argv.insert(1, name)
                else:
                    args.insert(0, name)
