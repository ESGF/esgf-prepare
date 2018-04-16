#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF data for publication.

"""

import os
import sys
from argparse import FileType
from importlib import import_module

from utils.constants import *
from utils.misc import init_logging
from utils.parser import MultilineFormatter, DirectoryChecker, regex_validator, _ArgumentParser

__version__ = 'from esgprep v{} {}'.format(VERSION, VERSION_DATE)


def get_args():
    """
    Returns parsed command-line arguments.

    :returns: The argument parser
    :rtype: *argparse.Namespace*

    """
    main = _ArgumentParser(
        prog='esgcheckvocab',
        description=PROGRAM_DESC['checkvocab'],
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog=EPILOG)
    main._optionals.title = OPTIONAL
    main._positionals.title = POSITIONAL
    main.add_argument(
        '-h', '--help',
        action='help',
        help=HELP)
    main.add_argument(
        '--test',
        action='store_true',
        default=False,
        help=TEST_HELP['program'])
    main.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s ({})'.format(__version__),
        help=VERSION_HELP)
    main.add_argument(
        '-i',
        metavar='/esg/config/esgcet',
        action=DirectoryChecker,
        default='/esg/config/esgcet',
        help=INI_HELP)
    main.add_argument(
        '--log',
        metavar='CWD',
        type=str,
        const='{}/logs'.format(os.getcwd()),
        nargs='?',
        help=LOG_HELP)
    main.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help=VERBOSE_HELP)
    group = main.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--directory',
        metavar='PATH',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP['checkvocab'])
    group.add_argument(
        '--dataset-list',
        metavar='TXT_FILE',
        type=FileType('r'),
        nargs='?',
        default=sys.stdin,
        help=DATASET_LIST_HELP)
    main.add_argument(
        '--project',
        metavar='PROJECT_ID',
        type=str,
        required=True,
        help=PROJECT_HELP['checkvocab'])
    main.add_argument(
        '--ignore-dir',
        metavar="PYTHON_REGEX",
        type=regex_validator,
        default='^.*/(files|latest|\.[\w]*).*$',
        help=IGNORE_DIR_HELP)
    main.add_argument(
        '--include-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=INCLUDE_FILE_HELP)
    main.add_argument(
        '--exclude-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=EXCLUDE_FILE_HELP)
    return main.parse_args()


def run():
    """
    Run main program

    """
    # Get command-line arguments
    args = get_args()
    # Initialize logger depending on log and debug mode
    init_logging(log=args.log, debug=args.debug)
    # Print progress bar if no log and no debug mode
    setattr(args, 'pbar', True if not args.log and not args.debug else False)
    # Run program
    if args.test:
        print('"esgcheckvocab" test suite not available. Coming soon!')
        exit()
        #  test = import_module('.test', package='esgprep.mapfile')
        #  test.run()
    else:
        main = import_module('.main', package='esgprep.checkvocab')
        main.run(args)


if __name__ == "__main__":
    run()
