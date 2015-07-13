#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Build ESGF mapfiles without ``esgscan_directory`` upon local ESGF datanode.

"""

# Module imports
import os
import re
import argparse
import ConfigParser
import logging
from multiprocessing.dummy import Pool as ThreadPool
from functools import wraps
from argparse import RawTextHelpFormatter
from lockfile import LockFile, LockTimeout
from datetime import datetime
from tempfile import mkdtemp
from shutil import copy2, rmtree

# Program version
__version__ = '{0} {1}-{2}-{3}'.format('v0.5.3', '2015', '07', '06')

# Log levels
_LEVELS = {'debug': logging.error,
           'info': logging.info,
           'warning': logging.warning,
           'error': logging.error,
           'critical': logging.critical,
           'exception': logging.exception}


class _ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +---------------------+-------------+-------------------------------------+
    | Attribute           | Type        | Description                         |
    +=====================+=============+=====================================+
    | *self*.directory    | *list*      | Directories to scan                 |
    +---------------------+-------------+-------------------------------------+
    | *self*.latest       | *boolean*   | True if latest version              |
    +---------------------+-------------+-------------------------------------+
    | *self*.outdir       | *str*       | Output directory                    |
    +---------------------+-------------+-------------------------------------+
    | *self*.verbose      | *boolean*   | True if verbose mode                |
    +---------------------+-------------+-------------------------------------+
    | *self*.keep         | *boolean*   | True if keep going mode             |
    +---------------------+-------------+-------------------------------------+
    | *self*.with_version | *boolean*   | True: include version in dataset ID |
    +---------------------+-------------+-------------------------------------+
    | *self*.project      | *str*       | Project                             |
    +---------------------+-------------+-------------------------------------+
    | *self*.dataset      | *boolean*   | True if one mapfile per dataset     |
    +---------------------+-------------+-------------------------------------+
    | *self*.checksum     | *boolean*   | True if checksums into mapfile      |
    +---------------------+-------------+-------------------------------------+
    | *self*.outmap       | *str*       | Mapfile output name                 |
    +---------------------+-------------+-------------------------------------+
    | *self*.cfg          | *callable*  | Configuration file parser           |
    +---------------------+-------------+-------------------------------------+
    | *self*.pattern      | *re object* | DRS regex pattern                   |
    +---------------------+-------------+-------------------------------------+
    | *self*.dtemp        | *str*       | Directory of temporary files        |
    +---------------------+-------------+-------------------------------------+

    :param dict args: Parsed command-line arguments
    :returns: The processing context
    :rtype: *dict*

    """
    def __init__(self, args):
        _init_logging(args.logdir)
        self.directory = _check_directory(args.directory)
        self.latest = args.latest
        self.outdir = args.outdir
        self.verbose = args.verbose
        self.keep = args.keep_going
        self.with_version = args.with_version
        self.project = args.project
        self.dataset = args.per_dataset
        self.outmap = args.mapfile
        self.cfg = _config_parse(args.config)
        if args.checksum:
            self.checksum = str(self.cfg.defaults()['checksum_type'])
        else:
            self.checksum = None
        self.pattern = re.compile(self.cfg.get(self.project, 'directory_format'))
        self.dtemp = mkdtemp()


class _SyndaProcessingContext(object):
    """
    Encapsulates the following processing context/information for SYNDA call:

    +---------------------+-------------+----------------------------------------------------+
    | Attribute           | Type        | Description                                        |
    +=====================+=============+====================================================+
    | *self*.directory    | *list*      | Variable path to scan                              |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.latest       | *boolean*   | True: only scan latest version                     |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.outdir       | *str*       | Output directory: /home/esg-user/mapfiles/pending/ |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.verbose      | *boolean*   | True: verbose mode                                 |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.keep         | *boolean*   | True: keep going mode                              |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.with_version | *boolean*   | True: include version in dataset ID                |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.project      | *str*       | Project: cmip5                                     |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.dataset      | *boolean*   | True: one mapfile per dataset                      |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.checksum     | *boolean*   | True: checksums into mapfile                       |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.outmap       | *str*       | None: no mapfile output name                       |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.cfg          | *callable*  | Configuration file parser                          |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.pattern      | *re object* | DRS regex pattern                                  |
    +---------------------+-------------+----------------------------------------------------+
    | *self*.dtemp        | *str*       | Directory of temporary files                       |
    +---------------------+-------------+----------------------------------------------------+

    :param str full_path_variable: Full path of a variable to process
    :returns: A specific processing context for SYNDA
    :rtype: *dict*

    """
    def __init__(self, full_path_variable):
        #_init_logging(args.logdir) # Logger initiates by synda worker
        # "merge" product is mandatory through the configuration file used by synda
        # synda submit non-latest path to translate
        self.directory = _check_directory(re.sub('v[0-9]*$', 'latest', os.path.normpath(full_path_variable)))
        self.latest = True
        self.outdir = '/home/esg-user/mapfiles/pending/'
        self.verbose = True
        self.keep = True
        self.with_version = False
        self.project = 'cmip5'
        self.dataset = True
        self.checksum = True
        self.outmap = False
        self.cfg = _config_parse('/home/esg-user/mapfiles/mapfile.ini')
        self.pattern = re.compile(self.cfg.get(self.project, 'directory_format'))
        self.dtemp = mkdtemp()


class _Exception(Exception):
    """
    When an error is encountered, logs a message with the ``ERROR`` status.

    :param str msg: Error message to log
    :returns: The logged message with the ``ERROR`` status
    :rtype: *str*

    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        print
        _log('error', self.msg)


def _get_args():
    """
    Returns parsed command-line arguments. See ``esg_mapfiles -h`` for full description.

    """
    parser = argparse.ArgumentParser(
        description="""Build ESGF mapfiles upon local ESGF datanode bypassing esgscan_directory\ncommand-line.""",
        formatter_class=RawTextHelpFormatter,
        add_help=False,
        epilog="""Developed by Levavasseur, G. (CNRS/IPSL)""")
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
        choices=['cmip5', 'cordex'],
        required=True,
        help="""Required project to build mapfiles among:\n- cmip5\n- cordex\n\n""")
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
        help="""Includes DRS version into dataset ID (ESGF 2.0 compatibility).\n\n""")
    parser.add_argument(
        '-C', '--checksum',
        action='store_true',
        default=False,
        help="""Includes file checksums into mapfiles (default is a SHA256 checksum).\n\n""")
    parser.add_argument(
        '-k', '--keep-going',
        action='store_true',
        default=False,
        help="""Keep going if some files cannot be processed.\n\n""")
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
    return parser.parse_args()


def _check_directory(paths):
    """
    Checks if all supplied directories exist. All paths are normalized before without trailing slash.

    :param list paths: List of paths
    :returns: The same input list if all paths exist
    :rtype: *list*
    :raises Error: if one directory do not exist

    """
    for path in paths:
        directory = os.path.normpath(path)
        if not os.path.isdir(directory):
            raise _Exception('No such directory: {0}'.format(directory))
    return paths


def _init_logging(logdir):
    """
    Initiates the logging configuration (output, message formatting). In the case of a logfile, the logfile name is unique and formatted as follows:\n
    esgmapfiles-YYYYMMDD-HHMMSS-PID.log

    :param str logdir: The relative or absolute logfile directory. If ``None`` the standard output is used.

    """
    if logdir:
        logfile = 'esg_mapfiles-{0}-{1}.log'.format(datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        logging.basicConfig(filename=os.path.join(logdir, logfile),
                            level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y/%m/%d %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(message)s')


def _log(level, msg):
    """
    Points to the log level as follows:

    +-----------+-------------------+
    | Log level | Log function      |
    +===========+===================+
    | debug     | logging.error     |
    +-----------+-------------------+
    | info      | logging.info      |
    +-----------+-------------------+
    | warning   | logging.warning   |
    +-----------+-------------------+
    | error     | logging.error     |
    +-----------+-------------------+
    | critical  | logging.critical  |
    +-----------+-------------------+
    | exception | logging.exception |
    +-----------+-------------------+

    :param str level: The log level
    :param str msg: The message to log
    :returns: A pointer to the appropriate log method
    :rtype: *dict*

    """
    return _LEVELS[level](msg)


def _config_parse(config_path):
    """
    Parses the configuration file if exists. If not, raises an exception.

    :param str config_path: The absolute or relative path of the configuration file
    :returns: The configuration file parser
    :rtype: *dict*
    :raises Error: If no configuration file exists

    """
    if not os.path.isfile(config_path):
        raise _Exception('Configuration file not found')
    cfg = ConfigParser.ConfigParser()
    cfg.read(config_path)
    if not cfg:
        raise _Exception('Configuration file parsing failed')
    return cfg


def _get_master_ID(attributes, config):
    """
    Builds the master identifier of a dataset.

    :param dict attributes: The attributes auto-detected with DRS pattern
    :param dict config: The absolute or relative path of the configuration file
    :returns: The master ID with the version
    :rtype: *str*

    """
    dataset_ID = config.get(attributes['project'].lower(), 'dataset_ID')
    facets = re.split('\.|#', dataset_ID)
    for facet in facets:
        if facet == 'project':
            dataset_ID = dataset_ID.replace(facet, attributes[facet].lower())
        dataset_ID = dataset_ID.replace(facet, attributes[facet])
    return dataset_ID


def _check_facets(attributes, ctx):
    """
    Checks all attributes from path. Each attribute or facet is auto-detected using the DRS pattern (regex) and compared to its corresponding options declared into the configuration file.

    :param dict attributes: The attributes auto-detected with DRS pattern
    :param dict ctx: The processing context
    :raises Error: If an option of an attribute is not declared

    """
    for facet in attributes.keys():
        if not facet in ['project', 'filename', 'variable', 'root', 'version', 'ensemble']:
            options = ctx.cfg.get(attributes['project'].lower(), '{0}_options'.format(facet)).replace(" ", "").split(',')
            if not attributes[facet] in options:
                if not ctx.keep:
                    _rmdtemp(ctx)
                raise _Exception('"{0}" not in "{1}_options" for {2}'.format(attributes[facet], facet, file))


def _checksum(file, ctx):
    """
    Does the MD5 or SHA256 checksum by the Shell avoiding Python memory limits.

    :param str file: The full path of a file
    :param dict ctx: The processing context
    :raises Error: If the checksum fails

    """
    try:
        if ctx.checksum == 'SHA256':
            shell = os.popen("sha256sum {0} | awk -F ' ' '{{ print $1 }}'".format(file), 'r')
        elif ctx.checksum == 'MD5':
            shell = os.popen("md5sum {0} | awk -F ' ' '{{ print $1 }}'".format(file), 'r')
        else:
            if not ctx.keep:
                _rmdtemp(ctx)
            raise _Exception('Invalid checksum type: {0} instead of MD5 or SHA256'.format(ctx.checksum))
        return shell.readline()[:-1]
    except:
        if not ctx.keep:
            _rmdtemp(ctx)
        raise _Exception('Checksum failed for {0}'.format(file))


def _rmdtemp(ctx):
    """
    Removes the temporary directory and its content.

    :param dict ctx: The processing context

    """
    # This function occurs just before each exception raised to clean temporary directory
    if ctx.verbose:
        _log('warning', 'Delete temporary directory {0}'.format(ctx.dtemp))
    rmtree(ctx.dtemp)


def _yield_inputs(ctx):
    """
    Yields all files to process within tuples with the processing context. The file walking through the DRS tree follows symbolic links and ignores the "files" directories and "latest" symbolic links if ``--latest`` is None.

    :param dict ctx: The processing context
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


def _write(outfile, msg):
    """
    Writes in a mapfile using the ``with`` statement.

    :param str outfile: The mapfile full path
    :param str msg: The line to write

    """
    with open(outfile, 'a+') as f:
        f.write(msg)


def _wrapper(inputs):
    """
    Transparent wrapper for pool map.

    :param tuple inputs: A tuple with the file path and the processing context
    :returns: The :func:`_file_process` call
    :rtype: *callable*

    """
    return _file_process(inputs)


def _wrapper_keep_going(inputs):
    """
    Like :func:`_wrapper`, but returns ``None`` if an exception is encountered.

    :param tuple inputs: A tuple with the file path and the processing context
    :returns: The :func:`_file_process` call
    :rtype: *callable*

    """
    try:
        return _file_process(inputs)
    except:
        _log('warning', '{0} skipped'.format(inputs[0]))
        return None


def _counted(fct):
    """
    Decorator used to count all file process calls.

    :param callable fct: The function to monitor
    :returns: A wrapped function with a ``.called`` attribute
    :rtype: *callable*

    """
    @wraps(fct)  # Convenience decorator to keep the _file_process docstring
    def wrapper(*args, **kwargs):
        wrapper.called += 1
        return fct(*args, **kwargs)
    wrapper.called = 0
    wrapper.__name__ = fct.__name__
    return wrapper


@_counted
def _file_process(inputs):
    """
    _file_process(inputs)

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
        if not ctx.keep:
            _rmdtemp(ctx)
        raise _Exception('Matching failed for {0}'.format(file))
    else:
        # Control vocabulary of each facet
        _check_facets(attributes, ctx)
        # Deduce master ID from full path and --latest option
        if ctx.with_version:
            if ctx.latest:
                master_ID = _get_master_ID(attributes, ctx.cfg).replace(attributes['version'], os.path.basename(os.path.realpath(''.join(re.split(r'(latest)', file)[:-1])))[1:])
            else:
                master_ID = _get_master_ID(attributes, ctx.cfg).replace(attributes['version'], attributes['version'][1:])
        else:
            master_ID = _get_master_ID(attributes, ctx.cfg).replace('#' + attributes['version'], '')

        # Retrieve size and modification time
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)
        # Make the file checksum (MD5)
        if ctx.checksum:
            checksum = _checksum(file, ctx)
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
                _write(outfile, '{0} | {1} | {2} | mod_time={3} | checksum={4} | checksum_type={5}\n'.format(master_ID, file, size, str(mtime)+'.000000', checksum, ctx.checksum))
            else:
                _write(outfile, '{0} | {1} | {2} | mod_time={3}\n'.format(master_ID, file, size, str(mtime)+'.000000'))
            lock.release()
        except LockTimeout:
            if not ctx.keep:
                _rmdtemp(ctx)
            raise _Exception('Timeout exceeded for {0}'.format(file))
        _log('info', '{0} <-- {1}'.format(outmap, file))
        # Return mapfile name
        return outmap


def _process(ctx):
    """
    Main process that\:
     * Creates mapfiles output directory if necessary,
     * Instanciates threads pools,
     * Copies mapfile(s) to the output directory,
     * Removes the temporary directory and its contents.

    :param dict ctx: The processing context

    """
    # Create output directory if not exists
    if not os.path.isdir(ctx.outdir):
        if ctx.verbose:
            _log('warning', 'Create output directory: {0}'.format(ctx.outdir))
        os.makedirs(ctx.outdir)
    # Start threads pool over files list in supplied directory
    pool = ThreadPool(int(ctx.cfg.defaults()['threads_number']))
    # Return the list of generated mapfiles in temporary directory
    if ctx.keep:
        outmaps = filter(lambda m: m is not None, pool.map(_wrapper_keep_going, _yield_inputs(ctx)))
    else:
        outmaps = pool.map(_wrapper, _yield_inputs(ctx))
    # Close threads pool
    pool.close()
    pool.join()
    # Overwrite each existing mapfile in output directory
    for outmap in list(set(outmaps)):
        copy2(os.path.join(ctx.dtemp, outmap), ctx.outdir)
    # Remove temporary directory
    _rmdtemp(ctx)


def run(job):
    """
    Main entry point for SYNDA call.

    :param dict job: A dictionnary with the variable full path to scan

    """
    # Instanciate synda processing context
    ctx = _SyndaProcessingContext(job['full_path_variable'])
    _log('info', 'mapfile.py started (dataset_path = {0})'.format(ctx.directory))
    _process(ctx)
    _log('info', 'mapfile.py complete')


def main():
    """
    Main entry point for stand-alone call.

    """
    # Instanciate context initialization
    ctx = _ProcessingContext(_get_args())
    _log('info', '==> Scan started')
    _process(ctx)
    _log('info', '==> Scan completed ({0} files)'.format(_file_process.called))


# Main entry point for stand-alone call.
if __name__ == "__main__":
    main()
