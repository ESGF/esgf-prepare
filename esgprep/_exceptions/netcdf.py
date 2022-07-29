# -*- coding: utf-8 -*-

"""
.. module:: esgprep._exceptions.ncfile.py
   :platform: Unix
   :synopsis: esgprep netCDF exceptions.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""


class InvalidNetCDFFile(Exception):
    """
    Raised when invalid or corrupted NetCDF file.

    """

    def __init__(self, path, error):
        self.msg = "Invalid or corrupted NetCDF file."
        self.msg += f"\n<file: '{path}'>"
        self.msg += f"\n<error: '{error}'>"
        super(self.__class__, self).__init__(self.msg)


class NoNetCDFAttribute(Exception):
    """
    Raised when a NetCDF attribute is missing.

    """

    def __init__(self, attribute, path=None, values=None, variable=None):
        self.msg = "Attribute not found"
        self.msg += f"\n<attribute: '{attribute}'>"
        if variable:
            self.msg += f"\n<variable: '{variable}'>"
        if path:
            self.msg += f"\n<file: '{path}'>"
        if values:
            self.msg += f"\n<keys: '{values}'>"
        super(self.__class__, self).__init__(self.msg)
