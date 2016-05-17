#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Manages ESGF DRS on local filesystem.

"""

# Module imports
import os
import sys
import logging
import argparse
from datetime import datetime
from utils import MultilineFormatter, config_parse, init_logging, split_line

# Program version
__version__ = 'v{0} {1}'.format('0.1', datetime(year=2016, month=04, day=28).strftime("%Y-%d-%m"))



def get_args():
    """
    Returns parsed command-line arguments. See ``esgdrs -h`` for full description.

    :returns: The corresponding ``argparse`` Namespace

    """
    __TEMPLATE_HELP__ = """Required path of the issue JSON template."""
    __DSETS_HELP__ = """Required path of the affected dataset IDs list."""
    __HELP__ = """Show this help message and exit."""
    __LOG_HELP__ = """Logfile directory. If not, standard output is used."""
    parser = argparse.ArgumentParser(
        prog='esgdrslite',
        description="""The publication workflow on the ESGF nodes requires to deal with errata issues.
                    The background of the version changes has to be published alongside the data: what was updated,
                    retracted or removed, and why. Consequently, the publication of a new version of a dataset has to
                    be motivated by an issue.|n|n

                    "esgissue" allows the referenced data providers to easily create, document, update, close or remove
                    a validated issue. "esgissue" relies on the GitHub API v3 to deal with private repositories.|n|n

                    The issue registration always appears prior to the publication process and should be mandatory
                    for additional version, version removal or retraction.|n|n

                    "esgissue" works with both JSON and TXT files. This allows the data provider in charge of ESGF
                    issues to manage one or several JSON templates gathering the issues locally.|n|n

                    See full documentation on http://esgissue.readthedocs.org/""",
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog="""Developed by:|n
                  Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.jussieu.fr)|n
                  Bennasser, A. (UPMC/IPSL - abennasser@ipsl.jussieu.fr""")
    parser._optionals.title = "Optional arguments"
    parser._positionals.title = "Positional arguments"
    parser.add_argument(
        '-h', '--help',
        action='help',
        help=__HELP__)
    parser.add_argument(
        '-V',
        action='version',
        version='%(prog)s ({0})'.format(__version__),
        help="""Program version.""")
    subparsers = parser.add_subparsers(
        title='Issue actions',
        dest='command',
        metavar='',
        help='')
    create = subparsers.add_parser(
        'create',
        prog='esgissue create',
        description=""""esgissue create" registers one or several issues on a defined GitHub repository. The data
                    provider submits one or several JSON files gathering all issues information with a list of all
                    affected dataset IDs (see http://esgissue.readthedocs.org/configuration.html to get a template).|n|n

                    This action returns to the corresponding local JSON template:|n
                    - the corresponding issue number,|n
                    - the ESGF issue ID (as UUID),|n
                    - the creation date,|n
                    - the last updated date (same as the creation date).|n|n

                    The issue registration sets:|n
                    - the issue status to "New",|n
                    - the data provider GitHub login as the issue responsible,|n
                    - the issue format using a fixed HTML schema.|n|n

                    SEE http://esgissue.readthedocs.org/usage.html TO FOLLOW ALL REQUIREMENTS TO REGISTER AN ISSUE.|n|n

                    See "esgissue -h" for global help.""",
        formatter_class=MultilineFormatter,
        help="""Creates ESGF issues from a JSON template to the GitHub repository. See |n
             "esgissue create -h" for full help.""",
        add_help=False)
    create._optionals.title = "Arguments"
    create._positionals.title = "Positional arguments"
    create.add_argument(
        '--issue',
        nargs='?',
        required=True,
        metavar='PATH/issue.json',
        type=argparse.FileType('r'),
        help=__TEMPLATE_HELP__)
    create.add_argument(
        '--dsets',
        nargs='?',
        required=True,
        metavar='PATH/dsets.list',
        type=argparse.FileType('r'),
        help=__DSETS_HELP__)
    create.add_argument(
        '-i',
        metavar='/esg/config/esgcet/.',
        type=str,
        default='/esg/config/esgcet/.',
        help="""Initialization/configuration directory containing "esg.ini"|n
                and "esg.<project>.ini" files. If not specified, the usual|n
                datanode directory is used.""")
    create.add_argument(
        '--log',
        metavar='$PWD',
        type=str,
        const=os.getcwd(),
        nargs='?',
        help=__LOG_HELP__)
    create.add_argument(
        '-v',
        action='store_true',
        default=False,
        help="""Verbose mode.""")
    create.add_argument(
        '-h', '--help',
        action='help',
        help=__HELP__)

    update = subparsers.add_parser(
        'update',
        prog='esgissue update',
        description=""""esgissue update" updates one or several issues on a defined GitHub repository. The data
                    provider submits one or several JSON files gathering all issues information with a list of all
                    affected dataset IDs (see http://esgissue.readthedocs.org/configuration.html to get a template).|n|n

                    This action returns the last updated date to the corresponding local JSON template.|n|n

                    SEE http://esgissue.readthedocs.org/usage.html TO FOLLOW ALL REQUIREMENTS TO UPDATE AN ISSUE.|n|n

                    See "esgissue -h" for global help.""",
        formatter_class=MultilineFormatter,
        help="""Updates ESGF issues from a JSON template to the GitHub repository. See |n
             "esgissue -h" for full help.""",
        add_help=False)
    update._optionals.title = "Optional arguments"
    update._positionals.title = "Positional arguments"
    update.add_argument(
        '--issue',
        nargs='?',
        required=True,
        metavar='PATH/issue.json',
        type=argparse.FileType('r'),
        help=__TEMPLATE_HELP__)
    update.add_argument(
        '--dsets',
        nargs='?',
        required=True,
        metavar='PATH/dsets.list',
        type=argparse.FileType('r'),
        help=__DSETS_HELP__)
    update.add_argument(
        '-i',
        metavar='/esg/config/esgcet/.',
        type=str,
        default='/esg/config/esgcet/.',
        help="""Initialization/configuration directory containing "esg.ini"|n
                and "esg.<project>.ini" files. If not specified, the usual|n
                datanode directory is used.""")
    update.add_argument(
        '--log',
        metavar='$PWD',
        type=str,
        const=os.getcwd(),
        nargs='?',
        help=__LOG_HELP__)
    update.add_argument(
        '-v',
        action='store_true',
        default=False,
        help="""Verbose mode.""")
    update.add_argument(
        '-h', '--help',
        action='help',
        help=__HELP__)

    close = subparsers.add_parser(
        'close',
        prog='esgissue close',
        description=""""esgissue close" closes one or several issues on a defined GitHub repository. The data
                    provider submits one or several JSON files gathering all issues information with a list of all
                    affected dataset IDs (see http://esgissue.readthedocs.org/configuration.html to get a template).|n|n

                    This action returns the date of closure to the corresponding local JSON template (as the same of
                    the last updated date).|n|n

                    SEE http://esgissue.readthedocs.org/usage.html TO FOLLOW ALL REQUIREMENTS TO CLOSE AN ISSUE.|n|n

                    See "esgissue -h" for global help.""",
        formatter_class=MultilineFormatter,
        help="""Closes ESGF issues on the GitHub repository. See "esgissue close -h" for full help.""",
        add_help=False)
    close._optionals.title = "Optional arguments"
    close._positionals.title = "Positional arguments"
    close.add_argument(
        '--issue',
        nargs='?',
        required=True,
        metavar='PATH/issue.json',
        type=argparse.FileType('r'),
        help=__TEMPLATE_HELP__)
    close.add_argument(
        '--dsets',
        nargs='?',
        required=True,
        metavar='PATH/dsets.list',
        type=argparse.FileType('r'),
        help=__DSETS_HELP__)
    close.add_argument(
        '-i',
        metavar='/esg/config/esgcet/.',
        type=str,
        default='/esg/config/esgcet/.',
        help="""Initialization/configuration directory containing "esg.ini"|n
                and "esg.<project>.ini" files. If not specified, the usual|n
                datanode directory is used.""")
    close.add_argument(
        '--log',
        metavar='$PWD',
        type=str,
        const=os.getcwd(),
        nargs='?',
        help=__LOG_HELP__)
    close.add_argument(
        '-v',
        action='store_true',
        default=False,
        help="""Verbose mode.""")
    close.add_argument(
        '-h', '--help',
        action='help',
        help=__HELP__)

    retrieve = subparsers.add_parser(
        'retrieve',
        prog='esgissue retrieve',
        description=""""esgissue retrieve" retrieves one or several issues from a defined GitHub repository. The data
                    provider submits one or several issue number he wants to retrieve and optional paths to write
                    them.|n|n

                    This action rebuilds:|n
                    - the corresponding issue template as a JSON file,|n
                    - the attached affected datasets list as a TEXT file.|n|n

                    SEE http://esgissue.readthedocs.org/usage.html TO FOLLOW ALL REQUIREMENTS TO RETRIEVE AN ISSUE.|n|n

                    See "esgissue -h" for global help.""",
        formatter_class=MultilineFormatter,
        help="""Retrieves ESGF issues from the GitHub repository to a JSON template. See |n
             "esgissue retrieve -h" for full help.""",
        add_help=False)
    retrieve._optionals.title = "Optional arguments"
    retrieve._positionals.title = "Positional arguments"
    retrieve.add_argument(
        '--id',
        metavar='ID',
        type=str,
        nargs='+',
        help='One or several issue number(s) or ESGF id(s) to retrieve.|n Default is to retrieve all GitHub issues.')
    retrieve.add_argument(
        '--issue',
        nargs='?',
        metavar='$PWD/issues',
        default='{0}/issues'.format(os.getcwd()),
        type=str,
        help="""Output directory for the retrieved JSON templates.""")
    retrieve.add_argument(
        '--dsets',
        nargs='?',
        metavar='$PWD/dsets',
        default='{0}/dsets'.format(os.getcwd()),
        type=str,
        help="""Output directory for the retrieved lists of affected dataset IDs.""")
    retrieve.add_argument(
        '-i',
        metavar='/esg/config/esgcet/.',
        type=str,
        default='/esg/config/esgcet/.',
        help="""Initialization/configuration directory containing "esg.ini"|n
                and "esg.<project>.ini" files. If not specified, the usual|n
                datanode directory is used.""")
    retrieve.add_argument(
        '--log',
        metavar='$PWD',
        type=str,
        const=os.getcwd(),
        nargs='?',
        help=__LOG_HELP__)
    retrieve.add_argument(
        '-v',
        action='store_true',
        default=False,
        help="""Verbose mode.""")
    retrieve.add_argument(
        '-h', '--help',
        action='help',
        help=__HELP__)
    return parser.parse_args()
