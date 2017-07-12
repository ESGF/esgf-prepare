#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to use with this package.

"""

# Module imports
import logging
import os
import pickle
import re
import sys
from datetime import datetime

from tqdm import tqdm


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
    logname = 'esgprep-{}-{}'.format(datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())
    formatter = logging.Formatter(fmt='%(levelname)-10s %(asctime)s %(message)s')
    if log:
        if not os.path.isdir(log):
            os.makedirs(log)
        logfile = os.path.join(log, logname)
    else:
        logfile = os.path.join(os.getcwd(), logname)
    logging.getLogger().setLevel(logging.DEBUG)
    error_handler = logging.FileHandler(filename='{}.err'.format(logfile), delay=True)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logging.getLogger().addHandler(error_handler)
    if log:
        stream_handler = logging.FileHandler(filename='{}.log'.format(logfile), delay=True)
    else:
        if verbose:
            stream_handler = logging.StreamHandler()
        else:
            stream_handler = logging.NullHandler()
    stream_handler.setLevel(logging.__dict__[level])
    stream_handler.addFilter(LogFilter(logging.WARNING))
    stream_handler.setFormatter(formatter)
    logging.getLogger().addHandler(stream_handler)


def remove(pattern, string):
    """
    Removes a substring catched by a regular expression.

    :param str pattern: The regular expression to catch
    :param str string: The string to test
    :returns: The string without the catched substring
    :rtype: *str*

    """
    return re.compile(pattern).sub("", string)


def match(pattern, string):
    """
    Validates a string against a regular expression.
    Only match at the beginning of the string.

    :param str pattern: The regular expression to match
    :param str string: The string to test
    :returns: True is it matches
    :rtype: *boolean*

    """
    return True if re.match(re.compile(pattern), string) else False


def load(path):
    """
    Loads data from Pickle file.

    :param str path: The Pickle file path
    :returns: The data stored in the Pickle file
    :rtype: *object*

    """
    with open(path, 'rb') as f:
        while True:
            if f.read(1) == b'':
                return
            f.seek(-1, 1)
            yield pickle.load(f)


def store(path, data):
    """
    Stores data into a Pickle file.

    :param str path: The Pickle file path
    :param *list* data: The list of data objects

    """
    with open(path, 'wb') as f:
        for i in range(len(data)):
            pickle.dump(data[i], f)


def cmd_exists(cmd):
    """
    Checks if a Shell command exists.

    :returns: True if exists.
    :rtype: *boolean*

    """
    return any(
        os.access(os.path.join(path, cmd), os.X_OK)
        for path in os.environ["PATH"].split(os.pathsep)
    )


def as_pbar(iterable, desc, units, total=None):
    """
    Build progress pbar if desired

    :param *iterable* iterable: An iterable object
    :param str desc: The progress bar description
    :param str units: The progress bar units
    :param int total: The number of iterations
    :returns: The progress bar object as a list
    :rtype: *tqdm.tqdm* or *iter*

    """
    return tqdm(iterable,
                desc=desc,
                total=total or len(iterable),
                bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} ' + units,
                ncols=100,
                file=sys.stdout)
