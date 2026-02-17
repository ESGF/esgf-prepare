# -*- coding: utf-8 -*-

"""
.. module:: esgprep._handlers.dataset_id.py
   :platform: Unix
   :synopsis: Path parsing utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""


class Dataset(object):
    """
    Class handling dataset identifiers.

    """

    def __init__(self, identifier, separator="."):
        # Instantiate dataset identifier in a common format.
        self.identifier = identifier.replace("#", ".v")

        # Instantiate identifier separator.
        self.sep = separator

        # Get identifier parts.
        self.parts = self.identifier.split(self.sep)

    def __str__(self):
        return self.identifier
