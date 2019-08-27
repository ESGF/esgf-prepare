# -*- coding: utf-8 -*-

"""
.. module:: esgprep.__init__.py
   :platform: Unix
   :synopsis: esgprep initializer.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import os
import sys

from esgprep.constants import *

__version__ = 'from esgprep v{} {}'.format(VERSION, VERSION_DATE)


class OutputControl:

    def __init__(self):
        self.null = open("/dev/null", "w")
        self.null_fh = self.null.fileno()
        self.stdout_fh = sys.stdout.fileno()
        self.stdout_copy_fh = os.dup(self.stdout_fh)
        self.stderr_fh = sys.stderr.fileno()
        self.stderr_copy_fh = os.dup(self.stderr_fh)

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
