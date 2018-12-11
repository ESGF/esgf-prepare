#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF data for publication.

"""

from argparse import FileType

from esgprep.drs.main import run
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
        prog='esgdrs',
        description=PROGRAM_DESC['drs'],
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
        metavar='$ESGINI_DIR',
        action=DirectoryChecker,
        default=os.environ['ESGINI_DIR'] if 'ESGINI_DIR' in os.environ.keys() else '/esg/config/esgcet',
        help=INI_HELP)
    parent.add_argument(
        '-l', '--log',
        metavar='CWD',
        type=str,
        const='{}/logs'.format(os.getcwd()),
        nargs='?',
        help=LOG_HELP)
    parent.add_argument(
        '-d', '--debug',
        action='store_true',
        default=False,
        help=VERBOSE_HELP)
    parent.add_argument(
        'directory',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP['drs'])
    parent.add_argument(
        '-p', '--project',
        metavar='NAME',
        type=str,
        required=True,
        help=PROJECT_HELP['drs'])
    parent.add_argument(
        '--root',
        metavar='CWD',
        action=DirectoryChecker,
        default=os.getcwd(),
        help=ROOT_HELP)
    parent.add_argument(
        '--version',
        metavar=datetime.now().strftime("%Y%m%d"),
        action=VersionChecker,
        default=datetime.now().strftime('%Y%m%d'),
        help=SET_VERSION_HELP['drs'])
    parent.add_argument(
        '--set-value',
        metavar='FACET_KEY=VALUE',
        type=keyval_converter,
        action='append',
        help=SET_VALUE_HELP)
    parent.add_argument(
        '--set-key',
        metavar='FACET_KEY=ATTRIBUTE',
        type=keyval_converter,
        action='append',
        help=SET_KEY_HELP)
    parent.add_argument(
        '--rescan',
        action='store_true',
        default=False,
        help=RESCAN_HELP)
    parent.add_argument(
        '--commands-file',
        metavar='TXT_FILE',
        type=str,
        help=COMMANDS_FILE_HELP)
    parent.add_argument(
        '--overwrite-commands-file',
        action='store_true',
        default=False,
        help=OVERWRITE_COMMANDS_FILE_HELP)
    parent.add_argument(
        '--upgrade-from-latest',
        action='store_true',
        default=False,
        help=UPGRADE_FROM_LATEST_HELP)
    parent.add_argument(
        '--ignore-from-latest',
        metavar='TXT_FILE',
        type=FileType('r'),
        help=IGNORE_FROM_LATEST_HELP)
    parent.add_argument(
        '--ignore-from-incoming',
        metavar='TXT_FILE',
        type=FileType('r'),
        help=IGNORE_FROM_INCOMING_HELP)
    group = parent.add_mutually_exclusive_group(required=False)
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
    parent.add_argument(
        '--no-checksum',
        action='store_true',
        default=False,
        help=NO_CHECKSUM_HELP['drs'])
    parent.add_argument(
        '--max-processes',
        metavar='4',
        type=processes_validator,
        default=4,
        help=MAX_PROCESSES_HELP)
    group = parent.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--color',
        action='store_true',
        help=COLOR_HELP)
    group.add_argument(
        '--no-color',
        action='store_true',
        help=NO_COLOR_HELP)
    # Subparser for "esgdrs list"
    list = subparsers.add_parser(
        'list',
        prog='esgdrs list',
        description=DRS_SUBCOMMANDS['list'],
        formatter_class=MultilineFormatter,
        help=DRS_HELPS['list'],
        add_help=False,
        parents=[parent])
    list._optionals.title = OPTIONAL
    list._positionals.title = POSITIONAL
    # Subparser for "esgdrs tree"
    tree = subparsers.add_parser(
        'tree',
        prog='esgdrs tree',
        description=DRS_SUBCOMMANDS['tree'],
        formatter_class=MultilineFormatter,
        help=DRS_HELPS['tree'],
        add_help=False,
        parents=[parent])
    tree._optionals.title = OPTIONAL
    tree._positionals.title = POSITIONAL
    # Subparser for "esgdrs todo"
    todo = subparsers.add_parser(
        'todo',
        prog='esgdrs todo',
        description=DRS_SUBCOMMANDS['todo'],
        formatter_class=MultilineFormatter,
        help=DRS_HELPS['todo'],
        add_help=False,
        parents=[parent])
    todo._optionals.title = OPTIONAL
    todo._positionals.title = POSITIONAL
    # Subparser for "esgdrs upgrade"
    upgrade = subparsers.add_parser(
        'upgrade',
        prog='esgdrs upgrade',
        description=DRS_SUBCOMMANDS['upgrade'],
        formatter_class=MultilineFormatter,
        help=DRS_HELPS['upgrade'],
        add_help=False,
        parents=[parent])
    upgrade._optionals.title = OPTIONAL
    upgrade._positionals.title = POSITIONAL
    main.set_default_subparser('list')
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
