# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import traceback
from collections import namedtuple

from esgprep._utils.github import *
from esgprep.fetchcv.constants import *
from esgprep.fetchcv.context import ProcessingContext
from multiprocessing import Pool

def initializer(keys, values):
    """
    Initialize process context by setting particular variables as global variables.

    """
    assert len(keys) == len(values)
    global pctx
    pctx = namedtuple("ChildProcess", keys)(*values)


def process(info):
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

        # Get type. Default is 'file'.
        blob = (info['type'] == 'blob')

        # Get destination subdirectory.
        path = info['path']

        # Set output full path of the file.
        outfile = os.path.join(pctx.outdir, path)

        # Make directory if not exists.
        try:
            os.makedirs(os.path.dirname(outfile))
            Print.debug('{} created'.format(os.path.dirname(outfile)))
        except OSError:
            pass

        # Get remote checksum infos.
        sha = info['sha']

        # Get remote download URL.
        download_url = info['url'] if blob else info['download_url']
        # Fetch GitHub file
        fetch(url=download_url,
              blob=blob,
              outfile=outfile,
              auth=pctx.auth,
              sha=sha,
              keep=pctx.keep,
              overwrite=pctx.overwrite,
              backup_mode=pctx.backup_mode)

    # Catch unknown exception into error log instead of stop the process.
    except KeyboardInterrupt:

        # Set error to True.
        pctx.error.value = True

        raise

    # Catch known exception with its traceback.
    except Exception:

        # Get download url.
        blob = (info['type'] == 'blob')
        download_url = info['url'] if blob else info['download_url']

        # Format & print exception traceback.
        exc = traceback.format_exc().splitlines()
        msg = TAGS.FAIL + COLORS.HEADER(download_url) + '\n'
        msg += '\n'.join(exc)
        with pctx.lock:
            Print.exception(msg, buffer=True)

        # Set error to True.
        pctx.error.value = True

    # Print progress.
    finally:

        # Lock progress value.
        with pctx.lock:

            # Increase progress counter.
            pctx.progress.value += 1

            # Compute progress percentage.
            percentage = int(pctx.progress.value * 100 / pctx.nfiles)

            # Print progress bar.
            msg = COLORS.OKBLUE('\rFetching CV: ')
            msg += '{}% | {}/{} files'.format(percentage, pctx.progress.value, pctx.nfiles)
            Print.progress(msg)


def run(args):
    """
    Main process.

    """
    # Instantiate processing context
    with ProcessingContext(args) as ctx:

        # Shared processing context between child processes as dictionary.
        cctx = {name: getattr(ctx, name) for name in PROCESS_VARS}

        # Instantiate pool of processes.
        if ctx.use_pool:

            # Initialize the pool.
            pool = Pool(processes=ctx.processes, initializer=initializer, initargs=(cctx.keys(), cctx.values()))

            # Instantiate pool iterator.
            processes = pool.imap(process, ctx.files)

        # Sequential processing use basic map function.
        else:

            # Initialise context.
            initializer(cctx.keys(), cctx.values())

            # Instantiate processes iterator.
            processes = map(process, ctx.files)

        # Run processes & get the list of results.
        _ = [x for x in processes]

        Print.progress('\n')

    # Flush buffer.
    Print.flush()

    # Evaluate errors & exit with corresponding return code.
    if ctx.error:
        sys.exit(1)
