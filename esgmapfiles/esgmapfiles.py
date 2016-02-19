#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Generates ESGF mapfiles upon an local ESGF node or not.

"""

import sys
import os
import re
import argparse
import logging
from esgmapfilesutils import init_logging, check_directory, config_parse, MultilineFormatter
from esgmapfilesutils import translate_directory_format, split_line, split_map
from multiprocessing.dummy import Pool as ThreadPool
from functools import wraps
from lockfile import LockFile, LockTimeout, LockFailed
from tempfile import mkdtemp
from datetime import datetime
from shutil import copy2, rmtree

# Program version
__version__ = 'v{0} {1}'.format('1.1.2', datetime(year=2016, month=02, day=19).strftime("%Y-%d-%m"))

# Lockfile timeout (in sec)
__LOCK_TIMEOUT__ = 30


class ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +------------------------+-------------+----------------------------------------------+
    | Attribute              | Type        | Description                                  |
    +========================+=============+==============================================+
    | *self*.directory       | *list*      | Paths to scan                                |
    +------------------------+-------------+----------------------------------------------+
    | *self*.outmap          | *str*       | Mapfile name/pattern using tokens            |
    +------------------------+-------------+----------------------------------------------+
    | *self*.latest          | *boolean*   | True to follow latest symlink                |
    +------------------------+-------------+----------------------------------------------+
    | *self*.outdir          | *str*       | Output directory                             |
    +------------------------+-------------+----------------------------------------------+
    | *self*.notes_url       | *str*       | Dataset technical notes URL                  |
    +------------------------+-------------+----------------------------------------------+
    | *self*.notes_title     | *str*       | Dataset technical notes title                |
    +------------------------+-------------+----------------------------------------------+
    | *self*.verbose         | *boolean*   | True if verbose mode                         |
    +------------------------+-------------+----------------------------------------------+
    | *self*.all             | *boolean*   | True to scan all versions                    |
    +------------------------+-------------+----------------------------------------------+
    | *self*.version         | *str*       | Version to scan                              |
    +------------------------+-------------+----------------------------------------------+
    | *self*.filter          | *re object* | File filter as regex pattern                 |
    +------------------------+-------------+----------------------------------------------+
    | *self*.no_version      | *boolean*   | True to not include version in dataset ID    |
    +------------------------+-------------+----------------------------------------------+
    | *self*.project         | *str*       | Project                                      |
    +------------------------+-------------+----------------------------------------------+
    | *self*.project_section | *str*       | Project section name in configuration file   |
    +------------------------+-------------+----------------------------------------------+
    | *self*.dataset         | *str*       | Dataset ID name                              |
    +------------------------+-------------+----------------------------------------------+
    | *self*.checksum_client | *str*       | Checksum client as shell command-line to use |
    +------------------------+-------------+----------------------------------------------+
    | *self*.checksum_type   | *str*       | Checksum type                                |
    +------------------------+-------------+----------------------------------------------+
    | *self*.threads         | *int*       | Maximum threads number                       |
    +------------------------+-------------+----------------------------------------------+
    | *self*.cfg             | *callable*  | Configuration file parser                    |
    +------------------------+-------------+----------------------------------------------+
    | *self*.pattern         | *re object* | DRS regex pattern                            |
    +------------------------+-------------+----------------------------------------------+
    | *self*.dtemp           | *str*       | Directory of temporary files                 |
    +------------------------+-------------+----------------------------------------------+
    | *self*.facets          | *list*      | List of the DRS facets                       |
    +------------------------+-------------+----------------------------------------------+

    :param dict args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *dict*
    :raises Error: If no section name corresponds to the project name in the configuration file

    """
    def __init__(self, args):
        """
        Returns the processing context as a dictionary.

        :param dict args: Parsed command-line arguments
        :returns: The processing context
        :rtype: *dict*
        """
        init_logging(args.log)
        for path in args.directory:
            check_directory(path)
        self.directory = args.directory
        self.outmap = args.mapfile
        self.verbose = args.v
        self.latest = args.latest_symlink
        self.outdir = args.outdir
        self.notes_title = args.tech_notes_title
        self.notes_url = args.tech_notes_url
        self.no_version = args.no_version
        self.threads = args.max_threads
        self.dataset = args.dataset
        self.all = args.all_versions
        if self.all:
            self.no_version = False
        self.version = args.version
        if self.version:
            try:
                datetime.strptime(self.version, '%Y%m%d')
            except:
                raise Exception('Invalid version {0}. Available format is YYYYMMDD.'.format(self.version))
        self.filter = args.filter
        self.project = args.project
        self.project_section = 'project:{0}'.format(args.project)
        self.cfg = config_parse(args.i, args.project, self.project_section)
        if not self.cfg.has_section(self.project_section):
            raise Exception('No section in configuration file corresponds to "{0}". '
                            'Available sections are {1}.'.format(self.project_section,
                                                                 self.cfg.sections()))
        if args.no_checksum:
            self.checksum_client, self.checksum_type = None, None
        elif self.cfg.has_option('default', 'checksum'):
            self.checksum_client, self.checksum_type = split_line(self.cfg.get('default',
                                                                               'checksum'))
        else:  # Use SHA256 as default
            self.checksum_client, self.checksum_type = 'sha256sum', 'SHA256'
        self.facets = set(re.findall(re.compile(r'%\(([^()]*)\)s'),
                                     self.cfg.get(self.project_section,
                                                  'dataset_id',
                                                  raw=True)))
        self.pattern = translate_directory_format(self.cfg.get(self.project_section,
                                                               'directory_format',
                                                               raw=True))
        self.dtemp = mkdtemp()


def get_args(job):
    """
    Returns parsed command-line arguments. See ``esgscan_directory -h`` for full description.
    A ``job`` dictionary can be used as developer's entry point to overload the parser.

    :param dict job: Optional dictionary instead of command-line arguments
    :returns: The corresponding ``argparse`` Namespace

    """
    parser = argparse.ArgumentParser(
        prog='esgscan_directory',
        description="""The publication process of the ESGF nodes requires mapfiles. Mapfiles are
                    text files where each line describes a file to publish on the following
                    format:|n|n

                    dataset_ID | absolute_path | size_bytes [ | option=value ]|n|n

                    1. All values have to be pipe-separated,|n
                    2. The dataset identifier, the absolute path and the size (in bytes) are
                    required,|n
                    3. Adding the file checksum and the checksum type as optional values is
                    strongly recommended,|n
                    4. Adding the version number to the dataset identifier is useful to publish in
                    a in bulk.|n|n

                    "esgscan_directory" allows you to easily generate ESGF mapfiles upon local ESGF
                    datanode or not. It implies that your directory structure strictly follows the
                    project DRS including the version facet.|n|n

                    Exit status:|n
                    [0]: Successful scanning of all files encountered,|n
                    [1]: No valid data or files have been found and no mapfile was produced,|n
                    [2]: A mapfile was produced but some files were skipped.|n|n

                    See full documentation on http://esgscan.readthedocs.org/|n|n

                    The default values are displayed next to the corresponding flags.""",
        formatter_class=MultilineFormatter,
        add_help=False,
        epilog="""Developed by:|n
                  Levavasseur, G. (UPMC/IPSL - glipsl@ipsl.jussieu.fr)|n
                  Berger, K. (DKRZ - berger@dkrz.de)|n
                  Iwi, A. (STFC/BADC - alan.iwi@stfc.ac.uk)""")
    parser._optionals.title = "Optional arguments"
    parser._positionals.title = "Positional arguments"
    parser.add_argument(
        'directory',
        type=str,
        nargs='+',
        help="""One or more directories to recursively scan. Unix wildcards|n
                are allowed.""")
    parser.add_argument(
        '--project',
        metavar='<project_id>',
        type=str,
        required=True,
        help="""Required lower-cased project name.""")
    parser.add_argument(
        '-i',
        metavar='/esg/config/esgcet/.',
        type=str,
        default='/esg/config/esgcet/.',
        help="""Initialization/configuration directory containing "esg.ini"|n
                and "esg.<project>.ini" files. If not specified, the usual|n
                datanode directory is used.""")
    parser.add_argument(
        '--mapfile',
        metavar='{dataset_id}.{version}.map',
        type=str,
        default='{dataset_id}.{version}',
        help="""Specifies template for the output mapfile(s) name.|n
                Substrings {dataset_id}, {version}, {job_id} or {date} |n
                (in YYYYDDMM) will be substituted where found. If |n
                {dataset_id} is not present in mapfile name, then all |n
                datasets will be written to a single mapfile, overriding |n
                the default behavior of producing ONE mapfile PER dataset.""")
    parser.add_argument(
        '--outdir',
        metavar='$PWD',
        type=str,
        default=os.getcwd(),
        help="""Mapfile(s) output directory.""")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--all-versions',
        action='store_true',
        default=False,
        help="""Generates mapfile(s) with all versions found in the|n
                directory recursively scanned (default is to pick up only|n
                the latest one). It disables --no-version.""")
    group.add_argument(
        '--version',
        metavar=datetime.now().strftime("%Y%d%m"),
        type=str,
        help="""Generates mapfile(s) scanning datasets with the|n
                corresponding version number only. It takes priority over|n
                --all-versions. If directly specified in positional|n
                argument, use the version number from supplied directory.""")
    group.add_argument(
        '--latest-symlink',
        action='store_true',
        default=False,
        help="""Generates mapfile(s) following latest symlinks only. This|n
                sets the {version} token to "latest" into the mapfile name,|n
                but picked up the pointed version to build the dataset|n
                identifier (if --no-version is disabled).""")
    parser.add_argument(
        '--no-version',
        action='store_true',
        default=False,
        help="""Includes DRS version into the dataset identifier.""")
    parser.add_argument(
        '--no-checksum',
        action='store_true',
        default=False,
        help="""Does not include files checksums into the mapfile(s).""")
    parser.add_argument(
        '--filter',
        metavar=r'".*\.nc$"',
        type=str,
        default=r'.*\.nc$',
        help="""Filter files matching the regular expression (default only|n
                support NetCDF files). Regular expression syntax is defined|n
                by the Python re module.""")
    parser.add_argument(
        '--tech-notes-url',
        metavar='<url>',
        type=str,
        help="""URL of the technical notes to be associated with each|n
                dataset.""")
    parser.add_argument(
        '--tech-notes-title',
        metavar='<title>',
        type=str,
        help="""Technical notes title for display.""")
    parser.add_argument(
        '--dataset',
        metavar='<dataset_id>',
        type=str,
        help="""String name of the dataset. If specified, all files will|n
                belong to the specified dataset, regardless of the DRS.""")
    parser.add_argument(
        '--max-threads',
        metavar=4,
        type=int,
        default=4,
        help="""Number of maximal threads for checksum calculation.""")
    parser.add_argument(
        '--log',
        metavar='$PWD',
        type=str,
        const=os.getcwd(),
        nargs='?',
        help="""Logfile directory. If not, standard output is used.""")
    parser.add_argument(
        '-h', '--help',
        action='help',
        help="""Show this help message and exit.""")
    parser.add_argument(
        '-v',
        action='store_true',
        default=False,
        help="""Verbose mode.""")
    parser.add_argument(
        '-V',
        action='version',
        version='%(prog)s ({0})'.format(__version__),
        help="""Program version.""")
    if job is None:
        return parser.parse_args()
    else:
        # SYNDA submits dataset path
        directory = os.path.dirname(os.path.normpath(job['args']['variable_path']))
        project = job['args']['project']
        model = job['args']['model']
        outdir = '/prodigfs/esgf/mapfiles/{0}/pending/{1}/'.format(project, model)
        return parser.parse_args([directory,
                                  '--project', project.lower(),
                                  '--mapfile', '{dataset_id}.latest.map',
                                  '--no-version',
                                  '--max-threads', 4,
                                  '--outdir', outdir,
                                  '--log', 'synda_logger',
                                  '--latest-symlink',
                                  '-v'])


def get_dataset_id(ctx, ffp):
    """
    Builds the dataset identifier. The DRS attributes are deduced from the file full path using
    the directory_format regex pattern. The project facet is added in any case with lower case. If
    the version facet cannot be deduced from full path (e.g., with --latest-symlink flag), it
    follows the symlink to complete the DRS attributes. If the dataset name is not specified
    (i.e., --dataset flag is None), it:

     * Checks each facet value regarding the corresponding option list in the esg_<project>.ini,
     * Gets missing attributes from the corresponding maptable in the esg_<project>.ini,
     * Builds the dataset identifier from the attributes,

    :param str ffp: The file full path
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The dataset ID and the dataset version as a tuple
    :rtype: *tuple*
    :raises Error: If the file full path does not match the ``directory_format`` pattern/regex

    """
    # Matching file full path with corresponding project pattern to get DRS attributes values
    # attributes.keys() are facet names
    # attributes[facet] is the facet value.
    try:
        attributes = re.match(ctx.pattern, ffp).groupdict()
        attributes['project'] = ctx.project.lower()
        # If file path is a symlink, deduce the version following the symlink
        if ctx.latest:
            pointed_path = os.path.realpath(''.join(re.split(r'(latest)', ffp)[:-1]))
            attributes['version'] = os.path.basename(pointed_path)
    except:
        msg = 'Matching failed to deduce DRS attributes from {0}. Please check the '\
              '"directory_format" regex in the [project:{1}] section.'.format(ffp, ctx.project)
        logging.warning(msg)
        raise Exception(msg)
    # Check each facet required by the dataset_id template from esg.<project>.ini
    # Facet values to check are deduced from file full-path
    # If a DRS attribute is missing regarding the dataset_id template,
    # the DRS attributes are completed from esg.<project>.ini maptables.
    if not ctx.dataset:
        for facet in ctx.facets.intersection(attributes.keys()):
            # Check attribute value from facet_option list in esg.<project>.ini
            check_facet(facet, attributes, ctx)
        for facet in ctx.facets.difference(attributes.keys()):
            # Get attribute from esg_<project>.ini maptables
            # All other facets have been checked before
            attributes = get_facet_from_map(facet, attributes, ctx)
        dataset_id = ctx.cfg.get(ctx.project_section, 'dataset_id', 0, attributes)
    else:
        dataset_id = ctx.dataset
    if 'version' in attributes and not ctx.no_version:
        return dataset_id, attributes['version']
    else:
        return dataset_id, None


def check_facet(facet, attributes, ctx):
    """
    Checks attribute from path. Each attribute or facet is auto-detected using the DRS pattern
    (regex) and compared to its corresponding options declared into the configuration file, if
    exists.

    :param str facet: The facet name to check with options list
    :param dict attributes: The attributes values auto-detected with DRS pattern
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :raises Error: If the options list is missiong
    :raises Error: If the attribute value is missing in the corresponding options list
    :raises Error: If the ensemble facet has a wrong syntax

    """
    if facet not in ['project', 'filename', 'variable', 'version']:
        if ctx.cfg.has_option(ctx.project_section, '{0}_options'.format(facet)):
            if facet == 'experiment':
                experiment_option_lines = split_line(ctx.cfg.get(ctx.project_section,
                                                     '{0}_options'.format(facet)),
                                                     sep='\n')
                if len(experiment_option_lines) > 1:
                    try:

                        options = [exp_option[1] for exp_option in map(lambda x: split_line(x),
                                                                       experiment_option_lines[1:])]
                    except:
                        msg = '"{0}_options" is misconfigured. Please follow the format '\
                            '"project | experiment | description"'.format(facet)
                        logging.warning(msg)
                        raise Exception(msg)
                else:
                    options = split_line(ctx.cfg.get(ctx.project_section,
                                                     '{0}_options'.format(facet)),
                                         sep=',')
            else:
                options = split_line(ctx.cfg.get(ctx.project_section,
                                                 '{0}_options'.format(facet)),
                                     sep=',')
            if attributes[facet] not in options:
                msg = '"{0}" is missing in "{1}_options" of the section "{2}" from '\
                      'esg.{3}.ini'.format(attributes[facet],
                                           facet,
                                           ctx.project_section,
                                           ctx.project)
                logging.warning(msg)
                raise Exception(msg)
        elif facet == 'ensemble':
            if not re.compile(r'r[\d]+i[\d]+p[\d]+').search(attributes[facet]):
                msg = 'Wrong syntax for "ensemble" facet. '\
                      'Please follow the regex "r[0-9]*i[0-9]*p[0-9]*".'
                logging.warning(msg)
                raise Exception(msg)
        else:
            msg = '"{0}_options" is missing in section "{1}" '\
                  'from esg.{2}.ini'.format(facet,
                                            ctx.project_section,
                                            ctx.project)
            logging.warning(msg)
            raise Exception(msg)


def get_facet_from_map(facet, attributes, ctx):
    """
    Get attribute value from the corresponding maptable in ``esg_<project>.ini`` and add
    to attributes dictionary.

    :param str facet: The facet name to get from maptable
    :param dict attributes: The attributes values auto-detected with DRS pattern
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The updated attributes
    :rtype: *dict*
    :raises Error: If the maptable is missing
    :raises Error: If the maptable is miss-declared
    :raises Error: If the ensemble facet has a wrong syntax

    """
    map_option = '{0}_map'.format(facet)
    if ctx.cfg.has_option(ctx.project_section, map_option):
        from_keys, to_keys, value_map = split_map(ctx.cfg.get(ctx.project_section, map_option))
        if facet not in to_keys:
            msg = '{0}_map is miss-declared in esg.{1}.ini. '\
                  '"{0}" facet has to be in "destination facet"'.format(facet,
                                                                        ctx.project)
            logging.warning(msg)
            raise Exception(msg)
        from_values = tuple(attributes[key] for key in from_keys)
        to_values = value_map[from_values]
        attributes[facet] = to_values[to_keys.index(facet)]
    elif facet == 'ensemble':
        if not re.compile(r'r[\d]+i[\d]+p[\d]+').search(attributes[facet]):
            msg = 'Wrong syntax for "ensemble" facet. '\
                  'Please follow the regex "r[0-9]*i[0-9]*p[0-9]*".'
            logging.warning(msg)
            raise Exception(msg)
    else:
        msg = '{0}_map is required in esg.{1}.ini'.format(facet, ctx.project)
        logging.warning(msg)
        raise Exception(msg)
    return attributes


def checksum(ffp, checksum_type, checksum_client):
    """
    Does the checksum by the Shell avoiding Python memory limits.

    :param str ffp: The file full path
    :param str checksum_client: Shell command line for checksum
    :param str checksum_type: Checksum type
    :returns: The checksum
    :rtype: *str*
    :raises Error: If the checksum fails

    """
    try:
        shell = os.popen("{0} {1} | awk -F ' ' '{{ print $1 }}'".format(checksum_client, ffp), 'r')
        return shell.readline()[:-1]
    except:
        msg = '{0} checksum failed for {1}'.format(checksum_type, ffp)
        logging.warning(msg)
        raise Exception(msg)


def rmdtemp(ctx):
    """
    Removes the temporary directory and its content.

    :param esgmapfiles.ProcessingContext ctx: The processing context (as a :func:`esgmapfiles.ProcessingContext` class instance)

    """
    if ctx.verbose:
        logging.warning('Delete temporary directory {0}'.format(ctx.dtemp))
    rmtree(ctx.dtemp)


def yield_inputs(ctx):
    """
    Yields all files to process within tuples with the processing context. The file walking
    through the DRS tree follows the latest version of each dataset. This behavior is modifed
    using:

     * ``--all-versions`` flag, to pick up all versions,
     * ``--version <version_number>`` argument, to pick up a specified version,
     * ``--latest-symlink`` flag, to pick up the version pointed by the latest symlink (if exists).

    If the supplied directory to scan specifies the version into its path, only this version is
    picked up as with ``--version`` argument.

    :param esgmapfiles.ProcessingContext ctx: The processing context (as a :func:`esgmapfiles.ProcessingContext` class instance)
    :returns: Attach the processing context to a file to process as an iterator of tuples
    :rtype: *iter*

    """
    for directory in ctx.directory:
        # Set --version flag if version number is included in the supplied directory path
        # to recursively scan
        if re.compile(r'/v[0-9]{8}').search(directory):
            ctx.version = re.compile(r'/v[0-9]{8}').search(directory).group()[2:-1]
        # Walk trough the DRS tree
        for root, _, filenames in os.walk(directory, followlinks=True):
            # Follow the latest symlink only
            if ctx.latest:
                if '/latest' in root:
                    for filename in filenames:
                        if os.path.isfile(os.path.join(root, filename)) and \
                           re.match(ctx.filter, filename) is not None:
                            yield os.path.join(root, filename), ctx
            # Pick up the specified version only (from directory path or --version flag)
            elif ctx.version:
                if re.compile(r'/v' + ctx.version).search(root):
                    for filename in filenames:
                        if os.path.isfile(os.path.join(root, filename)) and \
                           re.match(ctx.filter, filename) is not None:
                            yield os.path.join(root, filename), ctx
            # Pick up all encountered versions
            elif ctx.all:
                if re.compile(r'/v[0-9]{8}').search(root):
                    for filename in filenames:
                        if os.path.isfile(os.path.join(root, filename)) and \
                           re.match(ctx.filter, filename) is not None:
                            yield os.path.join(root, filename), ctx
            # Pick up the latest version among encountered versions (default)
            elif re.compile(r'/v[0-9]{8}').search(root):
                versions = [v for v in os.listdir(re.split(r'/v[0-9]{8}', root)[0])
                            if re.compile(r'v[0-9]{8}').search(v)]
                if re.compile(r'/' + sorted(versions)[-1]).search(root):
                    for filename in filenames:
                        if os.path.isfile(os.path.join(root, filename)) and \
                           re.match(ctx.filter, filename) is not None:
                            yield os.path.join(root, filename), ctx


def write(outfile, msg):
    """
    Writes in a mapfile using the ``with`` statement.

    :param str outfile: The mapfile full path
    :param str msg: The line to write

    """
    with open(outfile, 'a+') as mapfile:
        mapfile.write(msg)


def wrapper(inputs):
    """
    Transparent wrapper for pool map.

    :param tuple inputs: A tuple with the file path and the processing context
    :returns: The :func:`file_process` call
    :rtype: *callable*

    """
    # Extract file full path (ffp) and processing context (ctx) from inputs
    ffp, ctx = inputs
    try:
        return file_process(inputs)
    except:
        # Use verbosity to raise threads traceback errors
        if not ctx.verbose:
            logging.warning('{0} skipped'.format(ffp))
        else:
            logging.exception('A thread-process fails:')
        return None


def counted(fct):
    """
    Decorator used to count all file process calls.

    :param callable fct: The function to monitor
    :returns: A wrapped function with a ``.called`` attribute
    :rtype: *callable*

    """
    # Convenience decorator to keep the file_process docstring
    @wraps(fct)
    def wrap(*args, **kwargs):
        """
        Wrapper function for counting
        """
        wrap.called += 1
        return fct(*args, **kwargs)
    wrap.called = 0
    wrap.__name__ = fct.__name__
    return wrap


@counted
def file_process(inputs):
    """
    file_process(inputs)

    File process that:

     * Builds dataset ID,
     * Retrieves file size,
     * Does checksums,
     * Deduces mapfile name,
     * Writes the corresponding line into it.

    :param tuple inputs: A tuple with the file path and the processing context
    :return: The output mapfile name
    :rtype: *str*

    """
    # Extract inputs from tuple
    ffp, ctx = inputs
    # Deduce dataset identifier from DRS tree and esg_<project>.ini
    dataset_id, dataset_version = get_dataset_id(ctx, ffp)
    # Retrieve size and modification time
    size = os.stat(ffp).st_size
    mtime = os.stat(ffp).st_mtime
    # Make the file checksum (MD5)
    csum = None
    if ctx.checksum_client:
        csum = checksum(ffp, ctx.checksum_type, ctx.checksum_client)
    # Build mapfile name depending on the --mapfile flag and appropriate tokens
    outmap = ctx.outmap
    if re.compile(r'\{dataset_id\}').search(outmap):
        outmap = re.sub(r'\{dataset_id\}', dataset_id, outmap)
    if re.compile(r'\{version\}').search(outmap):
        if ctx.latest:
            outmap = re.sub(r'\{version\}', 'latest', outmap)
        elif dataset_version:
            outmap = re.sub(r'\{version\}', dataset_version, outmap)
        else:
            outmap = re.sub(r'.\{version\}', '', outmap)
    if re.compile(r'\{date\}').search(outmap):
        outmap = re.sub(r'\{date\}', datetime.now().strftime("%Y%d%m"), outmap)
    if re.compile(r'\{job_id\}').search(outmap):
        outmap = re.sub(r'\{job_id\}', str(os.getpid()), outmap)
    outmap += '.map'
    outfile = os.path.join(ctx.dtemp, outmap)
    # Mapfile line corresponding to processed file
    # Add version number to dataset identifier if --no-version flag is disabled
    if dataset_version:
        line = ['{0}#{1}'.format(dataset_id, dataset_version[1:])]
    else:
        line = [dataset_id]
    line.append(ffp)
    line.append(str(size))
    line.append('mod_time={0}.000000'.format(str(mtime)))
    if ctx.checksum_client:
        line.append('checksum={0}'.format(csum))
        line.append('checksum_type={0}'.format(ctx.checksum_type))
    if ctx.notes_url:
        line.append('dataset_tech_notes={0}'.format(ctx.notes_url))
    if ctx.notes_title:
        line.append('dataset_tech_notes_title={0}'.format(ctx.notes_title))
    # Generate a lockfile to avoid that several threads write on the same file at the same time
    # LockFile is acquired and released after writing.
    # Acquiring LockFile is timeouted if it's locked by other thread.
    # Each process adds one line to the appropriate mapfile
    lock = LockFile(outfile)
    try:
        lock.acquire(timeout=int(__LOCK_TIMEOUT__))
        write(outfile, ' | '.join(line) + '\n')
        lock.release()
    except LockFailed:
        raise Exception('Failed to lock file: {0}'.format(outfile))
    except LockTimeout:
        raise Exception('Timeout exceeded for {0}'.format(ffp))
    logging.info('{0} <-- {1}'.format(outmap, ffp))
    # Return mapfile name
    return outmap


def run(job=None):
    """
    Main process that:

     * Instantiates processing context,
     * Creates mapfiles output directory if necessary,
     * Instantiates threads pools,
     * Copies mapfile(s) to the output directory,
     * Removes the temporary directory and its content,
     * Implements exit status values.

    :param dict job: A job from SYNDA if supplied instead of classical command-line use.

    """
    # Instantiate processing context from command-line arguments or SYNDA job dictionnary
    ctx = ProcessingContext(get_args(job))
    logging.info('==> Scan started')
    # Create output directory if not exists
    if not os.path.isdir(ctx.outdir):
        if ctx.verbose:
            logging.warning('Create output directory: {0}'.format(ctx.outdir))
        os.makedirs(ctx.outdir)
    # Start threads pool over files list in supplied directory
    pool = ThreadPool(int(ctx.threads))
    # Return the list of generated mapfiles in temporary directory
    outmaps_all = [x for x in pool.imap(wrapper, yield_inputs(ctx))]
    outmaps = [x for x in outmaps_all if x is not None]
    # Close threads pool
    pool.close()
    pool.join()
    # Raises exception when all processed files failed (i.e., filtered list empty)
    if not outmaps:
        rmdtemp(ctx)
        if file_process.called == 0:
            raise Exception('No files found leading to no mapfile.')
        else:
            raise Exception('All files have been ignored or have failed leading to no mapfile.')
    # Overwrite each existing mapfile in output directory
    for outmap in list(set(outmaps)):
        copy2(os.path.join(ctx.dtemp, outmap), ctx.outdir)
    # Remove temporary directory
    rmdtemp(ctx)
    logging.info('==> Scan completed ({0} file(s) scanned)'.format(file_process.called))
    # Non-zero exit status if any files got filtered
    if None in outmaps_all:
        logging.warning('==> Scan completed '
                        '({0} file(s) skipped)'.format(len(outmaps_all) - len(outmaps)))
        sys.exit(2)


# Main entry point for stand-alone call.
if __name__ == "__main__":
    run()
