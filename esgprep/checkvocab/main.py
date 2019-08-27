# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Checks DRS vocabulary against configuration files.

"""

import traceback
from collections import namedtuple
from multiprocessing import Pool
import signal
from esgprep.constants import FRAMES, FINAL_FRAME, FINAL_STATUS
from esgprep.checkvocab.constants import *
from esgprep.checkvocab.context import ProcessingContext
from esgprep._utils.print import *

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

        if pctx.dataset_id or pctx.dataset_list:

            from esgprep._utils.dataset import get_terms

        elif pctx.directory:

            from esgprep._utils.path import get_terms

        else:

            from  esgprep._utils.ncfile import get_terms

        # Validate source against CV.
        if get_terms(source):

            # Print success.
            with pctx.lock:
                Print.success(str(source))

            return 1

        else:

            # Print failure.
            with pctx.lock:
                Print.error(str(source))

            return 0

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
            msg = '\r{} {} {}'.format(COLORS.OKBLUE('Checking input data against CV'),
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

        # Flush buffer
        Print.flush()

        # Get number of sources (without "Completed" step).
        ctx.nbsources = ctx.progress.value

        # Number of success (excluding errors/skipped files).
        ctx.success = sum(filter(None, results))

    # Evaluate errors & exit with corresponding return code.
    if ctx.errors.value > 0:
        sys.exit(ctx.errors.value)