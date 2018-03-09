#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF data for publication.

"""

import argparse
import os
import sys
import unittest
from importlib import import_module

from utils.constants import *
from utils.misc import init_logging
from utils.parser import MultilineFormatter, DirectoryChecker, VersionChecker, keyval_converter, regex_validator, \
    _ArgumentParser, FileChecker

__version__ = 'v{} {}'.format(VERSION, VERSION_DATE)


def get_args():
    """
    Returns parsed command-line arguments.

    :returns: The argument parser
    :rtype: *argparse.Namespace*

    """
    # Workaround to run the test suite without subparsers and their required flags
    if len(sys.argv[1:]) == 1 and sys.argv[1:][-1] == '--test':
        return argparse.Namespace(**{'cmd': None, 'test': True, 'log': None, 'v': False})
    if len(sys.argv[1:]) == 2 and sys.argv[1:][-1] == '--test':
        return argparse.Namespace(**{'cmd': sys.argv[1:][-2], 'test': True, 'log': None, 'v': False})

    ################################
    # Main parser for "esgmapfile" #
    ################################
    main = _ArgumentParser(
        prog='esgmapfile',
        description=PROGRAM_DESC,
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
    subparsers = main.add_subparsers(
        title=SUBCOMMANDS,
        dest='action',
        metavar='',
        help='')

    #######################################
    # Parent parser with common arguments #
    #######################################
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        '-h', '--help',
        action='help',
        help=HELP)
    parent.add_argument(
        '-i',
        metavar='/esg/config/esgcet',
        action=DirectoryChecker,
        default='/esg/config/esgcet',
        help=INI_HELP)
    parent.add_argument(
        '--log',
        metavar='CWD',
        type=str,
        const='{}/logs'.format(os.getcwd()),
        nargs='?',
        help=LOG_HELP)
    parent.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help=VERBOSE_HELP)
    parent.add_argument(
        '--test',
        action='store_true',
        default=False,
        help=TEST_HELP['parent'])

    ###################################
    # Subparser for "esgmapfile make" #
    ###################################
    make = subparsers.add_parser(
        'make',
        prog='esgmapfile make',
        description=MAPFILE_DESC,
        formatter_class=MultilineFormatter,
        help=MAPFILE_HELP,
        add_help=False,
        parents=[parent])
    make._optionals.title = OPTIONAL
    make._positionals.title = POSITIONAL
    make.add_argument(
        'directory',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP['mapfile'])
    make.add_argument(
        '--project',
        metavar='PROJECT_ID',
        type=str,
        required=True,
        help=PROJECT_HELP['mapfile'])
    make.add_argument(
        '--mapfile',
        metavar='{dataset_id}.{version}.map',
        type=str,
        default='{dataset_id}.{version}.map',
        help=MAPFILE_NAME_HELP)
    make.add_argument(
        '--outdir',
        metavar='CWD/mapfiles',
        type=str,
        default=os.path.join(os.getcwd(), 'mapfiles'),
        help=OUTDIR_HELP)
    group = make.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--all-versions',
        action='store_true',
        default=False,
        help=ALL_VERSIONS_HELP)
    group.add_argument(
        '--version',
        metavar=datetime.now().strftime("%Y%m%d"),
        action=VersionChecker,
        help=SET_VERSION_HELP['mapfile'])
    group.add_argument(
        '--latest-symlink',
        action='store_true',
        default=False,
        help=LATEST_SYMLINK_HELP)
    make.add_argument(
        '--no-version',
        action='store_true',
        default=False,
        help=NO_VERSION_HELP)
    make.add_argument(
        '--no-checksum',
        action='store_true',
        default=False,
        help=NO_CHECKSUM_HELP)
    make.add_argument(
        '--ignore-dir',
        metavar="PYTHON_REGEX",
        type=str,
        default='^.*/(files|\.[\w]*).*$',
        help=IGNORE_DIR_HELP)
    make.add_argument(
        '--include-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=INCLUDE_FILE_HELP)
    make.add_argument(
        '--exclude-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=EXCLUDE_FILE_HELP)
    make.add_argument(
        '--tech-notes-url',
        metavar='URL',
        type=str,
        help=TECH_NOTES_URL_HELP)
    make.add_argument(
        '--tech-notes-title',
        metavar='TITLE',
        type=str,
        help=TECH_NOTES_TITLE_HELP)
    make.add_argument(
        '--dataset',
        metavar='DATASET_ID',
        type=str,
        help=DATASET_HELP)
    make.add_argument(
        '--max-threads',
        metavar=4,
        type=int,
        default=4,
        help=MAX_THREADS_HELP)
    make.add_argument(
        '--no-cleanup',
        action='store_true',
        default=False,
        help=NO_CLEANUP_HELP)
    ###################################
    # Subparser for "esgmapfile show" #
    ###################################
    show = subparsers.add_parser(
        'show',
        prog='esgmapfile show',
        description=MAPFILE_DESC,
        formatter_class=MultilineFormatter,
        help=MAPFILE_HELP,
        add_help=False,
        parents=[parent])
    show._optionals.title = OPTIONAL
    show._positionals.title = POSITIONAL
    group = show.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--dataset',
        metavar='DATASET_ID',
        type=str,
        help=DATASET_HELP)
    group.add_argument(
        '--dataset-list',
        metavar='DATASET_ID',
        type=str,
        help=DATASET_HELP)
    group.add_argument(
        '--directory',
        metavar='DIRECTORY',
        type=str,
        help=DIRECTORY_HELP
    )
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
        test = import_module('.test', package='esgprep.mapfile')
        test.run()
    else:
        main = import_module('.main', package='esgprep.mapfile')
        main.run(args)


if __name__ == "__main__":
    # PyCharm workaround
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    run()
