#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to use with this package.

"""

import hashlib
import logging
import os
import pickle
import re
from datetime import datetime

from custom_exceptions import *


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


def init_logging(log, debug=False, level='INFO'):
    """
    Initiates the logging configuration (output, date/message formatting).
    If a directory is submitted the logfile name is unique and formatted as follows:
    ``name-YYYYMMDD-HHMMSS-JOBID.log``If ``None`` the standard output is used.

    :param str log: The logfile directory.
    :param boolean debug: Debug mode.
    :param str level: The log level.

    """
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
        if debug:
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


def match(pattern, string, inclusive=True):
    """
    Validates a string against a regular expression.
    Only match at the beginning of the string.
    Default is to match inclusive regex.

    :param str pattern: The regular expression to match
    :param str string: The string to test
    :param boolean inclusive: False if negative matching (i.e., exclude the regex)
    :returns: True if it matches
    :rtype: *boolean*

    """
    # Assert inclusive and exclusive flag are mutually exclusive
    if inclusive:
        return True if re.search(pattern, string) else False
    else:
        return True if not re.search(pattern, string) else False


def load(path):
    """
    Loads data from Pickle file.

    :param str path: The Pickle file path
    :returns: The Pickle file content
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
    :param *list* data: A list of data objects to store

    """
    with open(path, 'wb') as f:
        for i in range(len(data)):
            pickle.dump(data[i], f)


def evaluate(results):
    """
    Evaluates a list depending on absence/presence of None values.

    :param list results: The list to evaluate
    :returns: True if no blocking errors
    :rtype: *boolean*

    """
    if all(results) and any(results):
        # The list contains only True value = no errors
        return True
    elif not all(results) and any(results):
        # The list contains some None values = some errors occurred
        return True
    else:
        return False


def checksum(ffp, checksum_type, include_filename=False, human_readable=True):
    """
    Does the checksum by the Shell avoiding Python memory limits.

    :param str ffp: The file full path
    :param str checksum_type: Checksum type
    :param boolean human_readable: True to return a human readable digested message
    :param boolean include_filename: True to include filename in hash calculation
    :returns: The checksum
    :rtype: *str*
    :raises Error: If the checksum fails

    """
    try:
        hash_algo = getattr(hashlib, checksum_type)()
        with open(ffp, 'rb') as f:
            for block in iter(lambda: f.read(os.stat(ffp).st_blksize), b''):
                hash_algo.update(block)
        if include_filename:
            hash_algo.update(os.path.basename(ffp))
        if human_readable:
            return hash_algo.hexdigest()
        else:
            return hash_algo.digest()
    except AttributeError:
        raise InvalidChecksumType(checksum_type)
    except:
        raise ChecksumFail(ffp, checksum_type)
