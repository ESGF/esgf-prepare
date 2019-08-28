# -*- coding: utf-8 -*-

"""
.. module:: esgprep._contexts.__init__.py
   :platform: Unix
   :synopsis: esgprep processing contexts initializer.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

from esgprep._utils.print import *


class BaseContext(object):
    """
    Base class for processing context manager.

    """

    def __init__(self, args):

        # Set arguments.
        self.args = args

        # Instantiate print manager.
        Print.init(log=args.log, debug=args.debug, cmd=args.prog)

        # Enable/disable colors.
        if 'color' in args and args.color:
            Print.enable_colors()
        if 'no_color' in args and args.no_color:
            Print.disable_colors()

        # Set project.
        self.project = self.set('project')

        # Set program.
        self.prog = self.set('prog')

    def __enter__(self):

        # Print command-line running.
        Print.command()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        # Print log.
        Print.log()

    def set(self, key, default=False):

        # Validate argument presence.
        if hasattr(self.args, key):

            # Get argument value.
            return getattr(self.args, key)

        # If default value desired.
        elif default is not False:

            # Set default value.
            return default
