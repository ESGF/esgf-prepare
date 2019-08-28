# -*- coding: utf-8 -*-

"""
.. module:: esgprep.fetchini
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import traceback

from esgprep._utils.github import *
from esgprep.fetchini.context import ProcessingContext


def make_outdir(root):
    """
    Builds the INI output directory.

    """
    # Retrieve root directory from command-line.
    outdir = root

    # If submitted root directory does not exist.
    if not os.path.isdir(outdir):

        # Try to make it.
        try:
            os.makedirs(outdir)
            Print.warning('{} created'.format(outdir))

        # Error rollbacks to the current working directory (default).
        except OSError as e:
            msg = 'Cannot use "{}" (OSError {}: {}) -- '.format(outdir, e.errno, e.strerror)
            msg += 'Use "{}" instead.'.format(os.getcwd())
            Print.warning(msg)
            outdir = os.path.join(os.getcwd(), 'ini')
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
                Print.warning('{} created'.format(outdir))

    # Return output directory.
    return outdir


def run(args):
    """
    Main process.

    """
    # Instantiate processing context
    with ProcessingContext(args) as ctx:

        # Make output directory
        outdir = make_outdir(root=ctx.config_dir)

        # Reset counter
        progress = 0

        # Iterates over files to fetch.
        for f, info in ctx.files.items():

            # Escape in case of error.
            try:

                # Set output full path of the file.
                outfile = os.path.join(outdir, f)

                # Get remote checksum infos.
                sha = info['sha']

                # Get remote download URL.
                download_url = info['download_url']

                # Fetch GitHub file
                fetch(url=download_url,
                      outfile=outfile,
                      auth=ctx.auth,
                      sha=sha,
                      keep=ctx.keep,
                      overwrite=ctx.overwrite,
                      backup_mode=ctx.backup_mode)

            # Catch unknown exception into error log instead of stop the process.
            except KeyboardInterrupt:
                raise

            # Catch known exception with its traceback.
            except Exception:
                download_url = info['download_url']
                exc = traceback.format_exc().splitlines()
                msg = TAGS.FAIL + COLORS.HEADER(download_url) + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)
                ctx.error = True

            # Print progress.
            finally:
                progress += 1
                percentage = int(progress * 100 / ctx.nfiles)
                msg = COLORS.OKBLUE('\rFetching project(s) config: ')
                msg += '{}% | {}/{} files'.format(percentage, progress, ctx.nfiles)
                Print.progress(msg)

        Print.progress('\n')

    # Flush buffer.
    Print.flush()

    # Evaluate errors & exit with corresponding return code.
    if ctx.error:
        sys.exit(1)
