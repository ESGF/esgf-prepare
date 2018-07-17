#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF data for publication.

"""
import os
import sys
from argparse import FileType

from esgprep.checkvocab.main import run
from utils.constants import *
from utils.parser import MultilineFormatter, DirectoryChecker, regex_validator, CustomArgumentParser, keyval_converter, \
    processes_validator

__version__ = 'from esgprep v{} {}'.format(VERSION, VERSION_DATE)


def get_args():
    """
    Returns parsed command-line arguments.

    :returns: The argument parser
    :rtype: *argparse.Namespace*

    """
    main = CustomArgumentParser(
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
        '-v', '--version',
        action='version',
        version='%(prog)s ({})'.format(__version__),
        help=VERSION_HELP)
    main.add_argument(
        '-i',
        metavar='$ESGINI',
        action=DirectoryChecker,
        default=os.environ['ESGINI'] if 'ESGINI' in os.environ.keys() else '/esg/config/esgcet',
        help=INI_HELP)
    main.add_argument(
        '-l', '--log',
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
        '--incoming',
        metavar='PATH',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP['checkvocab'])
    group.add_argument(
        '--dataset-id',
        metavar='DATASET_ID',
        type=str,
        help=DATASET_ID_HELP)
    group.add_argument(
        '--dataset-list',
        metavar='TXT_FILE',
        type=FileType('r'),
        nargs='?',
        const=sys.stdin,
        help=DATASET_LIST_HELP)
    main.add_argument(
        '-p', '--project',
        metavar='PROJECT_ID',
        type=str,
        required=True,
        help=PROJECT_HELP['checkvocab'])
    main.add_argument(
        '--set-key',
        metavar='FACET_KEY=ATTRIBUTE',
        type=keyval_converter,
        action='append',
        help=SET_KEY_HELP)
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
    main.add_argument(
        '--max-processes',
        metavar='4',
        type=processes_validator,
        default=4,
        help=MAX_PROCESSES_HELP)
    return main.prog, main.parse_args()


def main():
    """
    Run main program

    """
    # Get command-line arguments
    prog, args = get_args()
    setattr(args, 'prog', prog)
    if not hasattr(args, 'quiet'):
        setattr(args, 'quiet', None)
    # Run program
    run(args)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
