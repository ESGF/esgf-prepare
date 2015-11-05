#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Generates ESGF mapfiles.

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
__version__ = '{0} {1}'.format('v0.7', datetime.now().strftime("%Y-%d-%m"))

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

    :param dict args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *dict*
    :raises Error: If the project name is inconsistent with the sections names from the configuration file

    """
    def __init__(self, args):
        init_logging(args.logdir)
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
        self.filter = args.filter
        self.project = args.project
        self.cfg = config_parse(args.i, args.project)
        self.project_section = 'project:{0}'.format(args.project)
        if not self.cfg.has_section(self.project_section):
            raise Exception('No section in configuration file corresponds to "{0}" project.\
                             Supported projects are {1}.'.format(args.project,
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
    Returns parsed command-line arguments. See ``esg_mapfiles -h`` for full description.
    A ``job`` dictionnary can be used as developper's entry point to overload the parser.

    :param dict job: Optionnal dictionnary instead of command-line arguments
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

                    esgscan_directory allows you to easily generate ESG-F mapfiles upon local ESGF
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
        epilog="""Developped by:|n
                  Levavasseur, G. (CNRS/IPSL - glipsl@ipsl.jussieu.fr)|n
                  Berger, K. (DKRZ - berger@dkrz.de)|n
                  Iwi, A. (STFC/BADC - alan.iwi@stfc.ac.uk)""")
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
        default='{dataset_id}.{version}.map',
        help="""Specifies template for the output mapfile(s) name.|n
                Substrings {dataset_id}, {version} or {date} (in YYYYDDMM)|n
                will be substituted where found. If {dataset_id} is not|n
                present in mapfile name, then all datasets will be written|n
                to a single mapfile, overriding the default behavior of|n
                producing ONE mapfile PER dataset.""")
    parser.add_argument(
        '--outdir',
        metavar='.../{0}/.'.format(os.getcwd().split('/')[-1]),
        type=str,
        default=os.getcwd(),
        help="""Mapfile(s) output directory (default is working directory).""")
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
        metavar='".*\.nc$"',
        type=str,
        default='.*\.nc$',
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
        '--logdir',
        metavar='.../{0}/.'.format(os.getcwd().split('/')[-1]),
        type=str,
        const=os.getcwd(),
        nargs='?',
        help="""Logfile directory (default is working directory). If not,|n
                standard output is used.""")
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
        # SYNDA submits non-latest path to translate
        return parser.parse_args([re.sub('v[0-9]*$',
                                         'latest',
                                         os.path.normpath(job['full_path_variable'])),
                                 '--project', job['project'].lower(),
                                 '--outdir', '/home/esg-user/mapfiles/pending/',
                                 '-l', 'synda_logger',
                                 '--latest-symlink',
                                 '-v'])


def get_dataset_ID(ctx, file):
    """
    Builds the dataset identifier. The DRS attributes are deduced from the file full path using
    the directory_format regex pattern. The project facet is added in any case with lower case. If
    the version facet cannot be deduced from full path (e.g., with --latest-symlink flag), it
    follows the symlink to complete the DRS attributes. If the dataset name is not specified
    (i.e., --dataset flag is None), it:
     * Checks each facet value regarding the corresponding option list in the esg_<project>.ini,
     * Gets missing attributes from the correponding maptable in the esg_<project>.ini,
     * Builds the dataset identifier from the attributes,

    :param str file: The file full path
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The dataset ID and the dataset version as a tuple
    :rtype: *tuple*
    :raises Error: If the file full path does not match the ``directory_format`` pattern/regex

    """
    # Matching file full path with corresponding project pattern to get DRS attributes values
    # attributes.keys() are facet names
    # attributes[facet] is the facet value.
    try:
        attributes = re.match(ctx.pattern, file).groupdict()
        attributes['project'] = ctx.project.lower()
        # If file path is a symlink, deduce the version following the symlink
        if ctx.latest:
            pointed_path = os.path.realpath(''.join(re.split(r'(latest)', file)[:-1]))
            attributes['version'] = os.path.basename(pointed_path)
    except:
        raise Exception('Matching failed to deduce DRS attributes from {0}. Please check the\
                        "directory_format" regex in esg.{1}.ini'.format(file,
                                                                        ctx.project))
    # Check each facet required by the dataset_id template from esg.<project>.ini
    # Available facet values have been deduced from file full-path
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
        dataset_ID = ctx.cfg.get(ctx.project_section, 'dataset_id', 0, attributes)
    else:
        dataset_ID = ctx.dataset
    return dataset_ID, attributes['version']


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
    if not facet in ['project', 'filename', 'variable', 'version']:
        if ctx.cfg.has_option(ctx.project_section, '{0}_options'.format(facet)):
            options = split_line(ctx.cfg.get(ctx.project_section,
                                             '{0}_options'.format(facet)),
                                 sep=',')
            if not attributes[facet] in options:
                raise Exception('"{0}" is missing in "{1}_options" of the section "{2}" from '
                                'esg.{3}.ini'.format(attributes[facet],
                                                     facet,
                                                     ctx.project_section,
                                                     ctx.project))
        elif facet == 'ensemble':
            if not re.compile(r'r[\d]+i[\d]+p[\d]+').search(attributes[facet]):
                raise Exception('Wrong syntax for "ensemble" facet. '
                                'Please follow the regex "r[0-9]*i[0-9]*p[0-9]*".')
        else:
            raise Exception('"{0}_options" is missing in section "{1}" '
                            'from esg.{2}.ini'.format(facet,
                                                      ctx.project_section,
                                                      ctx.project))


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
        if not facet in to_keys:
            raise Exception('{0}_map is miss-declared in esg.{1}.ini. '
                            '"{0}" facet has to be in "destination facet"'.format(facet,
                                                                                  ctx.project))
        from_values = tuple(attributes[key] for key in from_keys)
        to_values = value_map[from_values]
        attributes[facet] = to_values[to_keys.index(facet)]
    elif facet == 'ensemble':
        if not re.compile(r'r[\d]+i[\d]+p[\d]+').search(attributes[facet]):
                raise Exception('Wrong syntax for "ensemble" facet. '
                                'Please follow the regex "r[0-9]*i[0-9]*p[0-9]*".')
    else:
        raise Exception('{0}_map is required in esg.{1}.ini'.format(facet, ctx.project))
    return attributes


def checksum(file, checksum_type, checksum_client):
    """
    Does the checksum by the Shell avoiding Python memory limits.

    :param str file: The full path of a file
    :param str checksum_client: Shell commande line for checksum
    :param str checksum_type: Checksum type
    :raises Error: If the checksum fails

    """
    try:
        shell = os.popen("{0} {1} | awk -F ' ' '{{ print $1 }}'".format(checksum_client, file), 'r')
        return shell.readline()[:-1]
    except:
        raise Exception('{0} checksum failed for {1}'.format(checksum_type, file))


def rmdtemp(ctx):
    """
    Removes the temporary directory and its content.

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)

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

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: Attach the processing context to a file to process as an iterator of tuples
    :rtype: *iter*

    """
    for directory in ctx.directory:
        # Set --version flag if version number is included in the supplied directory path
        # to recursively scan
        if re.compile('/v[0-9]*/').search(directory):
            ctx.version = re.compile('/v[0-9]*/').search(directory).group()[1:]
        # Walk trought the DRS tree
        for root, dirs, files in os.walk(directory, followlinks=True):
            # Follow the latest symmlink only
            if ctx.latest:
                if '/latest/' in root:
                    for file in files:
                        if os.path.isfile(os.path.join(root, file)) and \
                           re.match(ctx.filter, file) is not None:
                            yield os.path.join(root, file), ctx
            # Pick up the specified version only (from directory path or --version flag)
            elif ctx.version:
                if re.compile('/v' + ctx.version + '/').search(root):
                    for file in files:
                        if os.path.isfile(os.path.join(root, file)) and \
                           re.match(ctx.filter, file) is not None:
                            yield os.path.join(root, file), ctx
            # Pick up all encountered versions
            elif ctx.all:
                if re.compile('/v[0-9]*/').search(root):
                    for file in files:
                        if os.path.isfile(os.path.join(root, file)) and \
                           re.match(ctx.filter, file) is not None:
                            yield os.path.join(root, file), ctx
            # Pick up the latest version among encountered versions (default)
            elif re.compile('/v[0-9]*/').search(root):
                versions = filter(lambda i: re.compile('v[0-9]').search(i),
                                  os.listdir(re.split('/v[0-9]*/', root)[0]))
                if re.compile('/' + sorted(versions)[-1] + '/').search(root):
                    for file in files:
                        if os.path.isfile(os.path.join(root, file)) and \
                           re.match(ctx.filter, file) is not None:
                            yield os.path.join(root, file), ctx


def write(outfile, msg):
    """
    Writes in a mapfile using the ``with`` statement.

    :param str outfile: The mapfile full path
    :param str msg: The line to write

    """
    with open(outfile, 'a+') as f:
        f.write(msg)


def wrapper(inputs):
    """
    Transparent wrapper for pool map.

    :param tuple inputs: A tuple with the file path and the processing context
    :returns: The :func:`file_process` call
    :rtype: *callable*

    """
    # Extract inputs from tuple
    file, ctx = inputs
    try:
        return file_process(inputs)
    except:
        # Use verbosity to raise threads traceback errors
        if not ctx.verbose:
            logging.warning('{0} skipped'.format(inputs[0]))
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
    def wrapper(*args, **kwargs):
        wrapper.called += 1
        return fct(*args, **kwargs)
    wrapper.called = 0
    wrapper.__name__ = fct.__name__
    return wrapper


@counted
def file_process(inputs):
    """
    file_process(inputs)

    File process that\:
     * Builds dataset ID,
     * Retrieves file size,
     * Does checksums,
     * Deduce mapfile name,
     * Writes the corresponding line into it.

    :param tuple inputs: A tuple with the file path and the processing context
    :return: The output mapfile name
    :rtype: *str*

    """
    # Extract inputs from tuple
    file, ctx = inputs
    # Deduce dataset identifier from DRS tree and esg_<project>.ini
    dataset_ID, dataset_version = get_dataset_ID(ctx, file)
    # Retrieve size and modification time
    (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)
    # Make the file checksum (MD5)
    if ctx.checksum_client:
        csum = checksum(file, ctx.checksum_type, ctx.checksum_client)
    # Build mapfile name depending on the --mapfile flag and appropriate tokens
    outmap = ctx.outmap
    if re.compile(r'{dataset_id}').search(outmap):
        outmap = re.sub('{dataset_id}', dataset_ID, outmap)
    if re.compile(r'{version}').search(outmap):
        if ctx.latest:
            outmap = re.sub('{version}', 'latest', outmap)
        else:
            outmap = re.sub('{version}', dataset_version, outmap)
    if re.compile(r'{date}').search(outmap):
        outmap = re.sub('{date}', datetime.now().strftime("%Y%d%m"), outmap)
    if re.compile(r'{pid}').search(outmap):
        outmap = re.sub('{pid}', str(os.getpid()), outmap)
    outfile = os.path.join(ctx.dtemp, outmap)
    # Mapfile line corresponding to processed file
    # Add version number to dataset identifier if --no-version flag is disabled
    if not ctx.no_version:
        line = ['{0}#{1}'.format(dataset_ID, dataset_version[1:])]
    else:
        line = [dataset_ID]
    line.append(file)
    line.append(str(size))
    line.append('mod_time='+str(mtime)+'.000000')
    if ctx.checksum_client:
        line.append('checksum='+csum)
        line.append('checksum_type='+ctx.checksum_type)
    if ctx.notes_url:
        line.append('dataset_tech_notes='+ctx.notes_url)
    if ctx.notes_title:
        line.append('dataset_tech_notes_title='+ctx.notes_title)
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
        raise Exception('Timeout exceeded for {0}'.format(file))
    logging.info('{0} <-- {1}'.format(outmap, file))
    # Return mapfile name
    return outmap


def run(job=None):
    """
    Main process that\:
     * Instantiates processing context,
     * Creates mapfiles output directory if necessary,
     * Instantiates threads pools,
     * Copies mapfile(s) to the output directory,
     * Removes the temporary directory and its content,
     * Implements exit status values.

    :param dict job: A job from SYNDA if supplied instead of classical command-line use.

    """
    # Instanciate processing context from command-line arguments or SYNDA job dictionnary
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
    outmaps = filter(lambda m: m is not None, outmaps_all)
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
