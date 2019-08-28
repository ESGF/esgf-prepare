# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.help.py
   :platform: Unix
   :synopsis: Command-line help.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from esgprep._utils.print import *

# Help
TITLE = COLOR('yellow').bold(""".___ ___ ___ ___ ___ ___ ___.
| -_|_ -| . | . | __| -_| . |
|___|___|__ | __|_| |___| __|
________|___|_|_________|_|__""")

INTRO = """The ESGF publication process requires a strong and effective data management. "esgprep" allows data providers to easily prepare their data before publishing to an ESGF node. "esgprep" provides python command-lines covering several steps of ESGF publication workflow."""

URL = COLOR('gray').italic("""See full documentation and references at http://esgf.github.io/esgf-prepare/""")

DEFAULT = COLOR('white').italic("""The default values are displayed next to the corresponding flags.""")

PROGRAM_DESC = {
    'fetchini': """
{}

{} Most of other ESGF tool rely on configuration files of different kinds. The "esg.<project_id>.ini" files  declare all the facets and allowed values according to the Data Reference Syntax (DRS) and the controlled vocabularies of the corresponding project. "esgfetchini" allows you to properly download and deploy those configuration files hosted on an official GitHub repository. Keep in mind that the fetched files have to be reviewed to ensure a correct configuration of your side.

{}

{}""".format(TITLE, INTRO, URL, DEFAULT),
    'fetchcv': """
{}

{} "esgprep" relies on the "pyessv" library to deal with Controlled Vocabularies. "esgfetchcv" allows you to properly download the "pyessv-archive" required to follow the Data Reference Syntax of the corresponding project. The "pyessv-archive" is composed by a set of manisfests and JSON files hosted on an official GitHub repository.

{}

{}""".format(TITLE, INTRO, URL, DEFAULT),
    'fetchtables': """
{}

{} Some of ESGF quality control tools rely on tables describing the variables, their coordinates and attributes. Those tables are produced to standardize data for ESGF through the Climate Model Output Rewriter (CMOR). The CMOR tables are available for different projects. "esgfetchtables" allows you to properly download those tables hosted on an official GitHub repository. Keep in mind that the fetched files have to be reviewed to ensure a correct configuration of your side.

{}

{}""".format(TITLE, INTRO, URL, DEFAULT),
    'drs': """
{}

{} The Data Reference Syntax (DRS) defines the way the data of a given project have to follow on your filesystem. This allows a proper publication on the ESGF. "esgdrs" has been designed to help ESGF datanode managers to prepare incoming data for publication, placing files in the DRS directory structure, and manage multiple versions of publication-level datasets to minimise disk usage. Only MIP-compliant netCDF files are supported as incoming files.

{}

{}""".format(TITLE, INTRO, URL, DEFAULT),
    'checkvocab': """
{}

{} In the case that your data already follows the appropriate directory structure, you may want to check that all values of each facet are correctly declared in the "esg.<project_id>.ini" sections. "esgcheckvocab" allows you to easily check the configuration file attributes by scanning your data tree or give (a list of) dataset identifiers. It requires that your directory structure or dataset format strictly follows the project Data Reference Syntax (DRS) including the dataset version.

{}

{}""".format(TITLE, INTRO, URL, DEFAULT),
    'mapfile': """
{}

{} The publication process of the ESGF nodes requires mapfiles. Mapfiles are text files where each line describes a file to publish. It's highly recommended to use mapfile as inputs for ESGF publication. "esgmapfile" allows you to easily generate and manage your ESGF mapfiles. It requires that your directory structure strictly follows the project Data Reference Syntax (DRS) including the dataset version.

{}

{}""".format(TITLE, INTRO, URL, DEFAULT)
}

EPILOG = COLOR('gray').italic("""Developed by:
    Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.fr)
    Berger, K.      (DKRZ      - berger@dkrz.de)
    Iwi, A.         (STFC/CEDA - alan.iwi@stfc.ac.uk)
    Stephens, A.    (STFC/CEDA - ag.stephens@stfc.ac.uk)""")

OPTIONAL = COLOR('blue')("""Optional arguments""")

POSITIONAL = COLOR('magenta')("""Positional arguments""")

HELP = """Show this help message and exit.

"""

VERSION_HELP = """Program version.

"""

INI_HELP = """Initialization/configuration directory containing "esg.ini" and "esg.<project>.ini" files.
Default is to use "$ESGINI_DIR" environment variable.
If not set, the usual ESGF datanode directory is used (i.e., "/esg/config/esgcet/").

"""

CV_HELP = """Initialization directory containing the "pyessv" archive.
Default is to use "$PYESSV_ARCHIVE_HOME" environment variable.
If not set, the usual "pyessv" home directory is used (i.e., "$HOME/.esdoc/pyessv-archive/").


"""

LOG_HELP = """Logfile directory.
If not, standard output is used.
Special case, with '--log -', messages are written to standard output as they would appear in a log file, and the usual output to standard output is suppressed.

"""

VERBOSE_HELP = """Debug mode. It disables progress bars and print verbose process infos.

"""

SUBCOMMANDS = COLOR('red')("""Subcommands""")

PROJECT_HELP = {
    'fetchini': """One or more lower-cased project name(s).
If not, all "esg.*.ini" are fetched.

""",
    'fetchcv': """One or more lower-cased project name(s).
If not, all projects within an authority are fetched.

""",
    'fetchtables': """One or more lower-cased project name(s).
If not, all "*-cmor-tables" contents are fetched.

""",
    'checkvocab': """Required lower-cased project name.
    
""",
    'drs': """Required lower-cased project name.
    
""",
    'mapfile': """Required lower-cased project name.

"""
}

AUTHORITY_HELP = """One or more lower-cased authority name(s).
If not, all CV authorities are fetched.

"""

KEEP_HELP = """Ignore and keep existing file(s) without prompting.

"""

OVERWRITE_HELP = """Ignore and overwrite existing file(s) without prompting.

"""

BACKUP_HELP = """Backup mode of existing files.
"one_version" renames an existing file in its source directory adding a ".bkp" extension to the filename.
"keep_versions" moves an existing file to a child directory called "bkp/" and add a timestamp to the filename.
If no mode specified, "one_version" is the default.
If no flag, no backup.

"""

GITHUB_USER_HELP = """GitHub username.
Default is the "$GH_USER" environment variable if exists.

"""

GITHUB_PASSWORD_HELP = """GitHub password.
Default is the "$GH_PASSWORD" environment variable if exists.
If the username is set, but the password is not provided as a command line option nor as an environment variable, then it is prompted for interactively.

"""

DEVEL_HELP = """Fetch from the devel branch.

"""

BRANCH_HELP = """Fetch from a GitHub branch.
Default is to fetch from "master" branch.

"""

BRANCH_REGEX_HELP = """Fetch from all GitHub branches matching the specified regex.

"""

TAG_HELP = """Fetch from a GitHub tag.

"""

TAG_REGEX_HELP = """Fetch from all GitHub tags matching the specified regex.

"""

DIRECTORY_HELP = {
    'checkvocab': """One or more directories to recursively scan. Unix wildcards are allowed.
    
""",

    'drs': """One or more directories to recursively scan. Unix wildcards are allowed.
    
""",

    'mapfile': """One or more directories to recursively scan. Unix wildcards are allowed.
    
"""
}

DATASET_LIST_HELP = """File containing list of dataset IDs.
If not, the standard input is used.

"""

IGNORE_DIR_HELP = """Filter directories NON-matching the regular expression.
Default ignore paths with folder name(s) starting with "." and/or including "/files/" or "/latest/" patterns (regular expression must match from start of path; prefix with ".*" if required).

"""

INCLUDE_FILE_HELP = {
    'fetchtables': """Filter files matching the regular expression.
Duplicate the flag to set several filters.
Default includes all regular files.

""",
    'checkvocab': """Filter files matching the regular expression.
Duplicate the flag to set several filters.
Default includes all netCDF files.
    
""",
    'mapfile': """Filter files matching the regular expression.
Duplicate the flag to set several filters.
Default includes all netCDF files.

"""
}

EXCLUDE_FILE_HELP = """Filter files NON-matching the regular expression.
Duplicate the flag to set several filters.
Default excludes all hidden files.

"""

DRS_SUBCOMMANDS = {
    'make': """
{}

The Data Reference Syntax (DRS) defines the way your data have to follow on your filesystem. This allows a proper publication on ESGF node. "esgdrs make" subcommand allows you to generate the appropriate directory structure from incoming netCDF files following several modes of migration.

{}

{}

""".format(TITLE, URL, DEFAULT),
    'remove': """
{}

The Data Reference Syntax (DRS) defines the way your data have to follow on your filesystem. This allows a proper publication on ESGF node. "esgdrs remove" subcommand allows you to remove one or several dataset versions from you local directory structure preserving the symlink skeleton of remaining versions.

{}

{}

""".format(TITLE, URL, DEFAULT),
    'latest': """
{}

The Data Reference Syntax (DRS) defines the way your data have to follow on your filesystem. This allows a proper publication on ESGF node. "esgdrs latest" subcommand allows you to generate create the "latest" symlink on a generated directory structure, if they do not already exist.

{}

{}

""".format(TITLE, URL, DEFAULT)
}

DRS_HELPS = {
    'make': """Generates DRS tree (default).
See "esgdrs make -h" for full help.
""",
    'remove': """Removes dataset versions safely.
See "esgdrs remove -h" for full help.
""",
    'latest': """Creates "latest" symbolic link at the version level.
See "esgdrs latest -h" for full help.
"""
}

ACTION_HELP = """- "list": Lists publication-level datasets (default).
- "tree": Displays the final DRS tree.
- "todo": Shows file operations pending for the next version.
- "upgrade": Makes changes to upgrade datasets to the next version.
"""

ROOT_HELP = """Root directory to build the DRS.

"""

SET_VERSION_HELP = {
    'drs': """Set the version number for all scanned files.

""",

    'mapfile':
        """Generates mapfile(s) scanning datasets with the corresponding version number only. It takes priority over "--all-versions".
If directly specified in positional argument, use the version number from supplied directory and disables "--all-versions" and "--latest-symlink".

"""
}

SET_VALUE_HELP = """Set a facet value.
Duplicate the flag to set several facet values.
This overwrites facet auto-detection.

"""

SET_KEY_HELP = """Map one a facet key with a netCDF attribute name.
Duplicate the flag to map several facet keys.
This overwrites facet auto-detection.

"""

NO_CHECKSUM_HELP = {
    'mapfile': """Does not include files checksums into the mapfile(s).
    
""",
    'drs': """Disable checksumming during DRS process.
    
"""
}

COMMANDS_FILE_HELP = """Writes Unix command-line statements only in the submitted file.
Default is the standard output (requires "todo" action).

"""

OVERWRITE_COMMANDS_FILE_HELP = """Allow overwriting of existing file specified by "--commands-file".

"""

UPGRADE_FROM_LATEST_HELP = """The upgraded version of the dataset is based primarily on the previous (latest) version.
Default is to consider the incoming files as the complete content of the new version of the dataset.
See the full documentation to get details on this method.

"""

IGNORE_FROM_LATEST_HELP = """A list of filename to ignore for version upgrade from the latest dataset version.
Default is to consider the incoming files as the complete content of the new version of the dataset.
It overwrites default behavior by enabling "--upgrade-from-latest". 
See the full documentation to get details on this method.

"""

IGNORE_FROM_INCOMING_HELP = """A list of filename to ignore for version upgrade from the incoming files.
Default is to consider the incoming files as the complete content of the new version of the dataset.
It allows to filter incoming files to consider.

"""

RESCAN_HELP = """Force incoming files rescan.
Default is to scan incoming files with "list" action, or if no cached scan results exist, or if the changed arguments between two runs do not require to rescan the incoming files.

"""

COPY_HELP = """Copy incoming files into the DRS tree. 
Default is moving files.

"""

LINK_HELP = """Hard link incoming files to the DRS tree.
Default is moving files.

"""

SYMLINK_HELP = """Symbolic link incoming files to the DRS tree.
Default is moving files.

"""

MOVE_HELP = """Move incoming files to the DRS tree (default)."""

MAX_PROCESSES_HELP = """Number of maximal processes to simultaneously treat several files (useful if checksum calculation is enabled).
Set to "1" seems sequential processing.
Set to "-1" seems all available resources as returned by "multiprocessing.cpu_count()".

"""

MAPFILE_SUBCOMMANDS = {
    'make': """
{}

The publication process of the ESGF nodes requires mapfiles. Mapfiles are text files where each line describes a file to publish on the following format:

dataset_ID | absolute_path | size_bytes [ | option=value ]

1. All values have to be pipe-separated.
2. The dataset identifier, the absolute path and the size (in bytes) are required.
3. Adding the version number to the dataset identifier is strongly recommended to publish in a in bulk.
4. Strongly recommended optional values are:
    - mod_time: last modification date of the file (since Unix EPOCH time, i.e., seconds since January, 1st, 1970),
    - checksum: file checksum,
    - checksum_type: checksum type (MD5 or the default SHA256).
5. Your directory structure has to strictly follows the tree fixed by the DRS including the version facet.
6. To store ONE mapfile PER dataset is strongly recommended.

{}

{}

""".format(TITLE, URL, DEFAULT),
    'show': """
{}

The publication process of the ESGF nodes requires mapfiles. Mapfiles are text files where each line describes a file to publish. The mapfile name can depend on several facets or tokens, as part of its path. Displaying expected mapfile full path and name to be generated could facilitate mapfile management and ESGF publication procedures.

{}

{}

""".format(TITLE, URL, DEFAULT)
}

MAPFILE_HELPS = {
    'make': """Generates ESGF mapfiles (default).|n
See "esgmapfile make -h" for full help.

""",
    'show': """Display expected mapfile path.|n
See "esgmapfile show -h" for full help.

"""
}

MAPFILE_NAME_HELP = """Specifies template for the output mapfile(s) name.
Substrings {dataset_id}, {version}, {job_id} or {date} (in YYYYDDMM) will be substituted where found.
If {dataset_id} is not present in mapfile name, then all datasets will be written to a single mapfile, overriding the default behavior of producing ONE mapfile PER dataset.

"""

OUTDIR_HELP = """Mapfile(s) output directory.
A "mapfile_drs" can be defined per project section in INI files and joined to build a mapfiles tree.

"""

TABLES_DIR_HELP = """Top CMOR tables output directory containing "<PROJECT>-cmor-tables" folder(s).
Default is the CMOR_TABLES environment variable.
If not exists, the usual datanode directory is used (i.e., /usr/local/).

"""

NO_SUBFOLDER_HELP = """Disable table sub-folder depending on the GitHub Reference (i.e., a tag or branch).
Default is to build output directory as: "<TABLES_DIR>/<PROJECT>-cmor-table/<GH_REF>
    
"""

CHECKSUMS_FROM_HELP = """Get the checksums from an submitted file.
This checksum file must have the same format as the output of the UNIX command-lines "*sum".
In the case of unfound checksums, it falls back to compute the checksum as normal.

"""

ALL_VERSIONS_HELP = """Generates mapfile(s) with all versions found in the directory recursively scanned (default is to pick up only the latest one).
It disables "--no-version".

"""

LATEST_SYMLINK_HELP = """Generates mapfile(s) following latest symlinks only.
This sets the {version} token to "latest" into the mapfile name, but picked up the pointed version to build the dataset identifier (if "--no-version" is disabled).

"""

TECH_NOTES_URL_HELP = """URL of the technical notes to be associated with each dataset.

"""

TECH_NOTES_TITLE_HELP = """Technical notes title for display.

"""

NO_CLEANUP_HELP = """Disables output directory cleanup prior to mapfile process. This is recommended if several "esgmapfile" instances run with the same output directory.

"""

DATASET_ID_HELP = """The dataset identifier dot-separated with or without the ending version.
Duplicate the flag to submit several dataset identifiers.

"""

QUIET_HELP = """Display only results without any other information.

"""

BASENAME_HELP = """Display result basename only (i.e., mapfile name without root directory).
Default prints the full mapfile path.

"""

COLOR_HELP = """Enable colors. (Default is to enable when writing to a terminal.)

"""

NO_COLOR_HELP = """Disable colors.

"""
