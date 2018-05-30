#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF data for publication.

"""

import argparse
import os
import sys
from argparse import FileType
from importlib import import_module

from utils.constants import *
from utils.misc import init_logging
from utils.parser import MultilineFormatter, DirectoryChecker, VersionChecker, regex_validator, _ArgumentParser

__version__ = 'from esgprep v{} {}'.format(VERSION, VERSION_DATE)


def get_args():
    """
    Returns parsed command-line arguments.

    :returns: The argument parser
    :rtype: *argparse.Namespace*

    """
    main = _ArgumentParser(
        prog='esgmapfile',
        description=PROGRAM_DESC['mapfile'],
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
    # Parent parser with common arguments
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
    parent.add_argument(
        '--project',
        metavar='PROJECT_ID',
        type=str,
        required=True,
        help=PROJECT_HELP['mapfile'])
    parent.add_argument(
        '--mapfile',
        metavar='{dataset_id}.{version}.map',
        type=str,
        default='{dataset_id}.{version}.map',
        help=MAPFILE_NAME_HELP)
    parent.add_argument(
        '--outdir',
        metavar='CWD/mapfiles',
        type=str,
        default=os.path.join(os.getcwd(), 'mapfiles'),
        help=OUTDIR_HELP)
    group = parent.add_mutually_exclusive_group(required=False)
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
    parent.add_argument(
        '--no-version',
        action='store_true',
        default=False,
        help=NO_VERSION_HELP)
    parent.add_argument(
        '--ignore-dir',
        metavar='\"^.*/(files|\.\w*).*$\"',
        type=str,
        default='^.*/(files|\.[\w]*).*$',
        help=IGNORE_DIR_HELP)
    parent.add_argument(
        '--include-file',
        metavar='\"^.*\.nc$\"',
        type=regex_validator,
        action='append',
        help=INCLUDE_FILE_HELP)
    parent.add_argument(
        '--exclude-file',
        metavar='\"^\..*$\"',
        type=regex_validator,
        action='append',
        help=EXCLUDE_FILE_HELP)
    parent.add_argument(
        '--dataset-name',
        metavar='DATASET_NAME',
        type=str,
        help=DATASET_NAME_HELP)
    parent.add_argument(
        '--max-threads',
        metavar='4',
        type=int,
        default=4,
        help=MAX_THREADS_HELP)
    parent.add_argument(
        '--no-cleanup',
        action='store_true',
        default=False,
        help=NO_CLEANUP_HELP)
    # Subparser for "esgmapfile make"
    make = subparsers.add_parser(
        'make',
        prog='esgmapfile make',
        description=MAPFILE_SUBCOMMANDS['make'],
        formatter_class=MultilineFormatter,
        help=MAPFILE_HELPS['make'],
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
        '--no-checksum',
        action='store_true',
        default=False,
        help=NO_CHECKSUM_HELP['mapfile'])
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
        '--checksums-from',
        metavar='CHECKSUM_FILE',
        type=FileType('r'),
        help=CHECKSUMS_FROM_HELP)
    # Subparser for "esgmapfile show"
    show = subparsers.add_parser(
        'show',
        prog='esgmapfile show',
        description=MAPFILE_SUBCOMMANDS['show'],
        formatter_class=MultilineFormatter,
        help=MAPFILE_HELPS['show'],
        add_help=False,
        parents=[parent])
    show._optionals.title = OPTIONAL
    show._positionals.title = POSITIONAL
    group = show.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--directory',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP['mapfile'])
    group.add_argument(
        '--dataset-list',
        metavar='TXT_FILE',
        type=FileType('r'),
        nargs='?',
        const=sys.stdin,
        help=DATASET_LIST_HELP)
    group.add_argument(
        '--dataset-id',
        metavar='DATASET_ID',
        type=str,
        help=DATASET_ID_HELP)
    show.add_argument(
        '--quiet',
        action='store_true',
        default=False,
        help=QUIET_HELP)
    show.add_argument(
        '--basename',
        action='store_true',
        default=False,
        help=BASENAME_HELP)
    main.set_default_subparser('make')
    return main.parse_args()


def run():
    """
    Run main program

    """
    # Get command-line arguments
    args = get_args()
    # Initialize logger depending on log and debug mode
    init_logging(log=args.log, debug=args.debug)
    # Print progress bar if no log, no debug and no silent mode
    if hasattr(args, 'quiet'):
        setattr(args, 'pbar', True if not args.log and not args.debug and not args.quiet else False)
    else:
        setattr(args, 'pbar', True if not args.log and not args.debug else False)
    # Run program
    if args.test:
        print('"esgmapfile" test suite not available. Coming soon!')
        exit()
        #  test = import_module('.test', package='esgprep.mapfile')
        #  test.run()
    else:
        main = import_module('.main', package='esgprep.mapfile')
        main.run(args)


if __name__ == "__main__":
    run()
