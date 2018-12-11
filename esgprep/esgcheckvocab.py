#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF data for publication.

"""
from argparse import FileType

from esgprep.checkvocab.main import run
from esgprep.utils.help import *
from utils.constants import *
from utils.parser import *

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
        metavar='$ESGINI_DIR',
        action=DirectoryChecker,
        default=os.environ['ESGINI_DIR'] if 'ESGINI_DIR' in os.environ.keys() else '/esg/config/esgcet',
        help=INI_HELP)
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
        metavar='NAME',
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
        metavar="'^.*/(files|latest|\.\w*).*$'",
        type=regex_validator,
        default='^.*/(files|latest|\.[\w]*).*$',
        help=IGNORE_DIR_HELP)
    main.add_argument(
        '--include-file',
        metavar="'^.*\.nc$'",
        type=regex_validator,
        action='append',
        help=INCLUDE_FILE_HELP['checkvocab'])
    main.add_argument(
        '--exclude-file',
        metavar="'^\..*$'",
        type=regex_validator,
        action='append',
        help=EXCLUDE_FILE_HELP)
    main.add_argument(
        '--max-processes',
        metavar='4',
        type=processes_validator,
        default=4,
        help=MAX_PROCESSES_HELP)
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
