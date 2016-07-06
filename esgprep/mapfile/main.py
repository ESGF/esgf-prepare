#!/usr/bin/env python

import sys
import os
import re
import logging
from esgprep.utils import utils, parser
from multiprocessing.dummy import Pool as ThreadPool
from functools import wraps
from lockfile import LockFile
from datetime import datetime
from file_handler import File

# Lockfile timeout (in sec)
__LOCK_TIMEOUT__ = 30

# Mapfile extension during processing
__WORKING_EXTENSION__ = '.part'

# Mapfile final extension (mapfiles always are TXT files)
__FINAL_EXTENSION__ = '.map'


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
    | *self*.facets          | *list*      | List of the DRS facets                       |
    +------------------------+-------------+----------------------------------------------+

    :param ArgumentParser args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *ProcessingContext*
    :raises Error: If no section corresponds to the project name in the configuration file

    """
    def __init__(self, args):
        for path in args.directory:
            utils.check_directory(path)
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
        self.cfg = parser.config_parse(args.i, args.project, self.project_section)
        if args.no_checksum:
            self.checksum_client, self.checksum_type = None, None
        elif self.cfg.has_option('DEFAULT', 'checksum'):
            self.checksum_client, self.checksum_type = parser.split_line(self.cfg.get('DEFAULT', 'checksum'))
        else:  # Use SHA256 as default because esg.ini not mandatory in configuration directory
            self.checksum_client, self.checksum_type = 'sha256sum', 'SHA256'
        self.facets = set(re.findall(re.compile(r'%\(([^()]*)\)s'),
                                     self.cfg.get(self.project_section, 'dataset_id', raw=True)))
        self.pattern = parser.translate_directory_format(self.cfg.get(self.project_section,
                                                                      'directory_format',
                                                                      raw=True))


def yield_inputs(ctx):
    """
    Yields all files to process within tuples with the processing context. The file walking
    through the DRS tree follows the latest version of each dataset. This behavior is modified
    using:

     * ``--all-versions`` flag, to pick up all versions,
     * ``--version <version_number>`` argument, to pick up a specified version,
     * ``--latest-symlink`` flag, to pick up the version pointed by the latest symlink (if exists).

    If the supplied directory to scan specifies the version into its path, only this version is
    picked up as with ``--version`` argument.

    :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
    :returns: Attach the processing context to a file to process as an iterator of tuples
    :rtype: *iter*

    """
    for directory in ctx.directory:
        # Set --version flag if version number is included in the supplied directory path
        # to recursively scan
        if re.compile(r'/v[0-9]+').search(directory):
            ctx.version = re.compile(r'/v[0-9]+').search(directory).group()[2:]
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
                if re.compile(r'/v[0-9]+').search(root):
                    for filename in filenames:
                        if os.path.isfile(os.path.join(root, filename)) and \
                           re.match(ctx.filter, filename) is not None:
                            yield os.path.join(root, filename), ctx
            # Pick up the latest version among encountered versions (default)
            elif re.compile(r'/v[0-9]+').search(root):
                versions = [v for v in os.listdir(re.split(r'/v[0-9]+', root)[0])
                            if re.compile(r'v[0-9]+').search(v)]
                if re.compile(r'/' + sorted(versions)[-1]).search(root):
                    for filename in filenames:
                        if os.path.isfile(os.path.join(root, filename)) and \
                           re.match(ctx.filter, filename) is not None:
                            yield os.path.join(root, filename), ctx
            # No version directory in path
            else:
                for filename in filenames:
                    if os.path.isfile(os.path.join(root, filename)) and \
                       re.match(ctx.filter, filename) is not None:
                        yield os.path.join(root, filename), ctx


def wrapper(inputs):
    """
    Transparent wrapper for pool map.

    :param tuple inputs: A tuple with the file path and the processing context
    :returns: The :func:`process` call
    :rtype: *callable*

    """
    # Extract file full path (ffp) and processing context (ctx) from inputs
    ffp, ctx = inputs
    try:
        return process(ffp, ctx)
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


def get_output_mapfile(attributes, dataset_id, dataset_version, ctx):
    """
    Builds the mapfile full path depending on:

     * the --mapfile name using tokens,
     * the --outdir output directory.

    The output directory can be deduced from file attributes in the case of a mapfile DRS.
    The ``mapfile_drs`` defined into esg.<project>.ini file can joined or substituted to output directory (default
    is the current working directory).

    :param dict attributes: The facets values deduces from file full path
    :param str dataset_id: The corresponding dataset id
    :param str dataset_version: The corresponding dataset version
    :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
    :returns: The mapfile full path
    :rtype: *str*

    """
    # Deduce output directory from --outdir of 'mapfile_drs'
    outdir = os.path.realpath(ctx.outdir)
    if ctx.cfg.has_option(ctx.project_section, 'mapfile_drs'):
        outdir = '{0}/{1}'.format(os.path.realpath(ctx.outdir),
                                  ctx.cfg.get(ctx.project_section, 'mapfile_drs', 0, attributes))
    # Create output directory if not exists, catch OSError instead
    try:
        os.makedirs(outdir)
    except OSError:
        pass
    # Deduce mapfile name from --mapfile argument
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
    return os.path.join(outdir, outmap) + __WORKING_EXTENSION__


def generate_mapfile_entry(dataset_id, dataset_version, ffp, size, mtime, csum, ctx):
    """
    Builds the mapfile entry corresponding to a processed file.

    :param str dataset_id: The corresponding dataset id
    :param str dataset_version: The corresponding dataset version
    :param str ffp: The file full path
    :param str size: The file size
    :param str mtime: The last modification time
    :param str csum: The file checksum
    :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
    :returns: THe mapfile line/entry
    :rtype: *str*

    """
    line = [dataset_id]
    # Add version number to dataset identifier if --no-version flag is disabled
    if dataset_version:
        line = ['{0}#{1}'.format(dataset_id, dataset_version[1:])]
    line.append(ffp)
    line.append(str(size))
    line.append('mod_time={0}'.format(str(mtime)))
    if ctx.checksum_client:
        line.append('checksum={0}'.format(csum))
        line.append('checksum_type={0}'.format(ctx.checksum_type))
    if ctx.notes_url:
        line.append('dataset_tech_notes={0}'.format(ctx.notes_url))
    if ctx.notes_title:
        line.append('dataset_tech_notes_title={0}'.format(ctx.notes_title))
    return ' | '.join(line) + '\n'


def insert_mapfile_entry(outfile, entry, ffp):
    """
    Inserts a mapfile entry using the ``with`` statement dealing with multiple threads.
    It generates a lockfile to avoid that several threads write on the same file at the same time.
    A LockFile is acquired and released after writing. Acquiring LockFile is timeouted if it's locked by other thread.
    Each process adds one line to the appropriate mapfile

    :param str outfile: The output mapfile full path
    :param str entry: The mapfile entry to write
    :param str ffp: The file full path

    """
    lock = LockFile(outfile)
    with lock:
        with open(outfile, 'a+') as mapfile:
            mapfile.write(entry)
    logging.info('{0} <-- {1}'.format(os.path.splitext(os.path.basename(outfile))[0], ffp))


@counted
def process(ffp, ctx):
    """
    process(ffp, ctx)

    File process that:

     * Builds dataset ID,
     * Retrieves file size,
     * Does checksums,
     * Deduces mapfile name,
     * Makes output directory if not already exists,
     * Writes the corresponding line into it.

    :param str ffp: The file full path
    :param esgprep.mapfile.main.ProcessingContext ctx: The processing context
    :return: The output file full path
    :rtype: *str*

    """
    # Instantiate file handler
    fh = File(ffp)
    # Matching between directory_format and file full path
    fh.load_attributes(ctx)
    # Deduce dataset_id
    dataset_id = fh.get_dataset_id(ctx)
    # Deduce dataset_version
    dataset_version = fh.get_dataset_version(ctx)
    # Build mapfile name depending on the --mapfile flag and appropriate tokens
    outfile = get_output_mapfile(fh.attributes, dataset_id, dataset_version, ctx)
    # Generate the corresponding mapfile entry/line
    line = generate_mapfile_entry(dataset_id,
                                  dataset_version,
                                  ffp,
                                  fh.size,
                                  fh.mtime,
                                  fh.checksum(ctx.checksum_type, ctx.checksum_client),
                                  ctx)
    insert_mapfile_entry(outfile, line, ffp)
    # Return mapfile name
    return outfile


def main(args):
    """
    Main process that:

     * Instantiates processing context,
     * Creates mapfiles output directory if necessary,
     * Instantiates threads pools,
     * Copies mapfile(s) to the output directory,
     * Removes the temporary directory and its content,
     * Implements exit status values.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Instantiate processing context from command-line arguments or SYNDA job dictionary
    ctx = ProcessingContext(args)
    logging.info('==> Scan started')
    # Start threads pool over files list in supplied directory
    pool = ThreadPool(int(ctx.threads))
    # Return the list of generated mapfiles full paths
    outfiles_all = [x for x in pool.imap(wrapper, yield_inputs(ctx))]
    outfiles = [x for x in outfiles_all if x is not None]
    # Close threads pool
    pool.close()
    pool.join()
    # Raises exception when all processed files failed (i.e., filtered list empty)
    if not outfiles:
        if process.called == 0:
            raise Exception('No files found leading to no mapfile.')
        else:
            raise Exception('All files have been ignored or have failed leading to no mapfile.')
    # Replace mapfile working extension by final extension
    # A final mapfile is silently overwritten if already exists
    for outfile in list(set(outfiles)):
        os.rename(outfile, outfile.replace(__WORKING_EXTENSION__, __FINAL_EXTENSION__))
    logging.info('==> Scan completed ({0} file(s) scanned)'.format(process.called))
    # Non-zero exit status if any files got filtered
    if None in outfiles_all:
        logging.warning('==> Scan completed '
                        '({0} file(s) skipped)'.format(len(outfiles_all) - len(outfiles)))
        sys.exit(2)
