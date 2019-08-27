# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Generates ESGF mapfiles upon a local ESGF node or not.

"""

import traceback
from collections import namedtuple
from multiprocessing import Pool

from lockfile import LockFile
from esgprep.constants import FRAMES, FINAL_FRAME, FINAL_STATUS
from esgprep import _STDOUT
from esgprep._utils.checksum import get_checksum
from esgprep.mapfile.constants import WORKING_EXTENSION, MAPFILE_EXTENSION, PROCESS_VARS, SPINNER_DESC
from esgprep.mapfile.context import ProcessingContext
from esgprep._utils.path import *
import signal

def build_mapfile_name(name, identifier, version):
    """
    Injects token values and returns mapfile name.

    """
    # Inject dataset name.
    if re.compile(r'{dataset_id}').search(name):
        name = re.sub(r'{dataset_id}', identifier, name)

    # Inject dataset version.
    if re.compile(r'{version}').search(name):
        if version:
            name = re.sub(r'{version}', version, name)
        else:
            name = re.sub(r'\.{version}', '', name)

    # Inject date.
    if re.compile(r'{date}').search(name):
        name = re.sub(r'{date}', datetime.now().strftime("%Y%d%m"), name)

    # Inject job id.
    if re.compile(r'{job_id}').search(name):
        name = re.sub(r'{job_id}', str(os.getpid()), name)

    # Return path object with working extension.
    return Path(name).with_suffix(WORKING_EXTENSION)


def build_mapfile_entry(dataset_name, dataset_version, ffp, size, optional_attrs):
    """
    Generate mapfile line corresponding to the source.

    """
    line = [dataset_name]
    if dataset_version:
        line = ['{}#{}'.format(dataset_name, dataset_version)]
    line.append(ffp)
    line.append(str(size))
    for k, v in optional_attrs.items():
        if v:
            line.append('{}={}'.format(k, v))
    return ' | '.join(line) + '\n'


def write(outpath, line):
    """
    Append line to a mapfile.
    It generates a lockfile to avoid that several threads write on the same file at the same time.
    A LockFile is acquired and released after writing. Acquiring LockFile is timeouted if it's locked by other thread.
    Each process adds one line to the appropriate mapfile.

    """
    lock = LockFile(outpath)
    with lock:
        with outpath.open('a+') as mapfile:
            mapfile.write(line)


def process(source):
    """
    Child process.
    Any error switches to the next child process.
    It does not stop the main process at all.

    """
    # Retrieve child processing content.
    assert 'pctx' in globals().keys()
    pctx = globals()['pctx']

    # Escape in case of error.
    try:
        # Get dataset version.
        dataset_version = get_version(source)

        # Build dataset identifier.
        # DRS terms are validated during this step.
        dataset_name = pctx.dataset_name
        if not pctx.dataset_name:
            dataset_name = dataset_id(source)

        # Check dataset identifier is not None.
        if not dataset_name:
            Print.debug('Dataset name is None')
            return False

        # Remove without ending version from dataset identifier.
        dataset_name = re.sub(r'\.latest|\.v[0-9]*$', '', dataset_name)

        # Build mapfile directory.
        outdir = Path(pctx.outdir).resolve(strict=False)
        try:
            outdir = outdir.joinpath(pctx.cfg.get(section='config:{}'.format(source.project),
                                                  option='mapfile_drs',
                                                  vars=source.terms))

        except:
            pass

        # Build mapfile name.
        outfile = build_mapfile_name(pctx.mapfile_name, dataset_name, dataset_version)

        # Build full mapfile path.
        outpath = outdir.joinpath(outfile)

        # Show command - Returns mapfile name only.
        if pctx.cmd == 'show' and pctx.basename:
            return outfile

        # Make command - Write mapfile.
        if pctx.cmd == 'make':

            # Create mapfile directory.
            try:
                os.makedirs(outdir)
            except OSError:
                pass

            # Gathers optional mapfile info into a dictionary.
            optional_attrs = dict()
            optional_attrs['mod_time'] = source.stat().st_mtime
            if not pctx.no_checksum:
                optional_attrs['checksum'] = get_checksum(str(source), pctx.checksum_type, pctx.checksums_from)
                optional_attrs['checksum_type'] = pctx.checksum_type.upper()
            optional_attrs['dataset_tech_notes'] = pctx.notes_url
            optional_attrs['dataset_tech_notes_title'] = pctx.notes_title

            # Generate the corresponding mapfile entry/line.
            if pctx.no_version:
                dataset_version = None
            line = build_mapfile_entry(dataset_name=dataset_name,
                                       dataset_version=dataset_version,
                                       ffp=str(source),
                                       size=source.stat().st_size,
                                       optional_attrs=optional_attrs)

            # Write line into mapfile.
            write(outpath, line)

            # Print success.
            msg = '{} <-- {}'.format(outfile.with_suffix(''), source)
            with pctx.lock:
                Print.success(msg)

        # Return mapfile path.
        return outpath

    except KeyboardInterrupt:

        # Lock error number.
        with pctx.lock:

            # Increase error counter.
            pctx.errors.value += 1

        raise

    # Catch known exception with its traceback.
    except Exception:

        # Lock error number.
        with pctx.lock:

            # Increase error counter.
            pctx.errors.value += 1

            # Format & print exception traceback.
            exc = traceback.format_exc().splitlines()
            msg = TAGS.SKIP + COLORS.HEADER(str(source)) + '\n'
            msg += '\n'.join(exc)
            Print.exception(msg, buffer=True)

        return None

    finally:

        # Lock progress value.
        with pctx.lock:

            # Increase progress counter.
            pctx.progress.value += 1

            # Clear previous print.
            msg = '\r{}'.format(' ' * pctx.msg_length.value)
            Print.progress(msg)

            # Print progress bar.
            msg = '\r{} {} {}'.format(COLORS.OKBLUE(SPINNER_DESC),
                                      FRAMES[pctx.progress.value % len(FRAMES)],
                                      source)
            Print.progress(msg)

            # Set new message length.
            pctx.msg_length.value = len(msg)


class Runner(object):

    def __init__(self, processes, init_args):

        # Initialize the pool.
        self.pool = None
        if processes != 1:
            self.pool = Pool(processes=processes,
                             initializer=self._initializer,
                             initargs=(init_args.keys(), init_args.values()))

        # Initialise context.
        else:
            self._initializer(init_args.keys(), init_args.values())

    @staticmethod
    def _initializer(keys, values):
        """
        Initialize process context by setting particular variables as global variables.

        """
        assert len(keys) == len(values)
        global pctx
        pctx = namedtuple("ChildProcess", keys)(*values)

    def _handle_sigterm(self, signum, frame):
        if self.pool:
            self.pool.terminate()
        os._exit(1)

    def run(self, sources):

        # Instantiate signal handler.
        sig_handler = signal.signal(signal.SIGTERM, self._handle_sigterm)

        # Instantiate pool of processes.
        if self.pool:

            # Instantiate pool iterator.
            processes = self.pool.imap(process, sources)

        # Sequential processing use basic map function.
        else:

            # Instantiate processes iterator.
            processes = map(process, sources)

        # Run processes & get the list of results.
        results = [x for x in processes]

        # Terminate pool in case of SIGTERM signal.
        signal.signal(signal.SIGTERM, sig_handler)

        # Close the pool.
        if self.pool:
            self.pool.close()
            self.pool.join()

        return results


def run(args):
    """
    Main process.

    """
    # Deal with 'quiet' option separately.
    # Turn off all output before creating ProcessingContext.
    # Turn it on only when needed.
    quiet = args.quiet if hasattr(args, 'quiet') else False
    if quiet:
        _STDOUT.stdout_off()

    # Instantiate processing context
    with ProcessingContext(args) as ctx:

        # Shared processing context between child processes as dictionary.
        cctx = {name: getattr(ctx, name) for name in PROCESS_VARS}

        # Instantiate the runner.
        r = Runner(ctx.processes, init_args=cctx)

        # Get runner results.
        results = r.run(ctx.sources)

        # Final print.
        msg = '\r{}'.format(' ' * ctx.msg_length.value)
        Print.progress(msg)
        msg = '\r{} {} {}\n'.format(COLORS.OKBLUE(SPINNER_DESC), FINAL_FRAME, FINAL_STATUS)
        Print.progress(msg)

        # Flush buffer.
        Print.flush()

        # Get number of sources (without "Completed" step).
        ctx.nbsources = ctx.progress.value

        # Number of success (excluding errors/skipped files).
        ctx.success = len(list(filter(None, results)))

        # Number of generated mapfiles.
        ctx.nbmap = len(list(filter(None, set(results))))

        # Evaluate the list of results triggering action.
        if any(results):

            # Iterate over written mapfiles.
            for mapfile in filter(None, set(results)):

                # Count number of expected lines.
                expected_lines = results.count(mapfile)

                # Count number of lines in written mapfile.
                with open(mapfile) as f:
                    lines = len(f.readlines())

                # Sanity check that the mapfile has the appropriate lines number.
                assert lines == expected_lines, "Wrong lines number : {}, {} expected - {}".format(lines,
                                                                                                   expected_lines,
                                                                                                   mapfile)

                # Set mapfile final extension.
                result = mapfile.with_suffix(MAPFILE_EXTENSION)

                # Print mapfiles to be generated.
                if ctx.cmd == 'show':

                    # Disable quiet mode to print results.
                    if quiet:
                        _STDOUT.stdout_on()
                        print(str(result))
                        _STDOUT.stdout_off()
                    else:
                        Print.result(str(result))

                # Do mapfile renaming.
                elif ctx.cmd == 'make':

                    # A final mapfile is silently overwritten if already exists
                    mapfile.rename(result)

    # Evaluate errors & exit with corresponding return code.
    if ctx.errors.value > 0:
        sys.exit(ctx.errors.value)
