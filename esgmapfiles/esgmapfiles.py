#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Build ESGF mapfiles without ``esgscan_directory`` upon local ESGF datanode.

"""

import sys
import os
import re
import argparse
import logging
from esgmapfilesutils import init_logging, check_directory, config_parse
from multiprocessing.dummy import Pool as ThreadPool
from functools import wraps
from argparse import RawTextHelpFormatter
from lockfile import LockFile, LockTimeout, LockFailed
from tempfile import mkdtemp
from shutil import copy2, rmtree

# Program version
__version__ = '{0} {1}-{2}-{3}'.format('v0.5.3', '2015', '07', '06')


class ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +---------------------+-------------+---------------------------------------+
    | Attribute           | Type        | Description                           |
    +=====================+=============+=======================================+
    | *self*.directory    | *list*      | Paths to scan                         |
    +---------------------+-------------+---------------------------------------+
    | *self*.latest       | *boolean*   | True if latest version                |
    +---------------------+-------------+---------------------------------------+
    | *self*.outdir       | *str*       | Output directory                      |
    +---------------------+-------------+---------------------------------------+
    | *self*.verbose      | *boolean*   | True if verbose mode                  |
    +---------------------+-------------+---------------------------------------+
    | *self*.with_version | *boolean*   | True to include version in dataset ID |
    +---------------------+-------------+---------------------------------------+
    | *self*.project      | *str*       | Project                               |
    +---------------------+-------------+---------------------------------------+
    | *self*.dataset      | *boolean*   | True if one mapfile per dataset       |
    +---------------------+-------------+---------------------------------------+
    | *self*.checksum     | *boolean*   | True if checksums into mapfile        |
    +---------------------+-------------+---------------------------------------+
    | *self*.outmap       | *str*       | Mapfile output name                   |
    +---------------------+-------------+---------------------------------------+
    | *self*.cfg          | *callable*  | Configuration file parser             |
    +---------------------+-------------+---------------------------------------+
    | *self*.pattern      | *re object* | DRS regex pattern                     |
    +---------------------+-------------+---------------------------------------+
    | *self*.dtemp        | *str*       | Directory of temporary files          |
    +---------------------+-------------+---------------------------------------+

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
        self.verbose = args.verbose
        self.latest = args.latest
        self.outdir = args.outdir
        self.with_version = args.with_version
        self.dataset = args.per_dataset
        self.cfg = config_parse(args.config)
        if args.project in self.cfg.sections():
            self.project = args.project
        else:
            raise Exception('No section in configuration file corresponds to "{0}" project. Supported projects are {1}.'.format(args.project, self.cfg.sections()))
        if args.checksum:
            self.checksum = str(self.cfg.defaults()['checksum_type'])
        else:
            self.checksum = None
        self.pattern = re.compile(self.cfg.get(self.project, 'directory_format'))
        self.dtemp = mkdtemp()


def get_args(job):
    """
    Returns parsed command-line arguments. See ``esg_mapfiles -h`` for full description.
    A ``job`` dictionnary can be used as developper's entry point to overload the parser.

    :param dict job: Optionnal dictionnary instead of command-line arguments.
    :returns: The corresponding ``argparse`` Namespace

    """
    parser = argparse.ArgumentParser(
        description="""Build ESGF mapfiles upon local ESGF datanode bypassing esgscan_directory\ncommand-line.""",
        formatter_class=RawTextHelpFormatter,
        add_help=False,
        epilog="""

Exit status:
        0 successful scanning of all files encountered
        1 no valid data files found and no mapfile produced
        2 a mapfile was produced but some files were skipped

Developed by Levavasseur, G. (CNRS/IPSL)""")
    parser.add_argument(
        'directory',
        type=str,
        nargs='+',
        help='One or more directories to recursively scan. Unix wildcards are allowed.')
    parser.add_argument(
        '-h', '--help',
        action="help",
        help="""Show this help message and exit.\n\n""")
    parser.add_argument(
        '-p', '--project',
        type=str,
        required=True,
        help="""Required project name corresponding to a section of the configuration file.\n\n""")
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='{0}/config.ini'.format(os.path.dirname(os.path.abspath(__file__))),
        help="""Path of configuration INI file\n(default is {0}/config.ini).\n\n""".format(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument(
        '-o', '--outdir',
        type=str,
        default=os.getcwd(),
        help="""Mapfile(s) output directory\n(default is working directory).\n\n""")
    parser.add_argument(
        '-l', '--logdir',
        type=str,
        const=os.getcwd(),
        nargs='?',
        help="""Logfile directory (default is working directory).\nIf not, standard output is used.\n\n""")
    parser.add_argument(
        '-m', '--mapfile',
        type=str,
        default='mapfile.txt',
        help="""Output mapfile name. Only used without --per-dataset option\n(default is 'mapfile.txt').\n\n""")
    parser.add_argument(
        '-d', '--per-dataset',
        action='store_true',
        default=False,
        help="""Produces ONE mapfile PER dataset. It takes priority over --mapfile.\n\n""")
    parser.add_argument(
        '-L', '--latest',
        action='store_true',
        default=False,
        help="""Generates mapfiles with latest versions only.\n\n""")
    parser.add_argument(
        '-w', '--with-version',
        action='store_true',
        default=False,
        help="""Includes DRS version into dataset ID (ESGF 2.x compatibility).\n\n""")
    parser.add_argument(
        '-C', '--checksum',
        action='store_true',
        default=False,
        help="""Includes file checksums into mapfiles (default is a SHA256 checksum).\n\n""")
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help="""Verbose mode.\n\n""")
    parser.add_argument(
        '-V', '--Version',
        action='version',
        version='%(prog)s ({0})'.format(__version__),
        help="""Program version.""")
    if job is None:
        return parser.parse_args()
    else:
        # SYNDA submits non-latest path to translate
        return parser.parse_args([re.sub('v[0-9]*$', 'latest', os.path.normpath(job['full_path_variable'])), '-p', 'cmip5', '-c', '/home/esg-user/mapfile.ini', '-o', '/home/esg-user/mapfiles/pending/', '-l', 'synda_logger', '-d', '-L', '-C', '-v'])


def get_master_ID(attributes, ctx):
    """
    Builds the master identifier of a dataset.

    :param dict attributes: The attributes auto-detected with DRS pattern
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The master ID with the version
    :rtype: *str*

    """
    dataset_ID = ctx.cfg.get(ctx.project, 'dataset_ID')
    facets = re.split('\.|#', dataset_ID)
    for facet in facets:
        dataset_ID = dataset_ID.replace(facet, attributes[facet])
    return dataset_ID


def check_facets(attributes, ctx, file):
    """
    Checks all attributes from path. Each attribute or facet is auto-detected using the DRS pattern (regex) and compared to its corresponding options declared into the configuration file.

    :param dict attributes: The attributes auto-detected with DRS pattern
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :raises Error: If an option of an attribute is not declared

    """
    for facet in attributes.keys():
        if not facet in ['project', 'filename', 'variable', 'root', 'version', 'ensemble']:
            options = ctx.cfg.get(ctx.project, '{0}_options'.format(facet)).replace(" ", "").split(',')
            if not attributes[facet] in options:
                raise Exception('"{0}" is missing in "{1}_options" of the "{2}" section from the configuration file to properly process {3}'.format(attributes[facet], facet, ctx.project, file))


def checksum(file, ctx):
    """
    Does the MD5 or SHA256 checksum by the Shell avoiding Python memory limits.

    :param str file: The full path of a file
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :raises Error: If the checksum fails

    """
    assert (ctx.checksum in ['SHA256', 'MD5']), 'Invalid checksum type: {0} instead of MD5 or SHA256'.format(ctx.checksum)
    try:
        if ctx.checksum == 'SHA256':
            shell = os.popen("sha256sum {0} | awk -F ' ' '{{ print $1 }}'".format(file), 'r')
        elif ctx.checksum == 'MD5':
            shell = os.popen("md5sum {0} | awk -F ' ' '{{ print $1 }}'".format(file), 'r')
        return shell.readline()[:-1]
    except:
        raise Exception('Checksum failed for {0}'.format(file))


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
    Yields all files to process within tuples with the processing context. The file walking through the DRS tree follows symbolic links and ignores the "files" directories and "latest" symbolic links if ``--latest`` is None.

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: Attach the processing context to a file to process as an iterator of tuples
    :rtype: *iter*

    """
    for directory in ctx.directory:
        for root, dirs, files in os.walk(directory, followlinks=True):
            if '/files' not in root:
                if not ctx.latest:
                    if '/latest' not in root:
                        for file in files:
                            yield os.path.join(root, file), ctx
                else:
                    if not re.compile('/v[0-9]*').search(root):
                        for file in files:
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
    :returns: The :func:`_file_process` call
    :rtype: *callable*

    """
    # Extract inputs from tuple
    file, ctx = inputs
    try:
        return file_process(inputs)
    except:
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
    @wraps(fct)  # Convenience decorator to keep the file_process docstring
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
     * Auto-detects facets,
     * Builds dataset ID,
     * Does checksums,
     * Writes to appropriate mapfile.

    :param tuple inputs: A tuple with the file path and the processing context
    :return: The output mapfile name
    :rtype: *str*

    """
    # Extract inputs from tuple
    file, ctx = inputs
    # Matching file full path with corresponding project pattern to get all attributes
    try:
        attributes = re.match(ctx.pattern, file).groupdict()
    except:
        # Fails can be due to:
        # -> Wrong project argument
        # -> Mistake in directory_format pattern in configuration file
        # -> Wrong version format (defined as one or more digit after 'v')
        # -> Wrong ensemble format (defined as r[0-9]i[0-9]p[0-9])
        # -> Mistake in the DRS tree of your filesystem.
        raise Exception('The "directory_format" regex cannot match {0}'.format(file))
    else:
        # Control vocabulary of each facet
        check_facets(attributes, ctx, file)
        # Deduce master ID from full path and --latest option
        if ctx.with_version:
            if ctx.latest:
                master_ID = get_master_ID(attributes, ctx).replace(attributes['version'], os.path.basename(os.path.realpath(''.join(re.split(r'(latest)', file)[:-1])))[1:])
            else:
                master_ID = get_master_ID(attributes, ctx).replace(attributes['version'], attributes['version'][1:])
        else:
            master_ID = get_master_ID(attributes, ctx).replace('#' + attributes['version'], '')

        # Retrieve size and modification time
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)
        # Make the file checksum (MD5)
        if ctx.checksum:
            csum = checksum(file, ctx)
        # Build mapfile name if one per dataset, or read the supplied name instead
        if ctx.dataset:
            outmap = '{0}{1}{2}'.format(master_ID.split('#')[0], '.', attributes['version'])
        else:
            outmap = ctx.outmap
        outfile = os.path.join(ctx.dtemp, outmap)
        # Generate a lockfile to avoid that several threads write on the same file at the same time
        # LockFile is acquired and released after writing.
        # Acquiring LockFile is timeouted if it's locked by other thread.
        # Each process adds one line to the appropriate mapfile
        lock = LockFile(outfile)
        try:
            lock.acquire(timeout=int(ctx.cfg.defaults()['lockfile_timeout']))
            if ctx.checksum:
                write(outfile, '{0} | {1} | {2} | mod_time={3} | checksum={4} | checksum_type={5}\n'.format(master_ID, file, size, str(mtime)+'.000000', csum, ctx.checksum))
            else:
                write(outfile, '{0} | {1} | {2} | mod_time={3}\n'.format(master_ID, file, size, str(mtime)+'.000000'))
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
     * Instantiates processing context
     * Creates mapfiles output directory if necessary,
     * Instantiates threads pools,
     * Copies mapfile(s) to the output directory,
     * Removes the temporary directory and its contents.
     * Implement exit status values as described in get_args (search for 'epilog')

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
    pool = ThreadPool(int(ctx.cfg.defaults()['threads_number']))
    # Return the list of generated mapfiles in temporary directory
    outmaps_all = [x for x in pool.imap(wrapper, yield_inputs(ctx))]
    outmaps = filter(lambda m: m is not None, outmaps_all)
    # Close threads pool
    pool.close()
    pool.join()
    # Raises exception when all processed files failed (filtered list empty)
    if not outmaps:
        rmdtemp(ctx)
        raise Exception('All files have been ignored or have failed: no mapfile.')
    # Overwrite each existing mapfile in output directory
    for outmap in list(set(outmaps)):
        copy2(os.path.join(ctx.dtemp, outmap), ctx.outdir)
    # Remove temporary directory
    rmdtemp(ctx)
    logging.info('==> Scan completed ({0} files scanned)'.format(file_process.called))
    # non-zero exit status if any files got filtered
    if None in outmaps_all:
        logging.warning("==> %d file(s) skipped", 
                        len(outmaps_all) - len(outmaps))
        sys.exit(2)


# Main entry point for stand-alone call.
if __name__ == "__main__":
    run()
