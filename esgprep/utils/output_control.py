#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Class to allow switching output messages on and off.

"""

import os
import sys


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
