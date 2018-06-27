#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import traceback

from context import ProcessingContext
from esgprep.utils.github import *


def make_outdir(root):
    """
    Build the output directory as follows:

    :param str root: The root directory

    """
    outdir = root
    # If directory does not already exist
    if not os.path.isdir(outdir):
        try:
            os.makedirs(outdir)
            Print.warning('{} created'.format(outdir))
        except OSError as e:
            # If default tables directory does not exists and without write access
            msg = 'Cannot use "{}" (OSError {}: {}) -- '.format(outdir, e.errno, e.strerror)
            msg += 'Use "{}" instead.'.format(os.getcwd())
            Print.warning(msg)
            outdir = os.path.join(os.getcwd(), 'ini')
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
                Print.warning('{} created'.format(outdir))
    return outdir


def run(args):
    """
    Main process that:

     * Decide to fetch or not depending on file presence/absence and command-line arguments,
     * Gets the GitHub file content from full API URL,
     * Backups old file if desired,
     * Writes response into INI file.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Instantiate processing context manager
    with ProcessingContext(args) as ctx:
        # Make output directory
        outdir = make_outdir(root=ctx.config_dir)
        # Counter
        progress = 0
        for f, info in ctx.files.items():
            try:
                # Set output file full path
                outfile = os.path.join(outdir, f)
                # Get checksum
                download_url = info['download_url']
                sha = info['sha']
                # Get GitHub file
                fetch(url=download_url,
                      outfile=outfile,
                      auth=ctx.auth,
                      sha=sha,
                      keep=ctx.keep,
                      overwrite=ctx.overwrite,
                      backup_mode=ctx.backup_mode)
            except KeyboardInterrupt:
                raise
            except Exception:
                download_url = info['download_url']
                exc = traceback.format_exc().splitlines()
                msg = TAGS.FAIL + COLORS.HEADER(download_url) + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)
                ctx.error = True
            finally:
                progress += 1
                percentage = int(progress * 100 / ctx.nfiles)
                msg = COLORS.OKBLUE('\rFetching project(s) config: ')
                msg += '{}% | {}/{} files'.format(percentage, progress, ctx.nfiles)
                Print.progress(msg)
        Print.progress('\n')
    # Flush buffer
    Print.flush()
    # Evaluate errors and exit with appropriated return code
    if ctx.error:
        sys.exit(1)
