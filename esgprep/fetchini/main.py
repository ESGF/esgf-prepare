#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import traceback

from constants import *
from context import ProcessingContext
from esgprep.utils.github import *
from esgprep.utils.custom_print import *
from esgprep.utils.misc import make_outdir


def fetch(url, outfile, auth, keep, overwrite, backup_mode):
    # Get GitHub file content
    r = gh_request_content(url=url, auth=auth)
    sha = r.json()['sha']
    download_url = r.json()['download_url']
    # Set output file full path
    outfile = os.path.join(outdir, INI_FILE.format(project))

    # Fetching True/False depending on flags and file checksum
    if do_fetching(outfile, sha, keep, overwrite):
        # Backup old file if exists
        backup(outfile, mode=backup_mode)
        # Get content
        content = requests.get(download_url, auth=auth).text
        # Write new file
        write_content(outfile, content)
        Print.info(TAGS.FETCH + '{} --> {}'.format(url, outfile))
    else:
        Print.info(TAGS.SKIP + url)


def run(args):
    """
    Main process that:

     * Decide to fetch or not depending on file presence/absence and command-line arguments,
     * Gets the GitHub file content from full API URL,
     * Backups old file if desired,
     * Writes response into INI file.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Init print management
    Print.init(log=args.log, debug=args.debug, cmd=args.prog)
    # Instantiate processing context manager
    with ProcessingContext(args) as ctx:
        # Print command-line
        Print.command(' '.join(sys.argv))
        # Make output directory
        outdir = make_outdir(root=ctx.config_dir)
        # Counter
        progress = 0
        for project in ctx.targets:
            try:
                # Set full url
                url = ctx.url.format(INI_FILE.format(project))
                # Get GitHub file
                fetch(url, outdir, ctx.auth, ctx.keep, ctx.overwrite, ctx.backup_mode)
            except KeyboardInterrupt:
                raise
            except Exception:
                exc = traceback.format_exc().splitlines()
                msg = TAGS.FAIL
                msg += COLORS.HEADER('Fetching {} config file'.format(project)) + '\n'
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
