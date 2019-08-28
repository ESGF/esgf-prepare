# -*- coding: utf-8 -*-

"""
.. module:: esgprep.checkvocab
    :platform: Unix
    :synopsis: Checks DRS vocabulary against CV.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import traceback

from esgprep._utils.print import *
from esgprep.constants import FRAMES


class Process(object):
    """
    Child process.

    """

    def __init__(self, ctx):
        """
        Shared processing context between child processes.

        """
        self.dataset_id = ctx.dataset_id
        self.dataset_list = ctx.dataset_list
        self.directory = ctx.directory
        self.lock = ctx.lock
        self.errors = ctx.errors
        self.progress = ctx.progress
        self.msg_length = ctx.msg_length

    def __call__(self, source):
        """
        Any error switches to the next child process.
        It does not stop the main process at all.

        """
        # Escape in case of error.
        try:

            if self.dataset_id or self.dataset_list:

                from esgprep._utils.dataset import get_terms

            elif self.directory:

                from esgprep._utils.path import get_terms

            else:

                from esgprep._utils.ncfile import get_terms

            # Validate source against CV.
            if get_terms(source):

                # Print success.
                with self.lock:
                    Print.success(str(source))

                return 1

            else:

                # Print failure.
                with self.lock:
                    Print.error(str(source))

                return 0

        except KeyboardInterrupt:

            # Lock error number.
            with self.lock:

                # Increase error counter.
                self.errors.value += 1

            raise

        # Catch known exception with its traceback.
        except Exception:

            # Lock error number.
            with self.lock:

                # Increase error counter.
                self.errors.value += 1

                # Format & print exception traceback.
                exc = traceback.format_exc().splitlines()
                msg = TAGS.SKIP + COLORS.HEADER(str(source)) + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)

            return None

        finally:

            # Lock progress value.
            with self.lock:

                # Increase progress counter.
                self.progress.value += 1

                # Clear previous print.
                msg = '\r{}'.format(' ' * self.msg_length.value)
                Print.progress(msg)

                # Print progress bar.
                msg = '\r{} {} {}'.format(COLORS.OKBLUE('Checking input data against CV'),
                                          FRAMES[self.progress.value % len(FRAMES)],
                                          source)
                Print.progress(msg)

                # Set new message length.
                self.msg_length.value = len(msg)
