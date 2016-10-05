#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. module:: esgprep
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF date for publication.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.jussieu.fr>

"""

import argparse
import os
from datetime import datetime

from utils.utils import MultilineFormatter, init_logging, version_checker, directory_checker

# Program version
__version__ = 'v{0} {1}'.format('2.5.9', datetime(year=2016, month=10, day=3).strftime("%Y-%d-%m"))


def get_args():
    """
    Returns parsed command-line arguments. See ``esgprep -h`` for full description.

    :returns: The corresponding ``argparse`` Namespace
    :rtype: *ArgumentParser*

    """
    #############################
    # Main parser for "esgprep" #
    #############################
    main = argparse.ArgumentParser(
        prog='esgprep',
        description="""
        The ESGF publication process requires a strong and effective data management. "esgprep" allows data providers to
        easily prepare their data before publishing to an ESGF node.|n|n

        "esgprep" gathers python command-lines covering several steps of ESGF publication workflow:|n
        i. Fetch proper configuration files from ESGF GitHub repository,|n
        ii. Data Reference Syntax management,|n
        iii. Check DRS vocable against configuration files,|n
        iv. Generate mapfiles.|n|n

        The "esgprep" toolbox is based on the ESGF datanode configuration files called "esg.ini". It implies those
        configuration files are correctly build and declares all required attributes following recommended best
        practices.|n|n

        See full documentation and references on http://is-enes-data.github.io/esgf-prepare/.
        """,
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog="""
        Developed by:|n
        Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.jussieu.fr)|n
        Berger, K. (DKRZ - berger@dkrz.de)|n
        Iwi, A. (STFC/BADC - alan.iwi@stfc.ac.uk)|n
        Stephens, A. (STFC/BADC - ag.stephens@stfc.ac.uk)
        """)
    main._optionals.title = "Optional arguments"
    main._positionals.title = "Positional arguments"
    main.add_argument(
        '-h', '--help',
        action='help',
        help="""Show this help message and exit.""")
    main.add_argument(
        '-V',
        action='version',
        version='%(prog)s ({0})'.format(__version__),
        help="""Program version.""")
    subparsers = main.add_subparsers(
        title='Tools as subcommands',
        dest='cmd',
        metavar='',
        help='')

    #######################################
    # Parent parser with common arguments #
    #######################################
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        '-i',
        metavar='/esg/config/esgcet/.',
        type=directory_checker,
        default='/esg/config/esgcet/.',
        help="""
        Initialization/configuration directory containing|n
        "esg.ini" and "esg.<project>.ini" files.|n
        If not specified, the usual datanode directory is used.
        """)
    parent.add_argument(
        '--log',
        metavar='$PWD',
        type=str,
        const=os.getcwd(),
        nargs='?',
        help="""Logfile directory. If not, standard output is used.""")
    parent.add_argument(
        '-h', '--help',
        action='help',
        help="""Show this help message and exit.""")
    parent.add_argument(
        '-v',
        action='store_true',
        default=False,
        help="""Verbose mode.""")

    #####################################
    # Subparser for "esgprep fetch-ini" #
    #####################################
    fetchini = subparsers.add_parser(
        'fetch-ini',
        prog='esgprep fetch-ini',
        description="""
        The ESGF publishing client and most of other ESGF tool rely on configuration files of different kinds, that are
        the primary means of configuring the ESGF publisher.|n|n

        - The "esg.ini" file gathers all required information to configure the datanode regarding to data publication
        (e.g., PostgreSQL access, THREDDS configuration, etc.).|n
        - The "esg.<project_id>.ini" files declare all facets and allowed values according to the Data Reference Syntax
        (DRS) and the controlled vocabularies of the corresponding project.|n
        - The "esgcet_models_table.txt" declares the models and their descriptions among the projects.|n
        - The "<project_id>_handler.py" are Python methods to guide the publisher in metadata harvesting.

        "esgprep fetch-ini" allows you to properly download, configure and deploy these configuration files hosted
        on a GitHub repository.|n|n

        Keep in mind that the fetched files have to be reviewed to ensure a correct configuration of your
        publication.|n|n

        The supply configuration directory is used to write the files retrieved from GitHub.|n|n

        The default values are displayed next to the corresponding flags.
        """,
        formatter_class=MultilineFormatter,
        help="""
        Fetch INI files from GitHub.|n
        See "esgprep fetch-ini -h" for full help.
        """,
        add_help=False,
        parents=[parent])
    fetchini._optionals.title = "Optional arguments"
    fetchini._positionals.title = "Positional arguments"
    fetchini.add_argument(
        '--project',
        metavar='<project>',
        type=str,
        nargs='+',
        help="""
        One or more lower-cased project name(s).|n
        If not, all "esg.*.ini" are fetched.
        """)
    fetchini.add_argument(
        '--db-password',
        metavar='<password>',
        type=str,
        help="""
        Database password.|n
        Required to configure "esg.ini".
        """)
    fetchini.add_argument(
        '--db-host',
        metavar='localhost',
        type=str,
        default='localhost',
        help="""Database hostname.""")
    fetchini.add_argument(
        '--db-port',
        metavar='5432',
        type=str,
        default='5432',
        help="""Database port.""")
    fetchini.add_argument(
        '--tds-password',
        metavar='<password>',
        type=str,
        help="""
        THREDDS password.|n
        Required to configure "esg.ini".
        """)
    fetchini.add_argument(
        '--data-root-path',
        metavar='<path>',
        type=str,
        help="""
        Path of a file table in which each line follows the|n
        syntax "<project_id> | <data_root_path>".|n
        Required to configure "esg.ini".
        """)
    fetchini.add_argument(
        '--esgf-index-peer',
        metavar='<hostname>',
        type=str,
        help="""Index peer hostname.""")
    fetchini.add_argument(
        '--esgf-host',
        metavar='<hostname>',
        type=str,
        help="""Datanode hostname.""")
    fetchini.add_argument(
        '--esg-root-id',
        metavar='<institute>',
        type=str,
        help="""Institute root id.""")
    group = fetchini.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '-k',
        action='store_true',
        default=False,
        help="""Ignore and keep existing file(s) without prompt.""")
    group.add_argument(
        '-o',
        action='store_true',
        default=False,
        help="""Ignore and overwrite existing file(s) without prompt.""")
    fetchini.add_argument(
        '-b',
        choices=['one_version', 'keep_versions'],
        type=str,
        nargs='?',
        const='one_version',
        help="""
        Backup mode of existing files.|n
        "one_version" renames an existing file in its source|n
        directory adding a ".bkp" extension to the filename.|n
        "keep_versions" moves an existing file to a child|n
        directory called "bkp" and add a timestamp to the filename.|n
        If no mode specified, "one_version" is the default.|n
        If not specified, no backup.
        """)
    fetchini.add_argument(
        '--gh-user',
        metavar='<username>',
        type=str,
        help="""GitHub username.""")
    fetchini.add_argument(
        '--gh-password',
        metavar='<password>',
        type=str,
        help="""GitHub password.""")

    #######################################
    # Subparser for "esgprep check-vocab" #
    #######################################
    checkvocab = subparsers.add_parser(
        'check-vocab',
        prog='esgprep check-vocab',
        description="""
        The data management/preparation" relies on the ESGF node configuration files. These "esg.<project>.ini" files
        declares the Data Reference Syntax (DRS) and the controlled vocabularies of each project.|n|n

        In the case of your data already follow the appropriate directory structure, you may want to check that all
        values of each facet are correctly declared into "esg.<project_id>.ini" sections.|n|n

        "esgprep check-vocab" allows you to easily check the configuration file attributes by scanning your data tree.
        It implies that your directory structure strictly follows the project DRS including the version facet.|n|n

        The default values are displayed next to the corresponding flags.
        """,
        formatter_class=MultilineFormatter,
        help="""
        Checks configuration file vocabulary.|n
        See "esgprep check-vocab -h" for full help.
        """,
        add_help=False,
        parents=[parent])
    checkvocab._optionals.title = "Optional arguments"
    checkvocab._positionals.title = "Positional arguments"
    checkvocab.add_argument(
        'directory',
        type=directory_checker,
        nargs='+',
        help="""
        One or more directories to recursively scan.|n
        Unix wildcards are allowed.""")
    checkvocab.add_argument(
        '--project',
        metavar='<project_id>',
        type=str,
        required=True,
        help="""Required lower-cased project name.""")
    checkvocab.add_argument(
        '--filter',
        metavar=r'".*\.nc$"',
        type=str,
        default=r'.*\.nc$',
        help="""
        Filter files matching the regular expression (default only|n
        support NetCDF files). Regular expression syntax is defined|n
        by the Python "re" module.
        """)

    ###############################
    # Subparser for "esgprep drs" #
    ###############################
    drs = subparsers.add_parser(
        'drs',
        prog='esgprep drs',
        description="""
        The Data Reference Syntax (DRS) defines the way your data have to follow on your filesystem. This allows a
        proper publication on ESGF node. "esgprep drs" command is designed to help ESGF datanode managers to prepare
        incoming data for publication, placing files in the DRS directory structure, and manage multiple versions of
        publication-level datasets to minimise disk usage.|n|n

        This feature is coming soon !
        """,
        formatter_class=MultilineFormatter,
        help="""
        Manages the Data Reference Syntax on your filesystem.|n
        See "esgprep drs -h" for full help.
        """,
        add_help=False,
        parents=[parent])
    drs._optionals.title = "Optional arguments"
    drs._positionals.title = "Positional arguments"
    drs.add_argument(
        'incoming',
        type=directory_checker,
        nargs='+',
        help="""
        One or more directories to recursively scan.|n
        Unix wildcards are allowed.""")
    drs.add_argument(
        '--project',
        metavar='<project_id>',
        type=str,
        required=True,
        help="""Required lower-cased project name.""")
    drs.add_argument(
        '--outdir',
        metavar='$PWD',
        type=directory_checker,
        default=os.getcwd(),
        help="""Output directory to build the DRS.""")

    ###################################
    # Subparser for "esgprep mapfile" #
    ###################################
    mapfile = subparsers.add_parser(
        'mapfile',
        prog='esgprep mapfile',
        description="""
        The publication process of the ESGF nodes requires mapfiles. Mapfiles are text files where each line describes a
        file to publish on the following format:|n|n

        dataset_ID | absolute_path | size_bytes [ | option=value ]|n|n

        1. All values have to be pipe-separated.|n
        2. The dataset identifier, the absolute path and the size (in bytes) are required.|n
        3. Adding the version number to the dataset identifier is strongly recommended to publish in a in bulk.|n
        4. Strongly recommended optional values are:|n
         - mod_time: last modification date of the file (since Unix EPOCH time, i.e., seconds since January, 1st,
         1970),|n
         - checksum: file checksum,|n
         - checksum_type: checksum type (MD5 or the default SHA256).|n
        5. Your directory structure has to strictly follows the tree fixed by the DRS including the version facet.|n
        6. To store ONE mapfile PER dataset is strongly recommended.|n|n

        "esgprep mapfile" allows you to easily generate ESGF mapfiles upon local ESGF datanode or not. It implies that
        your directory structure strictly follows the project DRS including the version facet.|n|n

        Exit status:|n
        [0]: Successful scanning of all files encountered,|n
        [1]: No valid data or files have been found and no mapfile was produced,|n
        [2]: A mapfile was produced but some files were skipped.|n|n

        The default values are displayed next to the corresponding flags.
        """,
        formatter_class=MultilineFormatter,
        help="""
        Generates ESGF mapfiles.|n
        See "esgprep mapfile -h" for full help.
        """,
        add_help=False,
        parents=[parent])
    mapfile._optionals.title = "Optional arguments"
    mapfile._positionals.title = "Positional arguments"
    mapfile.add_argument(
        'directory',
        type=directory_checker,
        nargs='+',
        help="""
        One or more directories to recursively scan.|n
        Unix wildcards are allowed.
        """)
    mapfile.add_argument(
        '--project',
        metavar='<project_id>',
        type=str,
        required=True,
        help="""Required lower-cased project name.""")
    mapfile.add_argument(
        '--mapfile',
        metavar='{dataset_id}.{version}.map',
        type=str,
        default='{dataset_id}.{version}',
        help="""
        Specifies template for the output mapfile(s) name.|n
        Substrings {dataset_id}, {version}, {job_id} or {date} |n
        (in YYYYDDMM) will be substituted where found. If |n
        {dataset_id} is not present in mapfile name, then all |n
        datasets will be written to a single mapfile, overriding |n
        the default behavior of producing ONE mapfile PER dataset.
        """)
    mapfile.add_argument(
        '--outdir',
        metavar='$PWD',
        type=str,
        default=os.getcwd(),
        help="""
        Mapfile(s) output directory. A "mapfile_drs" can be defined |n
        per each project section in INI files and joined to build a |n
        mapfiles tree.
        """)
    group = mapfile.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--all-versions',
        action='store_true',
        default=False,
        help="""
        Generates mapfile(s) with all versions found in the|n
        directory recursively scanned (default is to pick up only|n
        the latest one).|n
        It disables --no-version.
        """)
    group.add_argument(
        '--version',
        metavar=datetime.now().strftime("%Y%d%m"),
        type=version_checker,
        help="""
        Generates mapfile(s) scanning datasets with the|n
        corresponding version number only. It takes priority over|n
        --all-versions. If directly specified in positional|n
        argument, use the version number from supplied directory and|n
        disables --all-versions and --latest-symlink.
        """)
    group.add_argument(
        '--latest-symlink',
        action='store_true',
        default=False,
        help="""
        Generates mapfile(s) following latest symlinks only. This|n
        sets the {version} token to "latest" into the mapfile name,|n
        but picked up the pointed version to build the dataset|n
        identifier (if --no-version is disabled).
        """)
    mapfile.add_argument(
        '--no-version',
        action='store_true',
        default=False,
        help="""Does not includes DRS version into the dataset identifier.""")
    mapfile.add_argument(
        '--no-checksum',
        action='store_true',
        default=False,
        help="""Does not include files checksums into the mapfile(s).""")
    mapfile.add_argument(
        '--filter',
        metavar=r'".*\.nc$"',
        type=str,
        default=r'.*\.nc$',
        help="""
        Filter files matching the regular expression (default only|n
        support NetCDF files). Regular expression syntax is defined|n
        by the Python "re" module.
        """)
    mapfile.add_argument(
        '--tech-notes-url',
        metavar='<url>',
        type=str,
        help="""
        URL of the technical notes to be associated with each|n
        dataset.
        """)
    mapfile.add_argument(
        '--tech-notes-title',
        metavar='<title>',
        type=str,
        help="""Technical notes title for display.""")
    mapfile.add_argument(
        '--dataset',
        metavar='<dataset_id>',
        type=str,
        help="""
        String name of the dataset. If specified, all files will|n
        belong to the specified dataset, regardless of the DRS.
        """)
    mapfile.add_argument(
        '--max-threads',
        metavar=4,
        type=int,
        default=4,
        help="""
        Number of maximal threads to simultaneously process several|n
        files (useful if checksum calculation is enabled). Set to|n
        one seems sequential processing.
        """)

    return main.parse_args()


def run():
    # Get command-line arguments
    args = get_args()

    # Initialize logger
    if args.v:
        init_logging(args.log, level='DEBUG')
    else:
        init_logging(args.log)

    # Run subcommand
    if args.cmd == 'fetch-ini':
        from fetchini import main
        main.main(args)
    elif args.cmd == 'check-vocab':
        from checkvocab import main
        main.main(args)
    elif args.cmd == 'drs':
        from drs import main
        main.main(args)
    elif args.cmd == 'mapfile':
        from mapfile import main
        main.main(args)


# Main entry point for stand-alone call.
if __name__ == "__main__":
    run()
