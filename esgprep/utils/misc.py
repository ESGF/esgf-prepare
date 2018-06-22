#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Useful functions to use with this package.

"""

import hashlib
import os
import pickle
import re

from custom_exceptions import *


class ProcessContext(object):
    """
    Encapsulates the processing context/information for child process.

    :param dict args: Dictionary of argument to pass to child process
    :returns: The processing context
    :rtype: *ProcessContext*

    """

    def __init__(self, args):
        assert isinstance(args, dict)
        for key, value in args.items():
            setattr(self, key, value)


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
            blocksize = os.stat(ffp).st_blksize
            for block in iter(lambda: f.read(blocksize), b''):
                hash_algo.update(block)
        if include_filename:
            hash_algo.update(os.path.basename(ffp))
        if human_readable:
            return hash_algo.hexdigest()
        else:
            return hash_algo.digest()
    except AttributeError:
        raise InvalidChecksumType(checksum_type)
    except KeyboardInterrupt:
        raise
    except Exception:
        raise ChecksumFail(ffp, checksum_type)
