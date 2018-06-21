#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF data for publication.

"""

import os
from importlib import import_module

from utils.constants import *
from utils.misc import init_logging
from utils.parser import MultilineFormatter, _ArgumentParser, regex_validator

__version__ = 'from esgprep v{} {}'.format(VERSION, VERSION_DATE)


def get_args():
    """
    Returns parsed command-line arguments.

    :returns: The argument parser
    :rtype: *argparse.Namespace*

    """
    main = _ArgumentParser(
        prog='esgfetchtables',
        description=PROGRAM_DESC['fetchtables'],
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
        '--tables-dir',
        metavar='/usr/local/',
        type=str,
        default='/usr/local/',
        help=TABLES_DIR_HELP)
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
    main.add_argument(
        '--project',
        metavar='PROJECT_ID',
        type=str,
        nargs='+',
        help=PROJECT_HELP['fetchini'])
    group = main.add_mutually_exclusive_group(required=False)
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
    main.add_argument(
        '-b',
        metavar='one_version',
        choices=['one_version', 'keep_versions'],
        type=str,
        nargs='?',
        const='one_version',
        help=BACKUP_HELP)
    main.add_argument(
        '--no-ref-folder',
        action='store_true',
        default=False,
        help=NO_REF_FOLDER_HELP)
    main.add_argument(
        '--gh-user',
        metavar='USERNAME',
        type=str,
        default=os.environ['GH_USER'] if 'GH_USER' in os.environ.keys() else None,
        help=GITHUB_USER_HELP)
    main.add_argument(
        '--gh-password',
        metavar='PASSWORD',
        type=str,
        default=os.environ['GH_PASSWORD'] if 'GH_PASSWORD' in os.environ.keys() else None,
        help=GITHUB_PASSWORD_HELP)
    ref = main.add_mutually_exclusive_group(required=False)
    ref.add_argument(
        '--tag',
        metavar='TAG',
        type=str,
        help=TAG_HELP)
    ref.add_argument(
        '--tag-regex',
        metavar='REGEX',
        type=str,
        help=TAG_REGEX_HELP)
    ref.add_argument(
        '--branch',
        metavar='BRANCH',
        default='master',
        type=str,
        help=BRANCH_HELP)
    ref.add_argument(
        '--branch-regex',
        metavar='REGEX',
        type=str,
        help=BRANCH_REGEX_HELP)
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
        print('"esgfetchtables" test suite not available. Coming soon!')
        exit()
        #  test = import_module('.test', package='esgprep.mapfile')
        #  test.run()
    else:
        main = import_module('.main', package='esgprep.fetchtables')
        main.run(args)


if __name__ == "__main__":
    run()
