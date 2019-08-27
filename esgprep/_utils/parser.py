# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.parser.py
   :platform: Unix
   :synopsis: Command-line parser utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import argparse
import os
import re
import sys
from configparser import ConfigParser
from datetime import datetime
from gettext import gettext
from multiprocessing import cpu_count


class CustomArgumentParser(argparse.ArgumentParser):
    """
    Custom argument parser class.

    """

    def error(self, message):
        # Change exist status in case of wrong arguments.
        self.print_usage(sys.stderr)
        self.exit(-1, gettext('{}: error: {}\n'.format(self.prog, message)))


class MultilineFormatter(argparse.RawTextHelpFormatter):
    """
    Custom formatter class.

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


class DirectoryChecker(argparse.Action):
    """
    Action class to check a directory.

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
        Verify a directory exists.

        """
        # Normalize path.
        path = os.path.abspath(os.path.normpath(path))

        # Catch no such directory error.
        if not os.path.isdir(path):
            msg = 'No such directory: {}'.format(path)
            raise argparse.ArgumentTypeError(msg)

        # Return path.
        return path


class ConfigFileLoader(argparse.Action):
    """
    Configuration file action class.

    """

    def __call__(self, parser, namespace, value, option_string=None):
        checked_val = self.load(value)
        setattr(namespace, self.dest, checked_val)

    @staticmethod
    def load(path):
        """
        Loads configuration file parser.

        """
        # Normalize path.
        path = os.path.abspath(os.path.normpath(path))

        # Catch no such file error.
        if not os.path.isdir(path):
            msg = 'No such directory: {}'.format(path)
            raise argparse.ArgumentTypeError(msg)

        # Check existing esg.ini
        if 'esg.ini' not in os.listdir(path):
            msg = '"esg.ini not found in {}'.format(path)
            raise argparse.ArgumentTypeError(msg)

        # Instantiate configuration parser.
        cfg = ConfigParser()

        # Load configuration.
        cfg.read(os.path.join(path, 'esg.ini'))

        # Return configuration parser.
        return cfg


class ChecksumsReader(argparse.Action):
    """
    Action class to read a checksum file similar to any checksum client output.
    Returns a dictionary where (key: value) pairs respectively are the file path and its checksum.

    """

    def __call__(self, parser, namespace, value, option_string=None):
        checked_val = self.read(value)
        setattr(namespace, self.dest, checked_val)

    @staticmethod
    def read(path):
        """
        Reads checksum list.

        """
        # Normalize path.
        path = os.path.abspath(os.path.normpath(path))

        # Catch no such file error.
        if not os.path.isfile(path):
            msg = 'No such file: {}'.format(path)
            raise argparse.ArgumentTypeError(msg)

        # Instantiate checksum dictionary.
        checksums = dict()

        # Read pre-computed checksums.
        with open(path) as checksums_file:
            for checksum, ffp in [entry.split() for entry in checksums_file.read().splitlines()]:
                ffp = os.path.abspath(os.path.normpath(ffp))
                checksums[ffp] = checksum

        # Return checksums.
        return checksums


class DatasetsReader(argparse.Action):
    """
    Action class to read a dataset identifier list from a simple text file.
    Returns a list of identifiers.

    """

    def __call__(self, parser, namespace, value, option_string=None):
        checked_val = self.read(value)
        setattr(namespace, self.dest, checked_val)

    @staticmethod
    def read(path):
        """
        Reads checksum list.

        """
        # Normalize path.
        path = os.path.abspath(os.path.normpath(path))

        # Catch no such file error.
        if not os.path.isfile(path):
            msg = 'No such file: {}'.format(path)
            raise argparse.ArgumentTypeError(msg)

        # Read pre-computed checksums.
        with open(path) as datasets_file:
            # Return datasets.
            return [d.strip() for d in datasets_file.readlines() if d.strip()]


class VersionChecker(argparse.Action):
    """
    Custom action class.

    """

    def __call__(self, parser, namespace, value, option_string=None):
        checked_val = self.version_checker(value)
        setattr(namespace, self.dest, checked_val)

    @staticmethod
    def version_checker(version):
        """
        Validates version number.

        """
        # Match version with appropriate regex.
        if re.compile(r'^[\d]{1,8}$').search(str(version)):

            # Validates date format in case of 8 digits version.
            if len(version) == 8:
                try:
                    datetime.strptime(version, '%Y%m%d')

                # Catch wrong date format.
                except ValueError:
                    msg = 'Invalid version date: {}.'.format(str(version))
                    raise argparse.ArgumentTypeError(msg)

            # Return version.
            return 'v{}'.format(version)

        # Catch wrong version format.
        else:
            msg = 'Invalid version type: {}.\nAvailable format is YYYYMMDD or an integer.'.format(str(version))
            raise argparse.ArgumentTypeError(msg)


def keyval_converter(pair):
    """
    Validates (key = value) argument format.

    """
    # Build pattern.
    pattern = re.compile(r'([^=]+)=([^=]+)(?:,|$)')

    # Catch wrong format error.
    if not pattern.search(pair):
        msg = 'Bad argument syntax: {}'.format(pair)
        raise argparse.ArgumentTypeError(msg)

    # Return pair as dictionary {key: value}.
    return pattern.search(pair).groups()


def regex_validator(string):
    """
    Validates a regular expression syntax.

    """
    # Try compiling regex.
    try:
        return re.compile(string)

    # Catch wrong regex syntax.
    except re.error:
        msg = 'Bad regex syntax: {}'.format(string)
        raise argparse.ArgumentTypeError(msg)


def processes_validator(value):
    """
    Validates the maximum number of processes.

    """
    # Integer conversion.
    pnum = int(value)

    # Catch disallowed processes numbers.
    if pnum < 1 and pnum != -1:
        msg = 'Invalid processes number. Should be a positive integer or "-1".'
        raise argparse.ArgumentTypeError(msg)

    # Caps processes number by cpu_count().
    if pnum > cpu_count():
        pnum = cpu_count()

    # Return None if max processes = -1.
    # None value corresponds to cpu.count() in Pool creation.
    if pnum == -1:
        return None

    # Return maximum processes number.
    else:
        return pnum
