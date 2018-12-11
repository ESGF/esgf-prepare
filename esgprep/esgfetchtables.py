#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF data for publication.

"""

from esgprep.fetchtables.main import run
from utils.constants import *
from utils.help import *
from utils.parser import *

__version__ = 'from esgprep v{} {}'.format(VERSION, VERSION_DATE)


def get_args():
    """
    Returns parsed command-line arguments.

    :returns: The argument parser
    :rtype: *argparse.Namespace*

    """
    main = CustomArgumentParser(
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
        '-v', '--version',
        action='version',
        version='%(prog)s ({})'.format(__version__),
        help=VERSION_HELP)
    main.add_argument(
        '--tables-dir',
        metavar='$CMOR_TABLES',
        type=str,
        default=os.environ['CMOR_TABLES'] if 'CMOR_TABLES' in os.environ.keys() else '/usr/local/',
        help=TABLES_DIR_HELP)
    main.add_argument(
        '-l', '--log',
        metavar='CWD',
        type=str,
        const='{}/logs'.format(os.getcwd()),
        nargs='?',
        help=LOG_HELP)
    main.add_argument(
        '-d', '--debug',
        action='store_true',
        default=False,
        help=VERBOSE_HELP)
    main.add_argument(
        '-p', '--project',
        metavar='NAME',
        type=str,
        nargs='+',
        help=PROJECT_HELP['fetchtables'])
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
        '--no-subfolder',
        action='store_true',
        default=False,
        help=NO_SUBFOLDER_HELP)
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
        metavar="'^.*$'",
        type=regex_validator,
        action='append',
        help=INCLUDE_FILE_HELP['fetchtables'])
    main.add_argument(
        '--exclude-file',
        metavar="'^\..*$'",
        type=regex_validator,
        action='append',
        help=EXCLUDE_FILE_HELP)
    group = main.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--color',
        action='store_true',
        help=COLOR_HELP)
    group.add_argument(
        '--no-color',
        action='store_true',
        help=NO_COLOR_HELP)
    return main.prog, main.parse_args()


def main():
    """
    Run main program

    """
    # Get command-line arguments
    prog, args = get_args()
    setattr(args, 'prog', prog)
    # Run program
    run(args)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
