#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to use with this package.

"""

# Module imports
import logging
import os
import re
import textwrap
from argparse import HelpFormatter, ArgumentTypeError, Action
from datetime import datetime

from tqdm import tqdm


class MultilineFormatter(HelpFormatter):
    """
    Custom formatter class for argument parser to use with the Python
    `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

    """

    def __init__(self, prog):
        # Overload the HelpFormatter class.
        super(MultilineFormatter, self).__init__(prog, max_help_position=60, width=100)

    def _fill_text(self, text, width, indent):
        # Rewrites the _fill_text method to support multiline description.
        text = self._whitespace_matcher.sub(' ', text).strip()
        multiline_text = ''
        paragraphs = text.split('|n|n ')
        for paragraph in paragraphs:
            lines = paragraph.split('|n ')
            for line in lines:
                formatted_line = textwrap.fill(line, width,
                                               initial_indent=indent,
                                               subsequent_indent=indent) + '\n'
                multiline_text += formatted_line
            multiline_text += '\n'
        return multiline_text

    def _split_lines(self, text, width):
        # Rewrites the _split_lines method to support multiline helps.
        text = self._whitespace_matcher.sub(' ', text).strip()
        lines = text.split('|n ')
        multiline_text = []
        for line in lines:
            multiline_text.append(textwrap.fill(line, width))
        multiline_text[-1] += '\n'
        return multiline_text


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
            print path
            msg = 'No such directory: {0}'.format(path)
            print msg
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
                    msg = 'Invalid version date: {0}.'.format(str(version))
                    raise ArgumentTypeError(msg)
            return version
        else:
            msg = 'Invalid version type: {0}.\nAvailable format is YYYYMMDD or an integer.'.format(str(version))
            raise ArgumentTypeError(msg)


class LogFilter(object):
    """
    Log filter with upper log level to use with the Python
    `logging <https://docs.python.org/2/library/logging.html>`_ module.

    """

    def __init__(self, level):
        self.level = level

    def filter(self, log_record):
        """
        Set the upper log level.

        """
        return log_record.levelno <= self.level


def keyval_converter(pair):
    """
    Checks the key value syntax.

    :param str pair: The key/value pair to check
    :returns: The pairs if allowed
    :rtype: *list*
    :raises Error: If invalid pair syntax

    """
    pattern = re.compile(r'([^=]+)=([^=]+)(?:,|$)')
    if not pattern.search(pair):
        msg = 'Bad argument syntax: {0}'.format(pair)
        raise ArgumentTypeError(msg)
    return pattern.search(pair).groups()


def init_logging(log, verbose=False, level='INFO'):
    """
    Initiates the logging configuration (output, date/message formatting).
    If a directory is submitted the logfile name is unique and formatted as follows:
    ``name-YYYYMMDD-HHMMSS-JOBID.log``If ``None`` the standard output is used.

    :param str log: The logfile directory.
    :param boolean verbose: Verbose mode.
    :param str level: The log level.

    """
    logging.getLogger("github3").setLevel(logging.CRITICAL)  # Disables logging message from github3 library
    logging.getLogger("requests").setLevel(logging.CRITICAL)  # Disables logging message from request library
    logname = 'esgprep-{0}-{1}'.format(datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())
    formatter = logging.Formatter(fmt='%(levelname)-10s %(asctime)s %(message)s')
    if log:
        if not os.path.isdir(log):
            os.makedirs(log)
        logfile = os.path.join(log, logname)
    else:
        logfile = os.path.join(os.getcwd(), logname)
    logging.getLogger().setLevel(logging.DEBUG)
    error_handler = logging.FileHandler(filename='{0}.err'.format(logfile), delay=True)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logging.getLogger().addHandler(error_handler)
    if log:
        stream_handler = logging.FileHandler(filename='{0}.log'.format(logfile), delay=True)
    else:
        if verbose:
            stream_handler = logging.StreamHandler()
        else:
            stream_handler = logging.NullHandler()
    stream_handler.setLevel(logging.__dict__[level])
    stream_handler.addFilter(LogFilter(logging.WARNING))
    stream_handler.setFormatter(formatter)
    logging.getLogger().addHandler(stream_handler)


def walk(root, downstream=True, followlinks=False):
    """
    A wrapper from ``os.walk`` able to handle "downstream" and "upstream" tree parsing.
    If "down" argument is True calls usual ``os.walk``.
    :param string root: The directory to start walking
    :param boolean downstream: Walking the downstream tree if True
    :param boolean followlinks: If True to visit directories pointed to by symlinks (only if down is True)
    :returns: The current directory, its sub-directories and files list as a generator of tuple.
    :rtype: *iter*
    :raises Error: If the tree walking fails

    """
    if downstream:
        for root, dirs, files in os.walk(root, followlinks=followlinks):
            yield root, dirs, files
    else:
        root = os.path.realpath(root)
        try:
            items = os.listdir(root)
        except Exception as e:
            raise Exception(e)
        dirs, files = [], []
        for item in items:
            if os.path.isdir(os.path.join(root, item)):
                dirs.append(item)
            elif os.path.isfile(os.path.join(root, item)):
                files.append(item)
        yield root, dirs, files
        new_path = os.path.realpath(os.path.join(root, '..'))
        if new_path == root:
            return
        for x in walk(new_path, downstream=False):
            yield x
