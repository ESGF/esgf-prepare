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
import sys
from ctypes import c_char_p
from multiprocessing import Value

import requests

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
    except:
        raise ChecksumFail(ffp, checksum_type)


def get_checksum_pattern(checksum_type):
    """
    Build the checksum pattern depending on the checksum type.

    :param str checksum_type: The checksum type
    :return: The checksum pattern
    :rtype: *re.Object*

    """
    hash_algo = getattr(hashlib, checksum_type)()
    checksum_length = len(hash_algo.hexdigest())
    return re.compile('^[0-9a-f]{{{}}}$'.format(checksum_length))


def gh_request_content(url, auth=None):
    """
    Gets the GitHub content of a file or a directory.

    :param str url: The GitHub url to request
    :param *requests.auth.HTTPBasicAuth* auth: The authenticator object
    :returns: The GitHub request content
    :rtype: *requests.models.Response*
    :raises Error: If user not authorized to read GitHub repository
    :raises Error: If user exceed the GitHub API rate limit
    :raises Error: If the queried content does not exist
    :raises Error: If the GitHub request fails for other reasons

    """
    GitHubException.URI = url
    r = requests.get(url, auth=auth)
    if r.status_code == 200:
        return r
    elif r.status_code == 401:
        raise GitHubUnauthorized()
    elif r.status_code == 403:
        raise GitHubAPIRateLimit(int(r.headers['X-RateLimit-Reset']))
    elif r.status_code == 404:
        raise GitHubFileNotFound()
    else:
        raise GitHubConnectionError()


def backup(f, mode=None):
    """
    Backup a local file following different modes:

     * "one_version" renames the existing file in its source directory adding a ".bkp" extension to the filename.
     * "keep_versions" moves the existing file in a child directory called "bkp" and add a timestamp to the filename.

    :param str f: The file to backup
    :param str mode: The backup mode to follow

    """
    if os.path.isfile(f):
        if mode == 'one_version':
            dst = '{}.bkp'.format(f)
            os.rename(f, dst)
        elif mode == 'keep_versions':
            bkpdir = os.path.join(os.path.dirname(f), 'bkp')
            dst = os.path.join(bkpdir, '{}.{}'.format(datetime.now().strftime('%Y%m%d-%H%M%S'),
                                                      os.path.basename(f)))
            try:
                os.makedirs(bkpdir)
            except OSError:
                pass
            finally:
                # Overwritten silently if destination file already exists
                os.rename(f, dst)
        else:
            # No backup = default
            pass


def write_content(outfile, content):
    """
    Write GitHub content into a file.

    :param str outfile: The output file
    :param str content: The file content to write

    """
    with open(outfile, 'w+') as f:
        f.write(content.encode('utf-8'))


def do_fetching(f, remote_checksum, keep, overwrite):
    """
    Returns True or False depending on decision schema

    :param str f: The file to test
    :param str remote_checksum: The remote file checksum
    :param boolean overwrite: True if overwrite existing files
    :param boolean keep: True if keep existing files
    :returns: True depending on the conditions
    :rtype: *boolean*

    """
    if overwrite:
        return True
    else:
        if not os.path.isfile(f):
            return True
        else:
            if githash(f) == remote_checksum:
                return False
            else:
                msg = COLORS.BOLD + 'Local "{}" does not match version on GitHub -- '.format((os.path.basename(f)))
                msg += 'The file is either outdated or was modified.' + COLORS.ENDC
                Print.warning(msg)
                if keep:
                    return False
                else:
                    return True


def githash(outfile):
    """
    Makes Git checksum (as called by "git hash-object") of a file

    :param outfile:
    :returns: The SHA1 sum

    """
    with open(outfile) as f:
        data = f.read()
    s = hashlib.sha1()
    s.update("blob %u\0" % len(data))
    s.update(data)
    return unicode(s.hexdigest())


class COLORS:
    """
    Background colors for print statements

    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[1;32m'
    WARNING = '\033[1;93m'
    FAIL = '\033[1;31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Print(object):
    """
    Class to manage and dispatch print statement depending on log and debug mode.

    """
    LOG = None
    DEBUG = False
    CMD = None
    BUFFER = Value(c_char_p, '')
    LOGFILE = None
    ERRFILE = None

    @staticmethod
    def init(log, debug, cmd):
        Print.LOG = log
        Print.DEBUG = debug
        Print.CMD = cmd
        logname = '{}-{}'.format(Print.CMD, datetime.now().strftime("%Y%m%d-%H%M%S"))
        if Print.LOG:
            logdir = Print.LOG
            if not os.path.isdir(Print.LOG):
                os.makedirs(Print.LOG)
        else:
            logdir = os.getcwd()
        Print.LOGFILE = os.path.join(logdir, logname + '.log')
        Print.ERRFILE = os.path.join(logdir, logname + '.err')

    @staticmethod
    def print_to_stdout(msg):
        sys.stdout.write(msg)
        sys.stdout.flush()

    @staticmethod
    def print_to_logfile(msg):
        with open(Print.LOGFILE, 'a+') as f:
            for color in COLORS.__dict__.values():
                msg = msg.replace(color, '')
            f.write(msg)

    @staticmethod
    def print_to_errfile(msg):
        with open(Print.ERRFILE, 'a+') as f:
            for color in COLORS.__dict__.values():
                msg = msg.replace(color, '')
            f.write(msg)

    @staticmethod
    def progress(msg):
        if Print.LOG:
            Print.print_to_stdout(msg)
        elif not Print.DEBUG:
            Print.print_to_stdout(msg)

    @staticmethod
    def command(msg):
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)

    @staticmethod
    def log(msg):
        if Print.LOG:
            Print.print_to_stdout(msg)

    @staticmethod
    def summary(msg):
        if Print.LOG:
            Print.print_to_stdout(msg)
            Print.print_to_logfile(msg)
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def info(msg):
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)

    @staticmethod
    def debug(msg):
        if Print.DEBUG:
            if Print.LOG:
                Print.print_to_logfile(msg)
            else:
                Print.print_to_stdout(msg)

    @staticmethod
    def warning(msg):
        msg = COLORS.WARNING + '\n:: WARNING :: ' + COLORS.ENDC + '{}'.format(msg)
        if Print.LOG:
            Print.print_to_logfile(msg)
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def error(msg, buffer=False):
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)
        elif buffer:
            Print.BUFFER.value += msg
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def success(msg, buffer=False):
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)
        elif buffer:
            Print.BUFFER.value += msg
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def exception(msg, buffer=False):
        msg = COLORS.FAIL + '\n:: SKIPPED :: ' + COLORS.ENDC + '{}'.format(msg)
        if Print.LOG:
            Print.print_to_logfile(msg)
        elif Print.DEBUG:
            Print.print_to_stdout(msg)
        elif buffer:
            Print.BUFFER.value += msg
        else:
            Print.print_to_stdout(msg)

    @staticmethod
    def flush():
        if Print.BUFFER.value:
            Print.BUFFER.value = '\n' + Print.BUFFER.value
            if Print.LOG:
                Print.print_to_logfile(Print.BUFFER.value)
            else:
                Print.print_to_stdout(Print.BUFFER.value)
