#!/usr/bin/env python
"""
   :platform: Unix
   :synopsis: Build ESG-F mapfiles without esgscan_directory upon local ESG-F datanode.
   :members:

"""

#.. moduleauthor:: Levavasseur, G. <glipsl@ipsl.jussieu.fr>

# Module imports
import os
import re
import argparse
import ConfigParser
import logging
from multiprocessing.dummy import Pool as ThreadPool
from argparse import RawTextHelpFormatter
from lockfile import LockFile, LockTimeout
from datetime import datetime
from tempfile import mkdtemp
from shutil import copy2, rmtree


# Program version
__version__ = '{0} {1}-{2}-{3}'.format('v0.4', '2015', '03', '27')

# Log levels
_LEVELS = {'debug': logging.error,
           'info': logging.info,
           'warning': logging.warning,
           'error': logging.error,
           'critical': logging.critical,
           'exception': logging.exception}


class _ProcessingContext(object):
    """Encapsulate processing context information for main process."""
    def __init__(self, args):
        _init_logging(args.logdir)
        self.directory = _check_directory(args.directory)
        self.outdir = args.outdir
        self.verbose = args.verbose
        self.keep = args.keep_going
        self.project = args.project
        self.dataset = args.per_dataset
        self.outmap = args.mapfile
        self.cfg = _config_parse(args.config)
        self.pattern = re.compile(self.cfg.get(self.project, 'directory_format'))
        self.dtemp = mkdtemp()


class _SyndaProcessingContext(object):
    """Encapsulate processing context information for synda call."""
    def __init__(self, full_path_variable):
        #_init_logging(args.logdir) # Logger initiates by synda worker
        # "merge" product is mandatory through the configuration file used by synda
        # synda submit non-latest path to translate
        self.directory = _check_directory(re.sub('v[0-9]*$', 'latest', os.path.normpath(full_path_variable)))
        self.outdir = '/home/esg-user/mapfiles/pending/'
        self.verbose = True
        self.keep = True
        self.project = 'cmip5'
        self.dataset = True
        self.outmap = False
        self.cfg = _config_parse('/home/esg-user/mapfiles/mapfile.ini')
        self.pattern = re.compile(self.cfg.get(self.project, 'directory_format'))
        self.dtemp = mkdtemp()


class _Exception(Exception):
    """Exception type to log encountered error."""
    def __init__(self, msg=''):
        self.msg = msg

    def __str__(self):
        print
        _log('error', self.msg)


def _get_args():
    """
    Returns parsed command line arguments.

    :param numerateur: le numerateur de la division
    :type numerateur: int
    :param denominateur: le denominateur de la division
    :type denominateur: int
    :return: la valeur entiere de la division
    :rtype: int
    """
    parser = argparse.ArgumentParser(
        description="""Build ESG-F mapfiles upon local ESG-F datanode bypassing esgscan_directory\ncommand-line.""",
        formatter_class=RawTextHelpFormatter,
        add_help=False,
        epilog="""Developed by Levavasseur, G. (CNRS/IPSL)""")
    parser.add_argument(
        'directory',
        type=str,
        nargs='?',
        help='Directory to recursively scan')
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
        default='{0}/esg_mapfiles.ini'.format(os.getcwd()),
        help="""Path of configuration INI file\n(default is '{workdir}/esg_mapfiles.ini').\n\n""")
    parser.add_argument(
        '-o', '--outdir',
        type=str,
        default=os.getcwd(),
        help="""Mapfile(s) output directory\n(default is working directory).\n\n""")
    parser.add_argument(
        '-l', '--logdir',
        type=str,
        nargs='?',
        const=os.getcwd(),
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
        help="""Produce ONE mapfile PER dataset.\n\n""")
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


def _check_directory(path):
    """Checks if supplied directroy exists """
    directory = os.path.normpath(path)
    if not os.path.isdir(directory):
        raise _Exception('No such directory: {0}'.format(directory))
    return directory


def _get_unique_logfile(logdir):
    """Get unique logfile name."""
    logfile = 'esg_mapfile-{0}-{1}.log'.format(datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())
    return os.path.join(logdir, logfile)


def _init_logging(logdir):
    """Creates logfile or formates console message"""
    if logdir:
        if not os.path.exists(logdir):
            os.mkdir(logdir)
        logging.basicConfig(filename=_get_unique_logfile(logdir),
                            level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y/%m/%d %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(message)s')


def _log(level, msg):
    """Pointer to level logs."""
    return _LEVELS[level](msg)


def _config_parse(config_path):
    """Parses configuration file if exists."""
    if not os.path.isfile(config_path):
        raise _Exception('Configuration file not found')
    cfg = ConfigParser.ConfigParser()
    cfg.read(config_path)
    # No parsing error just empty list
    if not cfg:
        raise _Exception('Configuration file parsing failed')
    return cfg


def _get_file_list(directory):
    """Yields file walinking DRS tree ignoring 'files' or 'latest' directories."""
    for root, dirs, files in os.walk(directory):
        if 'files' in dirs:
            dirs.remove('files')
        if 'latest' in dirs:
            dirs.remove('latest')
        for file in files:
            yield os.path.join(root, file)


def _get_master_ID(attributes, config):
    """Returns master ID and version from dataset path."""
    facets = config.get(attributes['project'].lower(), 'dataset_ID').replace(" ", "").split(',')
    ID = [attributes['project'].lower()]
    for facet in facets:
        ID.append(attributes[facet])
    return '.'.join(ID)


def _get_options(section, facet, config):
    """Get facet options of a section as list."""
    return config.get(section, '{0}_options'.format(facet)).replace(" ", "").split(',')


def _check_facets(attributes, ctx):
    """Check all attribute regarding controlled vocabulary."""
    for facet in attributes.keys():
        if not facet in ['project', 'filename', 'variable', 'root', 'version', 'ensemble']:
            options = _get_options(attributes['project'].lower(), facet, ctx.cfg)
            if not attributes[facet] in options:
                if not ctx.keep:
                    _rmdtemp(ctx)
                raise _Exception('"{0}" not in "{1}_options" for {2}'.format(attributes[facet], facet, file))


def _checksum(file, ctx):
    """Do MD5 checksum by Shell"""
    # Here 'md5sum' from Unix filesystem is used avoiding python memory limits
    try:
        shell = os.popen("md5sum {0} | awk -F ' ' '{{ print $1 }}'".format(file), 'r')
        return shell.readline()[:-1]
    except:
        if not ctx.keep:
            _rmdtemp(ctx)
        raise _Exception('Checksum failed for {0}'.format(file))


def _rmdtemp(ctx):
    """Remove temporary directory and its content."""
    # This function occurs juste before each exception raised to clean temporary directory
    if ctx.verbose:
        _log('warning', 'Delete temporary directory {0}'.format(ctx.dtemp))
    rmtree(ctx.dtemp)


def _yield_inputs(ctx):
    """Generator yielding set of parameters to be passed to file processing."""
    for file in _get_file_list(ctx.directory):
        yield file, ctx


def _write(outfile, msg):
    """Writes in mapfile."""
    with open(outfile, 'a+') as f:
        f.write(msg)


def _wrapper(inputs):
    """Wrapper for pool map multiple arguments wrapper."""
    return _process(inputs)


def _wrapper_keep_going(inputs):
    """Like _wrapper, but returns None if exception encountered"""
    try:
        return _process(inputs)
    except:
        _log('warning', '{0} skipped'.format(inputs[0]))
        return None


def _process(inputs):
    """File processing."""
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
        # Deduce master ID from fulle path
        master_ID = _get_master_ID(attributes, ctx.cfg)
        # Retrieve size and modification time
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)
        # Make the file checksum (MD5)
        checksum = _checksum(file, ctx)
        # Build mapfile name if one per dataset, or read the supplied name instead
        if ctx.dataset:
            outmap = '{0}.{1}'.format(master_ID, attributes['version'])
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
            _write(outfile, '{0} | {1} | {2} | mod_time={3} | checksum={4} | checksum_type={5}\n'.format(master_ID, file, size, str(mtime)+'.000000', checksum, 'MD5'))
            lock.release()
        except LockTimeout:
            if not ctx.keep:
                _rmdtemp(ctx)
            raise _Exception('Timeout exceeded for {0}'.format(file))
        _log('info', '{0} <-- {1}'.format(outmap, file))
        # Return mapfile name
        return outmap


def main(ctx):
    """Main process."""
    # Create output directory if not exists
    if not os.path.isdir(ctx.outdir):
        if ctx.verbose:
            _log('warning', 'Create output directory: {0}'.format(ctx.outdir))
        os.mkdir(ctx.outdir)
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
    """Main entry point for call by synda."""
    # Instanciate synda processing context
    ctx = _SyndaProcessingContext(job['full_path_variable'])
    _log('info', 'mapfile.py started (dataset_path = {0})'.format(ctx.directory))
    main(ctx)
    _log('info', 'mapfile.py complete')


# Main entry point for stand-alone call.
if __name__ == "__main__":
    # Instanciate context initialization
    ctx = _ProcessingContext(_get_args())
    _log('info', 'Scan started for {0}'.format(ctx.directory))
    main(ctx)
    _log('info', 'Scan completed for {0}'.format(ctx.directory))
