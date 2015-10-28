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
from esgmapfilesutils import init_logging, check_directory, config_parse, split_line, split_record, split_map
from multiprocessing.dummy import Pool as ThreadPool
from functools import wraps
from argparse import RawTextHelpFormatter
from lockfile import LockFile, LockTimeout, LockFailed
from tempfile import mkdtemp
from datetime import datetime
from shutil import copy2, rmtree

# Program version
__version__ = '{0} {1}-{2}-{3}'.format('v0.5.3', '2015', '10', '05')


class ProcessingContext(object):
    """
    Encapsulates the following processing context/information for main process:

    +------------------------+-------------+-------------------------------------------+
    | Attribute              | Type        | Description                               |
    +========================+=============+===========================================+
    | *self*.directory       | *list*      | Paths to scan                             |
    +------------------------+-------------+-------------------------------------------+
    | *self*.latest          | *boolean*   | True if latest symlink                    |
    +------------------------+-------------+-------------------------------------------+
    | *self*.outdir          | *str*       | Output directory                          |
    +------------------------+-------------+-------------------------------------------+
    | *self*.notes_url       | *str*       | Dataset technical notes URL               |
    +------------------------+-------------+-------------------------------------------+
    | *self*.notes_title     | *str*       | Dataset technical notes title             |
    +------------------------+-------------+-------------------------------------------+
    | *self*.verbose         | *boolean*   | True if verbose mode                      |
    +------------------------+-------------+-------------------------------------------+
    | *self*.all_version     | *boolean*   | True to scan all versions                 |
    +------------------------+-------------+-------------------------------------------+
    | *self*.version         | *str*       | Version to scan                           |
    +------------------------+-------------+-------------------------------------------+
    | *self*.no_version      | *boolean*   | True to not include version in dataset ID |
    +------------------------+-------------+-------------------------------------------+
    | *self*.project         | *str*       | Project                                   |
    +------------------------+-------------+-------------------------------------------+
    | *self*.project_section | *str*       | Project-Section (project:<project>)       |
    +------------------------+-------------+-------------------------------------------+
    | *self*.dataset         | *boolean*   | True if one mapfile per dataset           |
    +------------------------+-------------+-------------------------------------------+
    | *self*.checksum_type   | *str*       | Checksum Type, defaults: SHA256           |
    +------------------------+-------------+-------------------------------------------+
    | *self*.checksum_client | *str*       | Checksum Client, defaults: sha256sum      |
    +------------------------+-------------+-------------------------------------------+
    | *self*.outmap          | *str*       | Mapfile output name                       |
    +------------------------+-------------+-------------------------------------------+
    | *self*.cfg             | *callable*  | Configuration file parser                 |
    +------------------------+-------------+-------------------------------------------+
    | *self*.pattern         | *re object* | DRS regex pattern                         |
    +------------------------+-------------+-------------------------------------------+
    | *self*.ini_pat         | *re object* | Pattern matching %(name)s                 |
    +------------------------+-------------+-------------------------------------------+
    | *self*.dtemp           | *str*       | Directory of temporary files              |
    +------------------------+-------------+-------------------------------------------+

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
        self.latest = args.latest_symlink
        self.outdir = args.outdir
        self.notes_title = args.tech_notes_title
        self.notes_url = args.tech_notes_url
        self.no_version = args.no_version
        self.all = args.all_versions
        if self.all:
            self.no_version = False
        self.version = args.version
        self.dataset = args.per_dataset
        self.filter = args.filter
        self.cfg = config_parse(args.init)
        
        self.project = args.project
        self.project_section = 'project:' + args.project
        if not self.project_section in self.cfg.sections():
            raise Exception('No section in configuration file corresponds to "{0}" project. Supported projects are {1}.'.format(args.project, self.cfg.sections()))
        
        if args.no_checksum:
            self.checksum_client, self.checksum_type = None
        elif self.cfg.has_option('DEFAULT', 'checksum'):
            self.checksum_client, self.checksum_type = split_line(self.cfg.defaults()['checksum'])
        else: # use SHA256 as default
            self.checksum_client, self.checksum_type = 'sha256sum', 'SHA256'
            
        # Pattern matching %(name)s from esg.ini
        self.ini_pat = re.compile(r'%\(([^()]*)\)s')
        
        # modify directory_format to python-re compatible version
        directory_format = self.cfg.get(self.project_section, 'directory_format', raw=True)
        
        pat = directory_format.strip()
        pat2 = pat.replace('\.','__ESCAPE_DOT__')
        pat3 = pat2.replace('.', r'\.')
        pat4 = pat3.replace('__ESCAPE_DOT__', r'\.')
        pat5 = re.sub(self.ini_pat, r'(?P<\1>[\w.-]+)', pat4)
        pat_fin = pat5+'/(?P<filename>[\w.-]+\.nc)'
        self.pattern = re.compile(pat_fin)
        
        self.dtemp = mkdtemp()

def get_args(job):
    """
    Returns parsed command-line arguments. See ``esg_mapfiles -h`` for full description.
    A ``job`` dictionnary can be used as developper's entry point to overload the parser.

    :param dict job: Optionnal dictionnary instead of command-line arguments.
    :returns: The corresponding ``argparse`` Namespace

    """
    parser = argparse.ArgumentParser(
        description="""Generates ESG-F mapfiles upon local ESG-F datanode or not.\n\n
            Exit status:\n
            [0]: Successful scanning of all files encountered,\n
            [1]: No valid data or files have been found and no mapfile was produced,\n
            [2]: A mapfile was produced but some files were skipped.""",
        formatter_class=RawTextHelpFormatter,
        add_help=False,
        epilog="""Developed by Levavasseur, G. (CNRS/IPSL)""")
    parser.add_argument(
        'directory',
        type=str,
        nargs='+',
        help="""One or more directories to recursively scan. Unix wildcards are allowed.""")
    parser.add_argument(
        '-p', '--project',
        type=str,
        required=True,
        help="""Required project name corresponding to a section of the configuration file.\n\n""")
    parser.add_argument(
        '-i', '--init',
        type=str,
        default='{0}/config.ini'.format(os.path.dirname(os.path.abspath(__file__))),
        help="""Path of configuration INI file\n(default is {0}/config.ini).\n\n""".format(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument(
        '--mapfile',
        type=str,
        default='mapfile_{0}.txt'.format(datetime.now().strftime("%Y%m%d-%I%M%S-%p")),
        help="""Output mapfile name. Only used without --per-dataset option\n(default is mapfile_YYYYDDMM-HHMMSS-[AP]M.txt).\n\n""")
    parser.add_argument(
        '--outdir',
        type=str,
        default=os.getcwd(),
        help="""Mapfile(s) output directory\n(default is working directory).\n\n""")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--all-versions',
        action='store_true',
        default=False,
        help="""Generates mapfile(s) with all versions found in the directory\nrecursively scanned (default is to pick up only the latest one).\nIt disables --no-version.\n\n""")
    group.add_argument(
        '--version',
        type=str,
        help="""Generates mapfile(s) scanning datasets\nwith the corresponding version number only (e.g., 20151023).\nIt takes priority over --all-versions.\n\n""")
    group.add_argument(
        '--latest-symlink',
        action='store_true',
        default=False,
        help="""Generates mapfiles following latest symlinks only.\n\n""")
    parser.add_argument(
        '--per-dataset',
        action='store_true',
        default=False,
        help="""Produces ONE mapfile PER dataset. It takes priority over --mapfile.\n\n""")
    parser.add_argument(
        '--no-version',
        action='store_true',
        default=False,
        help="""Includes DRS version into dataset ID (ESGF 2.x compatibility).\n\n""")
    parser.add_argument(
        '--no-checksum',
        action='store_true',
        default=False,
        help="""Does not include files checksums into the mapfile(s).\n\n""")
    parser.add_argument(
        '--filter',
        type=str,
        default=".*\.nc$",
        help="""Filter files matching the regular expression (default is ".*\.nc$").\nRegular expression syntax is defined by the Python re module.\n\n""")
    parser.add_argument(
        '--tech-notes-url',
        type=str,
        help="""URL of the technical notes to be associated with each dataset.\n\n""")
    parser.add_argument(
        '--tech-notes-title',
        type=str,
        help="""Tech notes title for display..\n\n""")
    parser.add_argument(
        '-h', '--help',
        action="help",
        help="""Show this help message and exit.\n\n""")
    parser.add_argument(
        '-l', '--logdir',
        type=str,
        const=os.getcwd(),
        nargs='?',
        help="""Logfile directory (default is working directory).\nIf not, standard output is used.\n\n""")
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
        return parser.parse_args([re.sub('v[0-9]*$', 'latest', os.path.normpath(job['full_path_variable'])), '-p', 'cmip5', '-c', '/home/esg-user/mapfile.ini', '-o', '/home/esg-user/mapfiles/pending/', '-l', 'synda_logger', '--per-dataset', '--latest-symlink', '-v'])


def get_master_ID(attributes, ctx):
    """
    Builds the master identifier of a dataset.

    :param dict attributes: The attributes auto-detected with DRS pattern
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: The master ID with the version
    :rtype: *str*

    """
    dataset_id_templ = ctx.cfg.get(ctx.project_section, 'dataset_id', 1)
    idfields = re.findall(ctx.ini_pat, dataset_id_templ)
    for idfield in idfields:
        if idfield not in attributes:
            attributes = get_attr_from_map(idfield, attributes, ctx)
    if 'projects' in attributes:
        attributes['project'] = attributes['project'].lower()  # Do the lower case need to be enforced? Waiting for esgf-devel decision.
    dataset_ID = ctx.cfg.get(ctx.project_section, 'dataset_id', 0, attributes)
    return dataset_ID


def get_attr_from_map(idfield, attributes, ctx):
    """
    Get attribute value from esg.ini maptable and add to attributes dictionary.
    
    :param str idfield: The attribute to find the value for
    :param dict attributes: The attributes auto-detected with DRS pattern
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: dict of attributes
    
    """
    map_option = '{0}_map'.format(idfield)
    if ctx.cfg.has_option(ctx.project_section, map_option):
        from_keys, to_keys, value_map = split_map(ctx.cfg.get(ctx.project_section, map_option))
        from_values = tuple(attributes[key] for key in from_keys)
        to_values = value_map[from_values]
        attributes.update(dict(zip(to_keys, to_values)))
    return attributes


def check_facets(attributes, ctx, file):
    """
    Checks all attributes from path.
    Each attribute or facet is auto-detected using the DRS pattern (regex) and compared to its corresponding options declared into the configuration file.

    :param dict attributes: The attributes auto-detected with DRS pattern
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :raises Error: If an option of an attribute is not declared

    """
    # get all maps in configuration file
    maps = None
    if ctx.cfg.has_option(ctx.project_section, 'maps'):
        maps = ctx.cfg.get(ctx.project_section, 'maps').replace(" ", "").split(',')
        
    for facet in attributes.keys():
        if not facet in ['project', 'filename', 'variable', 'root', 'version', 'ensemble']:
            if ctx.cfg.has_option(ctx.project_section, '{0}_options'.format(facet)):
                # experiment_options follows the form "<project> | <experiment> | <long_name>" => needs special treatment
                if facet == 'experiment':
                    experiment_options = split_record(ctx.cfg.get(ctx.project_section, '{0}_options'.format(facet)))
                    options = zip(*experiment_options)[1]
                else:
                    options = ctx.cfg.get(ctx.project_section, '{0}_options'.format(facet)).replace(" ", "").split(',')
                if not attributes[facet] in options:
                    msg = '"{0}" is missing in "{1}_options" of the "{2}" section from the configuration file to properly process {3}'.format(attributes[facet], facet, ctx.project_section, file)
                    logging.warning(msg)
                    raise Exception(msg)
            elif '{0}_map' not in maps:  # TODO model_options not in esg.ini but in esgcet_models_table
                msg = 'No option for facet "{0}" in the configuration file'.format(facet)
                logging.warning(msg)                


def checksum(file, checksum_type, checksum_client):
    """
    Does the checksum by the Shell avoiding Python memory limits.

    :param str file: The full path of a file
    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
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
    Yields all files to process within tuples with the processing context. The file walking through the DRS tree follows the latest version of each dataset. This behavior is modifed using:
     * ``--all-versions`` flag, to pick up all versions,
     * ``--version <version_number>`` argument, to pick up a specified version,
     * ``--latest-symlink`` flag, to pick up the version pointed by the latest symlink (if exists).

    :param dict ctx: The processing context (as a :func:`ProcessingContext` class instance)
    :returns: Attach the processing context to a file to process as an iterator of tuples
    :rtype: *iter*

    """
    for directory in ctx.directory:
        for root, dirs, files in os.walk(directory, followlinks=True):
            if ctx.latest:
                if '/latest/' in root:
                    for file in files:
                        if os.path.isfile(os.path.join(root, file)) and re.match(ctx.filter, file) is not None:
                            yield os.path.join(root, file), ctx
            elif ctx.version:
                if re.compile('/v' + ctx.version + '/').search(root):
                    for file in files:
                        if os.path.isfile(os.path.join(root, file)) and re.match(ctx.filter, file) is not None:
                            yield os.path.join(root, file), ctx
            elif ctx.all:
                if re.compile('/v[0-9]*/').search(root):
                    for file in files:
                        if os.path.isfile(os.path.join(root, file)) and re.match(ctx.filter, file) is not None:
                            yield os.path.join(root, file), ctx
            elif re.compile('/v[0-9]*/').search(root):
                versions = filter(lambda i: re.compile('v[0-9]').search(i), os.listdir(re.split('/v[0-9]*/', root)[0]))
                if re.compile('/' + sorted(versions)[-1] + '/').search(root):
                    for file in files:
                        if os.path.isfile(os.path.join(root, file)) and re.match(ctx.filter, file) is not None:
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
        if not 'project' in attributes:
            attributes['project'] = ctx.project
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
        master_ID = get_master_ID(attributes, ctx)
        
        # add version number to master_ID
        if not ctx.no_version:
            if ctx.latest:
                master_ID = '{0}#{1}'.format(master_ID, os.path.basename(os.path.realpath(''.join(re.split(r'(latest)', file)[:-1])))[1:])
            else:
                master_ID = '{0}#{1}'.format(master_ID, attributes['version'][1:])

        # Retrieve size and modification time
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)
        # Make the file checksum (MD5)
        if ctx.checksum_client:
            csum = checksum(file, ctx.checksum_type, ctx.checksum_client)
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
            line = [master_ID]
            line.append(file)
            line.append('mod_time='+str(mtime)+'.000000')
            if ctx.checksum_type:
                line.append('checksum='+csum)
                line.append('checksum_type='+ctx.checksum_type)
            if ctx.notes_url:
                line.append('dataset_tech_notes='+ctx.notes_url)
            if ctx.notes_title:
                line.append('dataset_tech_notes_title='+ctx.notes_title)
            lock.acquire(timeout=int(ctx.cfg.defaults()['lockfile_timeout']))
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
        logging.warning('==> Scan completed ({0} file(s) skipped)'.format(len(outmaps_all) - len(outmaps)))
        sys.exit(2)


# Main entry point for stand-alone call.
if __name__ == "__main__":
    run()
