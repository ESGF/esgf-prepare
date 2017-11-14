#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Constants used in this package.

"""

from datetime import datetime

# Program version
VERSION = '2.7.25'

# Date
VERSION_DATE = datetime(year=2017, month=11, day=14).strftime("%Y-%d-%m")

# Help
PROGRAM_DESC = \
    """
    The ESGF publication process requires a strong and effective data management. "esgprep" allows data providers
    to easily prepare their data before publishing to an ESGF node. "esgprep" provides python command-lines
    covering several steps of ESGF publication workflow:|n|n
    
    i. Fetch proper configuration files from ESGF GitHub repository,|n|n
    
    ii. Data Reference Syntax management,|n|n
    
    iii. Check DRS vocabulary against configuration files,|n|n
    
    iv. Generate mapfiles.|n|n
    
    See full documentation and references at http://is-enes-data.github.io/esgf-prepare/.
    
    """

EPILOG = \
    """
    Developed by:|n
    Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.fr)|n
    Berger, K. (DKRZ - berger@dkrz.de)|n
    Iwi, A. (STFC/CEDA - alan.iwi@stfc.ac.uk)|n
    Stephens, A. (STFC/CEDA - ag.stephens@stfc.ac.uk)
    
    """

OPTIONAL = \
    """Optional arguments"""

POSITIONAL = \
    """Positional arguments"""

HELP = \
    """
    Show this help message and exit.
    
    """

TEST_HELP = {
    'program':
        """
        Run the full test suite.
        
        """,

    'parent':
        """
        Run the test suite.
        
        """
}

VERSION_HELP = \
    """
    Program version.
    
    """

INI_HELP = \
    """
    Initialization/configuration directory containing|n
    "esg.ini" and "esg.<project>.ini" files.|n
    If not specified, the usual datanode directory|n
    is used.
    
    """

LOG_HELP = \
    """
    Logfile directory.|n
    If not, standard output is used.
    
    """

VERBOSE_HELP = \
    """
    Verbose mode.
    
    """

SUBCOMMANDS = \
    """Subcommands"""

FETCHINI_DESC = \
    """
    The ESGF publishing client and most of other ESGF tool rely on configuration files of different kinds, that 
    are the primary means of configuring the ESGF publisher. The "esg.<project_id>.ini" files declare all facets
    and allowed values according to the Data Reference Syntax (DRS) and the controlled vocabularies of the
    corresponding project. "esgprep fetch-ini" allows you to properly download and deploy those configuration files
    hosted on a GitHub repository. Keep in mind that the fetched files have to be reviewed to ensure a correct
    configuration of your publication. The supplied configuration directory is used to write the files retrieved
    from GitHub.|n|n
    
    The default values are displayed next to the corresponding flags.
    
    """

FETCHINI_HELP = \
    """
    Fetchs INI files from GitHub.|n
    See "esgprep fetch-ini -h" for full help.
    
    """

PROJECT_HELP = {
    'fetch-ini':
        """
        One or more lower-cased project name(s).|n
        If not, all "esg.*.ini" are fetched.
        
        """,

    'check-vocab':
        """
        Required lower-cased project name.
        
        """,

    'drs':
        """
        Required lower-cased project name.
        
        """,

    'mapfile':
        """
        Required lower-cased project name.
        
        """
}

KEEP_HELP = \
    """
    Ignore and keep existing file(s) without prompting.
    
    """

OVERWRITE_HELP = \
    """
    Ignore and overwrite existing file(s) without prompting.
    
    """

BACKUP_HELP = \
    """
    Backup mode of existing files.|n
    "one_version" renames an existing file in its source|n
    directory adding a ".bkp" extension to the filename.|n
    "keep_versions" moves an existing file to a child|n
    directory called "bkp" and add a timestamp to the filename.|n
    If no mode specified, "one_version" is the default.|n
    If not specified, no backup.
    
    """

GITHUB_USER_HELP = \
    """
    GitHub username.
    
    """

GITHUB_PASSWORD_HELP = \
    """
    GitHub password.
    
    """

DEVEL_HELP = \
    """
    Fetch from the devel branch.
    
    """

CHECKVOCAB_DESC = \
    """
    In the case that your data already follows the appropriate directory structure, you may want to check that all 
    values of each facet are correctly declared in the "esg.<project_id>.ini" sections. "esgprep check-vocab" 
    allows you to easily check the configuration file attributes by scanning your data tree. It requires that your 
    directory structure strictly follows the project DRS including the dataset version.|n|n
    
    The default values are displayed next to the corresponding flags.
    
    """

CHECKVOCAB_HELP = \
    """
    Checks configuration file vocabulary.|n
    See "esgprep check-vocab -h" for full help.
    
    """

DIRECTORY_HELP = {
    'check-vocab':
        """
        One or more directories to recursively scan.|n
        Unix wildcards are allowed.
        
        """,

    'drs':
        """
        One or more directories to recursively scan.|n
        Unix wildcards are allowed.
        
        """,

    'mapfile':
        """
        One or more directories to recursively scan.|n
        Unix wildcards are allowed.
        
        """
}

DATASET_LIST_HELP = \
    """
    File containing list of dataset IDs.
    
    """

IGNORE_DIR_HELP = \
    """
    Filter directories NON-matching the regular expression.|n
    Default ignore paths with folder name(s) starting with|n
    "." and/or including "/files/" or "/latest/" patterns.|n
    (Regular expression must match from start of path; prefix|n
    with ".*" if required.)
    
    """

INCLUDE_FILE_HELP = \
    """
    Filter files matching the regular expression.|n
    Duplicate the flag to set several filters.|n
    Default only include NetCDF files.
    
    """

EXCLUDE_FILE_HELP = \
    """
    Filter files NON-matching the regular expression.|n
    Duplicate the flag to set several filters.|n
    Default only exclude files (with names not|n
    starting with ".").

    """

DRS_DESC = \
    """
    The Data Reference Syntax (DRS) defines the way your data have to follow on your filesystem. This allows a
    proper publication on ESGF node. "esgprep drs" command is designed to help ESGF datanode managers to prepare
    incoming data for publication, placing files in the DRS directory structure, and manage multiple versions of
    publication-level datasets to minimise disk usage. Only CMORized netCDF files are supported as incoming
    files.|n|n
    
    The default values are displayed next to the corresponding flags.
    
    """

DRS_HELP = \
    """
    Manages the Data Reference Syntax on your filesystem.|n
    See "esgprep drs -h" for full help.
    
    """

ACTION_HELP = \
    """
    DRS action:|n
    - "list" lists publication-level datasets,|n
    - "tree" displays the final DRS tree,|n
    - "todo" shows file operations pending for the next version,|n
    - "upgrade" makes changes to upgrade datasets to the next version.
    
    """

ROOT_HELP = \
    """
    Root directory to build the DRS.
    
    """

SET_VERSION_HELP = {
    'drs':
        """
        Set the version number for all scanned files.
        
        """,

    'mapfile':
        """
        Generates mapfile(s) scanning datasets with the|n
        corresponding version number only. It takes priority over|n
        --all-versions. If directly specified in positional|n
        argument, use the version number from supplied directory|n
        and disables --all-versions and --latest-symlink.
        
        """
}

SET_VALUE_HELP = \
    """
    Set a facet value.|n
    Duplicate the flag to set several facet values.|n
    This overwrites facet auto-detection.
    
    """

SET_KEY_HELP = \
    """
    Map one a facet key with a NetCDF attribute name.|n
    Duplicate the flag to map several facet keys.|n
    This overwrites facet auto-detection.
    
    """
NO_CHECKSUM_HELP = {
    'drs':
        """
        Does not include files checksums for version comparison.
        
        """,

    'mapfile':
        """
        Does not include files checksums into the mapfile(s).
        
        """
}

COPY_HELP = \
    """
    Copy incoming files into the DRS tree.|n
    Default is moving files.
    
    """

LINK_HELP = \
    """
    Hard link incoming files to the DRS tree.|n
    Default is moving files.
    
    """

SYMLINK_HELP = \
    """
    Symbolic link incoming files to the DRS tree.|n
    Default is moving files.
    
    """

MAX_THREADS_HELP = \
    """
    Number of maximal threads to simultaneously process|n
    several files (useful if checksum calculation is|n
    enabled). Set to one seems sequential processing.
    
    """

MAPFILE_DESC = \
    """
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
    
    """

MAPFILE_HELP = \
    """
    Generates ESGF mapfiles.|n
    See "esgprep mapfile -h" for full help.
    
    """

MAPFILE_NAME_HELP = \
    """
    Specifies template for the output mapfile(s) name.|n
    Substrings {dataset_id}, {version}, {job_id} or {date} |n
    (in YYYYDDMM) will be substituted where found. If |n
    {dataset_id} is not present in mapfile name, then all |n
    datasets will be written to a single mapfile, overriding |n
    the default behavior of producing ONE mapfile PER|n
    dataset.
    
    """

OUTDIR_HELP = \
    """
    Mapfile(s) output directory. A "mapfile_drs" can be|n
    defined per project section in INI files and joined to|n
    build a mapfiles tree.
    
    """

ALL_VERSIONS_HELP = \
    """
    Generates mapfile(s) with all versions found in the|n
    directory recursively scanned (default is to pick up only|n
    the latest one).|n
    It disables --no-version.
    
    """

LATEST_SYMLINK_HELP = \
    """
    Generates mapfile(s) following latest symlinks only. This|n
    sets the {version} token to "latest" into the mapfile|n
    name, but picked up the pointed version to build the|n
    dataset identifier (if --no-version is disabled).
    
    """

NO_VERSION_HELP = \
    """
    Does not includes DRS version into the dataset|n
    identifier.
    
    """

NOT_IGNORED_HELP = \
    """
    One or more facet key(s) to not ignored. This excludes|n
    the corresponding facet from the default ignored list.|n
    Useful in case of differences between|n
    "directory_format" and "dataset_id" patterns.
    
    """

TECH_NOTES_URL_HELP = \
    """
    URL of the technical notes to be associated with each|n
    dataset.
    
    """

TECH_NOTES_TITLE_HELP = \
    """
    Technical notes title for display.
    
    """

DATASET_HELP = \
    """
    String name of the dataset. If specified, all files will|n
    belong to the specified dataset, regardless of the DRS.
    
    """

NO_CLEANUP_HELP = \
    """
    Disables output directory cleanup prior to mapfile|n
    process. This is recommended if several "esgprep mapfile"|n
    instances run with the same output directory.
    
    """
