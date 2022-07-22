#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF data for publication.

"""

from argparse import FileType

from esgprep import __version__
from esgprep._utils.help import *
from esgprep._utils.parser import *
from esgprep.drs import run


def get_args():
    """
    Returns parsed command-line arguments.

    """
    # Instantiate argument parser.
    main = CustomArgumentParser(
        prog='esgdrs',
        description=PROGRAM_DESC['drs'],
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog=EPILOG)
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
        dest='cmd',
        metavar='',
        help='')

    # Add parent parser with common arguments.
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        '-h', '--help',
        action='help',
        help=HELP)
    parent.add_argument(
        '-i',
        metavar='$ESGINI_DIR',
        action=ConfigFileLoader,
        default=os.getenv('ESGINI_DIR', '/esg/config/esgcet'),
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
        'action',
        choices=['list', 'tree', 'todo', 'upgrade'],
        default='list',
        help=ACTION_HELP)
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
        '--ignore-dir',
        metavar="'^.*/(files|\.\w*).*$'",
        type=regex_validator,
        default='^.*/(files|\.[\w]*).*$',
        help=IGNORE_DIR_HELP)
    parent.add_argument(
        '--include-file',
        metavar="'^.*\.nc$'",
        type=regex_validator,
        action='append',
        default=['^.*\.nc$'],
        help=INCLUDE_FILE_HELP['mapfile'])
    parent.add_argument(
        '--exclude-file',
        metavar="'^\..*$'",
        type=regex_validator,
        action='append',
        default=['^\..*$'],
        help=EXCLUDE_FILE_HELP)
    group = parent.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--color',
        action='store_true',
        help=COLOR_HELP)
    group.add_argument(
        '--no-color',
        action='store_true',
        help=NO_COLOR_HELP)
    parent.add_argument(
        '--max-processes',
        metavar='4',
        type=processes_validator,
        default=4,
        help=MAX_PROCESSES_HELP)

    # Add subparser.
    make = subparsers.add_parser(
        'make',
        prog='esgdrs make',
        description=DRS_SUBCOMMANDS['make'],
        formatter_class=MultilineFormatter,
        help=DRS_HELPS['make'],
        add_help=False,
        parents=[parent])

    make.add_argument(
        '--root',
        metavar='CWD',
        action=DirectoryChecker,
        default=os.getcwd(),
        help=ROOT_HELP)
    make.add_argument(
        '--version',
        metavar=datetime.now().strftime("%Y%m%d"),
        action=VersionChecker,
        default='v{}'.format(datetime.now().strftime('%Y%m%d')),
        help=SET_VERSION_HELP['drs'])
    make.add_argument(
        '--set-value',
        metavar='FACET_KEY=VALUE',
        type=keyval_converter,
        action='append',
        help=SET_VALUE_HELP)
    make.add_argument(
        '--set-key',
        metavar='FACET_KEY=ATTRIBUTE',
        type=keyval_converter,
        action='append',
        help=SET_KEY_HELP)
    make.add_argument(
        '--rescan',
        action='store_true',
        default=False,
        help=RESCAN_HELP)
    make.add_argument(
        '--commands-file',
        metavar='TXT_FILE',
        type=str,
        help=COMMANDS_FILE_HELP)
    make.add_argument(
        '--overwrite-commands-file',
        action='store_true',
        default=False,
        help=OVERWRITE_COMMANDS_FILE_HELP)
    make.add_argument(
        '--upgrade-from-latest',
        action='store_true',
        default=False,
        help=UPGRADE_FROM_LATEST_HELP)
    make.add_argument(
        '--ignore-from-latest',
        metavar='TXT_FILE',
        type=FileType('r'),
        help=IGNORE_FROM_LATEST_HELP)
    make.add_argument(
        '--ignore-from-incoming',
        metavar='TXT_FILE',
        type=FileType('r'),
        help=IGNORE_FROM_INCOMING_HELP)
    group = make.add_mutually_exclusive_group(required=False)
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
    make.add_argument(
        '--no-checksum',
        action='store_true',
        default=False,
        help=NO_CHECKSUM_HELP['drs'])
    make.add_argument(
        '--checksums-from',
        metavar='CHECKSUM_FILE',
        type=FileType('r'),
        help=CHECKSUMS_FROM_HELP)
    make.add_argument(
        '--quiet',
        action='store_true',
        default=False,
        help=QUIET_HELP)

    # Add subparser.
    remove = subparsers.add_parser(
        'remove',
        prog='esgdrs remove',
        description=DRS_SUBCOMMANDS['remove'],
        formatter_class=MultilineFormatter,
        help=DRS_HELPS['remove'],
        add_help=False,
        parents=[parent])
    remove.add_argument(  # Lolo change temporary add to be able to skip the use of pickle tree
        '--rescan',
        action='store_true',
        default=False,
        help=RESCAN_HELP)
    group = remove.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--directory',
        metavar='PATH',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP['mapfile'])
    group.add_argument(
        '--dataset-list',
        metavar='TXT_FILE',
        type=DatasetsReader,
        nargs='?',
        const=sys.stdin,
        help=DATASET_LIST_HELP)
    group.add_argument(
        '--dataset-id',
        metavar='DATASET_ID',
        action='append',
        help=DATASET_ID_HELP)

    group = remove.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--version',
        metavar=datetime.now().strftime("%Y%m%d"),
        action=VersionChecker,
        help=SET_VERSION_HELP['drs'])
    group.add_argument(
        '--all-versions',
        action='store_true',
        default=False,
        help=ALL_VERSIONS_HELP)

    # Add subparser.
    latest = subparsers.add_parser(
        'latest',
        prog='esgdrs latest',
        description=DRS_SUBCOMMANDS['latest'],
        formatter_class=MultilineFormatter,
        help=DRS_HELPS['make'],
        add_help=False,
        parents=[parent])
    latest.add_argument(
        '--directory',
        action=DirectoryChecker,
        nargs='+',
        help=DIRECTORY_HELP['mapfile'])
    latest.add_argument(
        '--rescan',
        action='store_true',
        default=False,
        help=RESCAN_HELP)
    # Return command-line parser & program name.
    return main.prog, main.parse_args()


def main():
    """
    Run main program

    """
    # Get command-line arguments.
    prog, args = get_args()

    # Set default sub-command.
    args.cmd = 'make' if not args.cmd else args.cmd

    # Add program name as argument.
    setattr(args, 'prog', prog)
    print(args)
    # Run program.
    run(args)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
