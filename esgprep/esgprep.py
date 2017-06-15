#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Toolbox to prepare ESGF date for publication.

"""

import argparse
import os
import sys
import unittest
from datetime import datetime
from importlib import import_module

from utils.utils import MultilineFormatter, DirectoryChecker, VersionChecker
from utils.utils import init_logging, keyval_converter

# Program version
__version__ = 'v{0} {1}'.format('2.7.5', datetime(year=2017, month=6, day=15).strftime("%Y-%d-%m"))


def get_args():
    """
    Returns parsed command-line arguments. See ``esgprep -h`` for full description.

    :returns: The corresponding ``argparse`` Namespace
    :rtype: *argparse.Namespace*

    """
    # Workaround to run ``esgprep [subcommand] --test`` without subparsers and required flags
    if len(sys.argv[1:]) == 1 and sys.argv[1:][-1] == '--test':
        return argparse.Namespace(**{'cmd': None, 'test': True, 'log': None, 'v': False})
    if len(sys.argv[1:]) == 2 and sys.argv[1:][-1] == '--test':
        return argparse.Namespace(**{'cmd': sys.argv[1:][-2], 'test': True, 'log': None, 'v': False})

    #############################
    # Main parser for "esgprep" #
    #############################
    main = argparse.ArgumentParser(
        prog='esgprep',
        description="""
        The ESGF publication process requires a strong and effective data management. "esgprep" allows data providers
        to easily prepare their data before publishing to an ESGF node. "esgprep" provides python command-lines
        covering several steps of ESGF publication workflow:|n|n
        
        i. Fetch proper configuration files from ESGF GitHub repository,|n|n

        ii. Data Reference Syntax management,|n|n

        iii. Check DRS vocabulary against configuration files,|n|n

        iv. Generate mapfiles.|n|n

        See full documentation and references at http://is-enes-data.github.io/esgf-prepare/.
        """,
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog="""
        Developed by:|n
        Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.fr)|n
        Berger, K. (DKRZ - berger@dkrz.de)|n
        Iwi, A. (STFC/CEDA - alan.iwi@stfc.ac.uk)|n
        Stephens, A. (STFC/CEDA - ag.stephens@stfc.ac.uk)
        """)
    main._optionals.title = "Optional arguments"
    main._positionals.title = "Positional arguments"
    main.add_argument(
        '-h', '--help',
        action='help',
        help="""Show this help message and exit.""")
    main.add_argument(
        '--test',
        action='store_true',
        default=False,
        help="""Run the full test suite.""")
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
        '-h', '--help',
        action='help',
        help="""Show this help message and exit.""")

    parent.add_argument(
        '-i',
        metavar='/esg/config/esgcet',
        action=DirectoryChecker,
        default='/esg/config/esgcet',
        help="""
        Initialization/configuration directory containing|n
        "esg.ini" and "esg.<project>.ini" files.|n
        If not specified, the usual datanode directory|n
        is used.
        """)
    parent.add_argument(
        '--log',
        metavar='CWD',
        type=str,
        const='{0}/logs'.format(os.getcwd()),
        nargs='?',
        help="""
        Logfile directory.|n
        If not, standard output is used.
        """)
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
        The ESGF publishing client and most of other ESGF tool rely on configuration files of different kinds, that 
        are the primary means of configuring the ESGF publisher. The "esg.<project_id>.ini" files declare all facets
        and allowed values according to the Data Reference Syntax (DRS) and the controlled vocabularies of the
        corresponding project. "esgprep fetch-ini" allows you to properly download and deploy those configuration files
        hosted on a GitHub repository. Keep in mind that the fetched files have to be reviewed to ensure a correct
        configuration of your publication. The supplied configuration directory is used to write the files retrieved
        from GitHub.|n|n

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
        metavar='PROJECT_ID',
        type=str,
        nargs='+',
        help="""
        One or more lower-cased project name(s).|n
        If not, all "esg.*.ini" are fetched.
        """)
    group = fetchini.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '-k',
        action='store_true',
        default=False,
        help="""Ignore and keep existing file(s) without prompting.""")
    group.add_argument(
        '-o',
        action='store_true',
        default=False,
        help="""Ignore and overwrite existing file(s) without prompting.""")
    fetchini.add_argument(
        '-b',
        metavar='one_version',
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
        metavar='USERNAME',
        type=str,
        help="""GitHub username.""")
    fetchini.add_argument(
        '--gh-password',
        metavar='PASSWORD',
        type=str,
        help="""GitHub password.""")

    #######################################
    # Subparser for "esgprep check-vocab" #
    #######################################
    checkvocab = subparsers.add_parser(
        'check-vocab',
        prog='esgprep check-vocab',
        description="""
        In the case that your data already follows the appropriate directory structure, you may want to check that all 
        values of each facet are correctly declared in the "esg.<project_id>.ini" sections. "esgprep check-vocab" 
        allows you to easily check the configuration file attributes by scanning your data tree. It requires that your 
        directory structure strictly follows the project DRS including the dataset version.|n|n

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
    group = checkvocab.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--directory',
        metavar='PATH',
        action=DirectoryChecker,
        nargs='+',
        help="""
        One or more directories to recursively scan.|n
        Unix wildcards are allowed.
        """)
    group.add_argument(
        '--dataset-list',
        metavar='TXT_FILE',
        type=str,
        help="""File containing list of dataset IDs.""")
    checkvocab.add_argument(
        '--project',
        metavar='PROJECT_ID',
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
        support netCDF files). Regular expression syntax is defined|n
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
        publication-level datasets to minimise disk usage. Only CMORized netCDF files are supported as incoming
        files.|n|n

        The default values are displayed next to the corresponding flags.
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
        'action',
        choices=['list', 'tree', 'todo', 'upgrade'],
        metavar='action',
        type=str,
        help="""
        DRS action:|n
        - "list" lists publication-level datasets,|n
        - "tree" displays the final DRS tree,|n
        - "todo" shows file operations pending for the next version,|n
        - "upgrade" makes changes to upgrade datasets to the next version.
        """)
    drs.add_argument(
        'directory',
        action=DirectoryChecker,
        nargs='+',
        help="""
        One or more directories to recursively scan.|n
        Unix wildcards are allowed.""")
    drs.add_argument(
        '--project',
        metavar='PROJECT_ID',
        type=str,
        required=True,
        help="""Required lower-cased project name.""")
    drs.add_argument(
        '--root',
        metavar='CWD',
        action=DirectoryChecker,
        default=os.getcwd(),
        help="""Root directory to build the DRS.""")
    drs.add_argument(
        '--version',
        metavar=datetime.now().strftime("%Y%m%d"),
        action=VersionChecker,
        default=datetime.now().strftime('%Y%m%d'),
        help="""Set the version number for all scanned files.""")
    drs.add_argument(
        '--set-value',
        metavar='FACET_KEY=VALUE',
        type=keyval_converter,
        action='append',
        help="""
        Set a facet value.|n
        Duplicate the flag to set several facet values.|n
        This overwrites facet auto-detection.
        """)
    drs.add_argument(
        '--set-key',
        metavar='FACET_KEY=ATTRIBUTE',
        type=keyval_converter,
        action='append',
        help="""
        Map one a facet key with a NetCDF attribute name.|n
        Duplicate the flag to map several facet keys.|n
        This overwrites facet auto-detection.
        """)
    drs.add_argument(
        '--no-checksum',
        action='store_true',
        default=False,
        help="""Does not include files checksums for version comparison.""")
    group = drs.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--copy',
        action='store_true',
        default=False,
        help="""
        Copy incoming files into the DRS tree.|n
        Default is moving files.
        """)
    group.add_argument(
        '--link',
        action='store_true',
        default=False,
        help="""
        Hard link incoming files to the DRS tree.|n
        Default is moving files.
        """)
    group.add_argument(
        '--symlink',
        action = 'store_true',
        default = False,
        help = """
        Symbolic link incoming files to the DRS tree.|n
        Default is moving files.
        """)
    drs.add_argument(
        '--filter',
        metavar='"*.nc"',
        type=str,
        default='*.nc',
        help="""
        Filter files matching the regular expression (default only|n
        support netCDF files). Unix wildcards are supported.
        """)
    drs.add_argument(
        '--max-threads',
        metavar=4,
        type=int,
        default=4,
        help="""
        Number of maximal threads to simultaneously process several|n
        files (useful if checksum calculation is enabled). Set to|n
        one seems sequential processing.
        """)

    ###################################
    # Subparser for "esgprep mapfile" #
    ###################################
    mapfile = subparsers.add_parser(
        'mapfile',
        prog='esgprep mapfile',
        description="""
        The publication process of the ESGF nodes requires mapfiles. Mapfiles are text files where each line describes
        a file to publish on the following format:|n|n

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

        "esgprep mapfile" allows you to easily generate ESGF mapfiles upon local ESGF datanode or not.|n|n

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
        action=DirectoryChecker,
        nargs='+',
        help="""
        One or more directories to recursively scan.|n
        Unix wildcards are allowed.
        """)
    mapfile.add_argument(
        '--project',
        metavar='PROJECT_ID',
        type=str,
        required=True,
        help="""Required lower-cased project name.""")
    mapfile.add_argument(
        '--mapfile',
        metavar='{dataset_id}.{version}.map',
        type=str,
        default='{dataset_id}.{version}.map',
        help="""
        Specifies template for the output mapfile(s) name.|n
        Substrings {dataset_id}, {version}, {job_id} or {date} |n
        (in YYYYDDMM) will be substituted where found. If |n
        {dataset_id} is not present in mapfile name, then all |n
        datasets will be written to a single mapfile, overriding |n
        the default behavior of producing ONE mapfile PER|n
        dataset.
        """)
    mapfile.add_argument(
        '--outdir',
        metavar='CWD/mapfiles',
        type=str,
        default=os.path.join(os.getcwd(), 'mapfiles'),
        help="""
        Mapfile(s) output directory. A "mapfile_drs" can be|n
        defined per project section in INI files and joined to|n
        build a mapfiles tree.
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
        metavar=datetime.now().strftime("%Y%m%d"),
        type=VersionChecker,
        help="""
        Generates mapfile(s) scanning datasets with the|n
        corresponding version number only. It takes priority over|n
        --all-versions. If directly specified in positional|n
        argument, use the version number from supplied directory|n
        and disables --all-versions and --latest-symlink.
        """)
    group.add_argument(
        '--latest-symlink',
        action='store_true',
        default=False,
        help="""
        Generates mapfile(s) following latest symlinks only. This|n
        sets the {version} token to "latest" into the mapfile|n
        name, but picked up the pointed version to build the|n
        dataset identifier (if --no-version is disabled).
        """)
    mapfile.add_argument(
        '--no-version',
        action='store_true',
        default=False,
        help="""
        Does not includes DRS version into the dataset|n
        identifier.
        """)
    mapfile.add_argument(
        '--no-checksum',
        action='store_true',
        default=False,
        help="""Does not include files checksums into the mapfile(s).""")
    mapfile.add_argument(
        '--not-ignored',
        metavar='FACET_KEY',
        type=str,
        nargs='+',
        default=[],
        help="""
        One or more facet key(s) to not ignored. This excludes|n
        the corresponding facet from the default ignored list.|n
        Useful in case of differences between|n
        "directory_format" and "dataset_id" patterns.
        """)
    mapfile.add_argument(
        '--filter',
        metavar='"*.nc"',
        type=str,
        default='*.nc',
        help="""
        Filter files matching the regular expression (default|n
        only scan netCDF files). Uniw wildcards are supported.
        """)
    mapfile.add_argument(
        '--tech-notes-url',
        metavar='URL',
        type=str,
        help="""
        URL of the technical notes to be associated with each|n
        dataset.
        """)
    mapfile.add_argument(
        '--tech-notes-title',
        metavar='TITLE',
        type=str,
        help="""Technical notes title for display.""")
    mapfile.add_argument(
        '--dataset',
        metavar='DATASET_ID',
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
        Number of maximal threads to simultaneously process|n
        several files (useful if checksum calculation is|n
        enabled). Set to one seems sequential processing.
        """)
    mapfile.add_argument(
        '--no-cleanup',
        action='store_true',
        default=False,
        help="""Disables output directory cleanup prior to mapfile|n
        process. This is recommended if several "esgprep mapfile"|n
        instances run with the same output directory.
        """)

    return main.parse_args()


def run():
    """
    Run main program

    """
    # Get command-line arguments
    args = get_args()
    # Initialize logger
    init_logging(log=args.log, verbose=args.v)
    # Print progress bar
    setattr(args, 'pbar', True if not args.log and not args.v else False)
    # Run subcommand
    if args.test and not args.cmd:
        print('"esgprep" test suite is not available. Coming soon!')
        exit()
        testsuite = unittest.TestLoader().discover('.')
        unittest.TextTestRunner().run(testsuite)
    else:
        submodule = args.cmd.lower().replace('-', '')
        if args.test:
            test = import_module('.test', package='esgprep.{0}'.format(submodule))
            test.run()
        else:
            main = import_module('.main', package='esgprep.{0}'.format(submodule))
            main.main(args)


# Main entry point for stand-alone call.
if __name__ == "__main__":
    run()
