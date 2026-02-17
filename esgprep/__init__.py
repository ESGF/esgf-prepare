# -*- coding: utf-8 -*-

"""
.. module:: esgprep.__init__.py
   :platform: Unix
   :synopsis: esgprep initializer.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import os
import sys

import esgprep.constants as constants

__version__ = "from esgprep v{} {}".format(constants.VERSION, constants.VERSION_DATE)


__all__ = ["__version__", "OutputControl"]


class OutputControl:
    def __init__(self):
        self.null = open("/dev/null", "w")
        self.null_fh = self.null.fileno()
        self.stdout_fh = sys.stdout.fileno()
        self.stdout_copy_fh = os.dup(self.stdout_fh)
        self.stderr_fh = sys.stderr.fileno()
        self.stderr_copy_fh = os.dup(self.stderr_fh)

    def close(self):
        """Close all file handles to prevent resource leaks."""
        try:
            if hasattr(self, "null") and self.null and not self.null.closed:
                self.null.close()
        except (AttributeError, OSError):
            pass
        try:
            if hasattr(self, "stdout_copy_fh"):
                os.close(self.stdout_copy_fh)
        except (AttributeError, OSError):
            pass
        try:
            if hasattr(self, "stderr_copy_fh"):
                os.close(self.stderr_copy_fh)
        except (AttributeError, OSError):
            pass

    def __del__(self):
        """Ensure file handles are closed when object is garbage collected."""
        self.close()

    def stdout_on(self):
        sys.stdout.flush()
        os.dup2(self.stdout_copy_fh, self.stdout_fh)

    def stdout_off(self):
        sys.stdout.flush()
        os.dup2(self.null_fh, self.stdout_fh)

    def stderr_on(self):
        sys.stderr.flush()
        os.dup2(self.stderr_copy_fh, self.stderr_fh)

    def stderr_off(self):
        sys.stderr.flush()
        os.dup2(self.null_fh, self.stderr_fh)


global _STDOUT
_STDOUT = OutputControl()
