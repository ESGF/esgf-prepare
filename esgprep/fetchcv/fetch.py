# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF CV from GitHub repository.

"""

import traceback

from esgprep._utils.github import *


class Process(object):
    """
    Child process.

    """

    def __init__(self, ctx):
        """
        Shared processing context between child processes.

        """
        self.outdir = ctx.outdir
        self.auth = ctx.auth,
        self.sha = ctx.sha
        self.keep = ctx.keep
        self.overwrite = ctx.overwrite
        self.backup_mode = ctx.backup_mode
        self.error = ctx.error
        self.progress = ctx.progress
        self.nfiles = ctx.nfiles
        self.lock = ctx.lock

    def __call__(self, info):
        """
        Any error switches to the next child process.
        It does not stop the main process at all.

        """
        # Escape in case of error.
        try:

            # Get type. Default is 'file'.
            blob = (info['type'] == 'blob')

            # Get destination subdirectory.
            path = info['path']

            # Set output full path of the file.
            outfile = os.path.join(self.outdir, path)

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
                  auth=self.auth,
                  sha=sha,
                  keep=self.keep,
                  overwrite=self.overwrite,
                  backup_mode=self.backup_mode)

        # Catch unknown exception into error log instead of stop the process.
        except KeyboardInterrupt:

            # Set error to True.
            self.error.value = True

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
            with self.lock:
                Print.exception(msg, buffer=True)

            # Set error to True.
            self.error.value = True

        # Print progress.
        finally:

            # Lock progress value.
            with self.lock:

                # Increase progress counter.
                self.progress.value += 1

                # Compute progress percentage.
                percentage = int(self.progress.value * 100 / self.nfiles)

                # Print progress bar.
                msg = COLORS.OKBLUE('\rFetching CV: ')
                msg += '{}% | {}/{} files'.format(percentage, self.progress.value, self.nfiles)
                Print.progress(msg)
