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

    #############################
    # Main parser for "esgprep" #
    #############################
    main = _ArgumentParser(
        prog='esgprep',
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
        dest='cmd',
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

    #####################################
    # Subparser for "esgprep fetch-ini" #
    #####################################
    fetchini = subparsers.add_parser(
        'fetch-ini',
        prog='esgprep fetch-ini',
        description=FETCHINI_DESC,
        formatter_class=MultilineFormatter,
        help=FETCHINI_HELP,
        add_help=False,
        parents=[parent])
    fetchini._optionals.title = OPTIONAL
    fetchini._positionals.title = POSITIONAL
    fetchini.add_argument(
        '--project',
        metavar='PROJECT_ID',
        type=str,
        nargs='+',
        help=PROJECT_HELP['fetch-ini'])
    group = fetchini.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '-k',
        action='store_true',
        default=False,
        help=KEEP_HELP)
    group.add_argument(
        '-o',
        action='store_true',
        default=False,
        help=OVERWRITE_HELP)
    fetchini.add_argument(
        '-b',
        metavar='one_version',
        choices=['one_version', 'keep_versions'],
        type=str,
        nargs='?',
        const='one_version',
        help=BACKUP_HELP)
    fetchini.add_argument(
        '--gh-user',
        metavar='USERNAME',
        type=str,
        help=GITHUB_USER_HELP)
    fetchini.add_argument(
        '--gh-password',
        metavar='PASSWORD',
        type=str,
        help=GITHUB_PASSWORD_HELP)
    fetchini.add_argument(
        '--devel',
        action='store_true',
        default=False,
        help=DEVEL_HELP)

    #######################################
    # Subparser for "esgprep check-vocab" #
    #######################################
    checkvocab = subparsers.add_parser(
        'check-vocab',
        prog='esgprep check-vocab',
        description=CHECKVOCAB_DESC,
        formatter_class=MultilineFormatter,
        help=CHECKVOCAB_HELP,
        add_help=False,
        parents=[parent])
    checkvocab._optionals.title = OPTIONAL
    checkvocab._positionals.title = POSITIONAL
    group = checkvocab.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--directory',
        metavar='PATH',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP['check-vocab'])
    group.add_argument(
        '--dataset-list',
        metavar='TXT_FILE',
        type=str,
        help=DATASET_LIST_HELP)
    checkvocab.add_argument(
        '--project',
        metavar='PROJECT_ID',
        type=str,
        required=True,
        help=PROJECT_HELP['check-vocab'])
    checkvocab.add_argument(
        '--ignore-dir',
        metavar="PYTHON_REGEX",
        type=regex_validator,
        default='^.*/(files|latest|\.[\w]*).*$',
        help=IGNORE_DIR_HELP)
    checkvocab.add_argument(
        '--include-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=INCLUDE_FILE_HELP)
    checkvocab.add_argument(
        '--exclude-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=EXCLUDE_FILE_HELP)

    ###############################
    # Subparser for "esgprep drs" #
    ###############################
    drs = subparsers.add_parser(
        'drs',
        prog='esgprep drs',
        description=DRS_DESC,
        formatter_class=MultilineFormatter,
        help=DRS_HELP,
        add_help=False,
        parents=[parent])
    drs._optionals.title = OPTIONAL
    drs._positionals.title = POSITIONAL
    drs.add_argument(
        'action',
        choices=['list', 'tree', 'todo', 'upgrade'],
        metavar='action',
        type=str,
        help=ACTION_HELP['drs'])
    drs.add_argument(
        'directory',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP['drs'])
    drs.add_argument(
        '--project',
        metavar='PROJECT_ID',
        type=str,
        required=True,
        help=PROJECT_HELP['drs'])
    drs.add_argument(
        '--root',
        metavar='CWD',
        action=DirectoryChecker,
        default=os.getcwd(),
        help=ROOT_HELP)
    drs.add_argument(
        '--version',
        metavar=datetime.now().strftime("%Y%m%d"),
        action=VersionChecker,
        default=datetime.now().strftime('%Y%m%d'),
        help=SET_VERSION_HELP['drs'])
    drs.add_argument(
        '--set-value',
        metavar='FACET_KEY=VALUE',
        type=keyval_converter,
        action='append',
        help=SET_VALUE_HELP)
    drs.add_argument(
        '--set-key',
        metavar='FACET_KEY=ATTRIBUTE',
        type=keyval_converter,
        action='append',
        help=SET_KEY_HELP)
    drs.add_argument(
        '--rescan',
        action='store_true',
        default=False,
        help=RESCAN_HELP)
    drs.add_argument(
        '--commands-file',
        metavar='TXT_FILE',
        action=FileChecker,
        help=COMMANDS_FILE_HELP)
    drs.add_argument(
        '--overwrite-commands-file',
        action='store_true',
        default=False,
        help=OVERWRITE_COMMANDS_FILE_HELP)
    drs.add_argument(
        '--upgrade-from-latest',
        action='store_true',
        default=False,
        help=UPGRADE_FROM_LATEST_HELP)
    drs.add_argument(
        '--ignore-from-latest',
        metavar='TXT_FILE',
        action=FileChecker,
        help=IGNORE_FROM_LATEST_HELP)
    group = drs.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--copy',
        action='store_true',
        default=False,
        help=COPY_HELP)
    group.add_argument(
        '--link',
        action='store_true',
        default=False,
        help=LINK_HELP)
    group.add_argument(
        '--symlink',
        action='store_true',
        default=False,
        help=SYMLINK_HELP)
    drs.add_argument(
        '--max-threads',
        metavar=4,
        type=int,
        default=4,
        help=MAX_THREADS_HELP)

    ###################################
    # Subparser for "esgprep mapfile" #
    ###################################
    mapfile = subparsers.add_parser(
        'mapfile',
        prog='esgprep mapfile',
        description=MAPFILE_DESC,
        formatter_class=MultilineFormatter,
        help=MAPFILE_HELP,
        add_help=False,
        parents=[parent])
    mapfile._optionals.title = OPTIONAL
    mapfile._positionals.title = POSITIONAL
    # mapfile.add_argument(
    #     'action',
    #     choices=['make', 'show'],
    #     metavar='action',
    #     nargs='?',
    #     default='make',
    #     type=str,
    #     help=ACTION_HELP['mapfile'])
    mapfile.add_argument(
        'directory',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP['mapfile'])
    mapfile.add_argument(
        '--project',
        metavar='PROJECT_ID',
        type=str,
        required=True,
        help=PROJECT_HELP['mapfile'])
    mapfile.add_argument(
        '--mapfile',
        metavar='{dataset_id}.{version}.map',
        type=str,
        default='{dataset_id}.{version}.map',
        help=MAPFILE_NAME_HELP)
    mapfile.add_argument(
        '--outdir',
        metavar='CWD/mapfiles',
        type=str,
        default=os.path.join(os.getcwd(), 'mapfiles'),
        help=OUTDIR_HELP)
    group = mapfile.add_mutually_exclusive_group(required=False)
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
    mapfile.add_argument(
        '--no-version',
        action='store_true',
        default=False,
        help=NO_VERSION_HELP)
    mapfile.add_argument(
        '--no-checksum',
        action='store_true',
        default=False,
        help=NO_CHECKSUM_HELP)
    mapfile.add_argument(
        '--ignore-dir',
        metavar="PYTHON_REGEX",
        type=str,
        default='^.*/(files|\.[\w]*).*$',
        help=IGNORE_DIR_HELP)
    mapfile.add_argument(
        '--include-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=INCLUDE_FILE_HELP)
    mapfile.add_argument(
        '--exclude-file',
        metavar='PYTHON_REGEX',
        type=regex_validator,
        action='append',
        help=EXCLUDE_FILE_HELP)
    mapfile.add_argument(
        '--tech-notes-url',
        metavar='URL',
        type=str,
        help=TECH_NOTES_URL_HELP)
    mapfile.add_argument(
        '--tech-notes-title',
        metavar='TITLE',
        type=str,
        help=TECH_NOTES_TITLE_HELP)
    mapfile.add_argument(
        '--dataset',
        metavar='DATASET_ID',
        type=str,
        help=DATASET_HELP)
    mapfile.add_argument(
        '--max-threads',
        metavar=4,
        type=int,
        default=4,
        help=MAX_THREADS_HELP)
    mapfile.add_argument(
        '--no-cleanup',
        action='store_true',
        default=False,
        help=NO_CLEANUP_HELP)

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
        # Run test suite
        print('"esgprep" test suite not available. Coming soon!')
        exit()
        testsuite = unittest.TestLoader().discover('.')
        unittest.TextTestRunner().run(testsuite)
    else:
        # Run subcommand
        module_name = args.cmd.lower().replace('-', '')
        if args.test:
            test = import_module('.test', package='esgprep.{}'.format(module_name))
            test.run()
        else:
            main = import_module('.main', package='esgprep.{}'.format(module_name))
            main.run(args)


if __name__ == "__main__":
    # PyCharm workaround
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    run()
